from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOCK = ROOT / "docker" / "runtime-image-sources.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_personal_source import PublicationError, checked_file, copy_allowlisted_tree, file_record, scan_image_archive
VEX_DOCUMENTS: dict[str, Path] = {}


def prepare_image_context(image: dict[str, Any], output: Path) -> dict[str, Any]:
    policy=json.loads((ROOT/'docker/runtime-context-files.json').read_text(encoding='utf-8'))
    if policy.get('schema_version')!='1.0.0' or image['id'] not in policy.get('images',{}):
        raise PublicationError('Unknown image build-context policy')
    entry=policy['images'][image['id']]
    records=[file_record(ROOT,source,target=target) for target,source in entry['files'].items()]
    context_root=ROOT/image['context']
    allowed={source.removeprefix(image['context']+'/') for source in entry['files'].values() if source.startswith(image['context']+'/')}
    allowed.update(entry['ancillary_files'])
    if image['id']=='document_worker':
        wheel_manifest=json.loads(checked_file(ROOT,'docker/document-worker/wheelhouse-manifest.json').read_text())
        for wheel in wheel_manifest['wheels']:
            name=wheel['filename']
            record=file_record(ROOT,'docker/document-worker/wheelhouse/'+name,target='wheelhouse/'+name)
            if record['sha256']!=wheel['sha256']:raise PublicationError('Wheel differs from hash-bound manifest')
            records.append(record);allowed.add('wheelhouse/'+name)
    for path in context_root.rglob('*'):
        if path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400:
            raise PublicationError('Reparse point in image context')
        if '__pycache__' in path.relative_to(context_root).parts:
            # Generated interpreter caches are explicitly excluded, never copied.
            continue
        if path.is_file() and path.relative_to(context_root).as_posix() not in allowed:
            raise PublicationError('Unexpected file in image source context')
    result=copy_allowlisted_tree(ROOT,output,records,private_roots=(str(ROOT),os.environ.get('USERPROFILE','')))
    result['source_inputs']=records
    return result


def verify_context_commit(image: dict[str, Any], report: dict, commit: str, *, runner=subprocess.run) -> None:
    """Reject a concurrent source change even if Git was clean when the build began."""
    import re
    if not re.fullmatch('[0-9a-f]{40}',commit):raise PublicationError('Invalid frozen source commit')
    def committed(path):
        result=runner(['git','show',f'{commit}:{path}'],cwd=ROOT,check=True,capture_output=True)
        return result.stdout
    for path in ('docker/runtime-context-files.json','docker/runtime-image-sources.json'):
        if committed(path)!=(ROOT/path).read_bytes():raise PublicationError('Build policy/source lock changed after freeze')
    source_lock=json.loads(committed('docker/runtime-image-sources.json'))
    if image not in source_lock['images']:raise PublicationError('Image build inputs differ from frozen source lock')
    wheels={}
    if image['id']=='document_worker':
        manifest=json.loads(committed('docker/document-worker/wheelhouse-manifest.json'))
        wheels={'docker/document-worker/wheelhouse/'+w['filename']:w['sha256'] for w in manifest['wheels']}
    for record in report['source_inputs']:
        expected=wheels.get(record['path'])
        if expected is None:expected=hashlib.sha256(committed(record['path'])).hexdigest()
        if expected!=record['sha256']:raise PublicationError('Context bytes do not belong to frozen publication commit')


def _run(arguments: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )


def _git(*arguments: str) -> str:
    return _run(("git", *arguments), capture=True).stdout.strip()


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _source_identity(allow_dirty: bool) -> tuple[str, int, str, bool]:
    checkout=Path(_git('rev-parse','--show-toplevel')).resolve(strict=True)
    if checkout!=ROOT.resolve(strict=True):
        raise RuntimeError('Build source must be its own Git checkout; parent development history is forbidden')
    source_clean = not bool(_git("status", "--porcelain"))
    if not allow_dirty and not source_clean:
        raise RuntimeError("Release image builds require a clean Git checkout")
    commit = _git("rev-parse", "HEAD")
    epoch = int(_git("show", "-s", "--format=%ct", "HEAD"))
    created = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return commit, epoch, created, source_clean


def _metadata_identity(path: Path) -> tuple[str, str]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    digest = metadata.get("containerimage.digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest) != 71:
        raise RuntimeError(f"Build metadata does not contain an image digest: {path}")
    config_digest = metadata.get("containerimage.config.digest")
    if not isinstance(config_digest, str) or not config_digest.startswith("sha256:") or len(config_digest) != 71:
        raise RuntimeError(f"Build metadata does not contain a config digest: {path}")
    descriptor = metadata.get("containerimage.descriptor")
    if not isinstance(descriptor, dict) or descriptor.get("platform") != {"architecture": "amd64", "os": "linux"}:
        raise RuntimeError(f"Build metadata platform is not linux/amd64: {path}")
    return digest, config_digest


def _license_inventory(sbom_path: Path) -> dict[str, Any]:
    sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
    packages = []
    for value in sbom.get("packages", []):
        if not isinstance(value, dict):
            continue
        packages.append(
            {
                "name": value.get("name"),
                "version": value.get("versionInfo"),
                "license_concluded": value.get("licenseConcluded"),
                "reviewed_by": None,
                "notice": None,
                "source_required": None,
                "source": None,
                "lgpl_replacement": None,
            }
        )
    packages.sort(key=lambda item: (str(item["name"]), str(item["version"])))
    return {"schema_version": "1.0.0", "source_sbom_sha256": _sha256(sbom_path), "packages": packages}


def _build_once(
    image: dict[str, Any],
    *,
    round_number: int,
    output_root: Path,
    commit: str,
    epoch: int,
    created: str,
    source_clean: bool = True,
) -> dict[str, Any]:
    image_id = image["id"]
    round_root = output_root / f"round-{round_number}" / image_id
    round_root.mkdir(parents=True, exist_ok=True)
    metadata_path = round_root / "build-metadata.json"
    archive_path = round_root / "image.docker.tar"
    archive_cli_path = archive_path.relative_to(ROOT).as_posix() if archive_path.is_relative_to(ROOT) else str(archive_path)
    tag = f"{image['repository']}:personal-r1-build-{round_number}"
    context_path=round_root/'approved-context'
    context_report=prepare_image_context(image,context_path)
    if source_clean:verify_context_commit(image,context_report,commit)
    _atomic_json(round_root/'context-manifest.json',context_report)
    arguments = [
        "docker",
        "buildx",
        "build",
        "--no-cache",
        "--platform",
        "linux/amd64",
        "--provenance=false",
        "--sbom=false",
        "--build-arg",
        f"SOURCE_REVISION={commit}",
        "--build-arg",
        f"SOURCE_DATE_EPOCH={epoch}",
        "--build-arg",
        f"OCI_CREATED={created}",
        "--metadata-file",
        str(metadata_path),
        "--output",
        f"type=docker,dest={archive_cli_path},rewrite-timestamp=true,name={tag}",
        "--tag",
        tag,
        str(context_path),
    ]
    _run(arguments)
    grants=('LICENSE','PERSONAL_USE_PERMISSION.md','OFFICIAL_REDISTRIBUTION_PERMISSION.md')
    archive_scan=scan_image_archive(archive_path,private_roots=(str(ROOT),os.environ.get('USERPROFILE','')),
        required_files={'usr/share/doc/plwc/'+name:(ROOT/name).read_bytes() for name in grants})
    digest, config_digest = _metadata_identity(metadata_path)
    _run(("docker", "load", "--input", str(archive_path)))
    observed = json.loads(
        _run(("docker", "image", "inspect", tag, "--format", "{{json .}}"), capture=True).stdout
    )
    if (
        observed.get("Os") != "linux"
        or observed.get("Architecture") != "amd64"
        or observed.get("Id") not in {digest, config_digest}
    ):
        raise RuntimeError(f"Loaded {image_id} does not match its build identity/platform")
    return {
        "round": round_number,
        "tag": tag,
        "digest": digest,
        "config_digest": config_digest,
        "content_bytes": int(observed["Size"]),
        "archive_path": str(archive_path.relative_to(output_root)),
        "archive_sha256": _sha256(archive_path),
        "metadata_path": str(metadata_path.relative_to(output_root)),
        "metadata_sha256": _sha256(metadata_path),
        "context_manifest_sha256": _sha256(round_root/'context-manifest.json'),
        "source_commit_verified": source_clean,
        "archive_secret_scan": archive_scan,
    }


def _probe_image(image: dict[str, Any], tag: str) -> dict[str, Any]:
    image_id = image["id"]
    user = "10001:10001" if image_id == "document_worker" else "65532:65532"
    arguments = [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "512m",
        "--cpus",
        "1",
        "--user",
        user,
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
    ]
    if image_id == "document_worker":
        arguments.extend(
            (
                "--entrypoint",
                "sh",
                tag,
                "-c",
                "test ! -e /usr/bin/perl && ! command -v perl >/dev/null 2>&1 && "
                "! command -v tiffcrop >/dev/null 2>&1 && "
                "test -s /usr/share/mime/mime.cache && "
                "test -s /usr/share/mime/globs2 && "
                "test -s /usr/share/mime/magic && "
                "test -s /usr/share/doc/shared-mime-info/copyright && "
                "test -s /usr/share/doc/odfpy/APACHE-LICENSE-2.0.txt && "
                "test -s /usr/share/doc/odfpy/GPL-LICENSE-2.txt && "
                "test -s /usr/share/doc/odfpy/LGPL-2.1.txt && "
                "test -s /usr/share/doc/odfpy/SOURCE-NOTICE.md && "
                "! command -v update-mime-database >/dev/null 2>&1 && "
                "! dpkg-query -s shared-mime-info >/dev/null 2>&1 && "
                "! dpkg-query -s libxml2 >/dev/null 2>&1 && "
                "! dpkg-query -s libgdk-pixbuf-2.0-0 >/dev/null 2>&1 && "
                "! dpkg-query -s libglib2.0-0t64 >/dev/null 2>&1 && "
                "! dpkg-query -s libpango-1.0-0 >/dev/null 2>&1 && "
                "! dpkg-query -s libpangoft2-1.0-0 >/dev/null 2>&1 && "
                "test ! -e /usr/lib/x86_64-linux-gnu/libxml2.so.2 && "
                "test ! -e /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 && "
                "dpkg-query -s libc6 | grep -qx 'Version: 2.41-12+deb13u4' && "
                "dpkg-query -s libc-bin | grep -qx 'Version: 2.41-12+deb13u4' && "
                "python -c 'import importlib.util; assert importlib.util.find_spec(\"weasyprint\") is None' && "
                "python -c 'from PIL import features; assert features.check(\"libtiff\")' && "
                "python -c 'import ssl; assert ssl.OPENSSL_VERSION_INFO == (3, 5, 0, 7, 0)' && "
                "python -m plwc_document_worker probe",
            )
        )
    elif image_id == "node_runner":
        arguments.extend(
            (
                "--entrypoint",
                "sh",
                tag,
                "-c",
                "node --version && dpkg-query -s libc6 | grep -qx 'Version: 2.41-12+deb13u4' && "
                "dpkg-query -s libc-bin | grep -qx 'Version: 2.41-12+deb13u4' && "
                'test ! -e /usr/bin/perl && '
                '! command -v perl >/dev/null 2>&1 && for x in npm npx corepack yarn yarnpkg; do '
                'if command -v "$x" >/dev/null 2>&1; then exit 19; fi; done',
            )
        )
    elif image_id == "python_runner":
        arguments.extend(
            (
                "--entrypoint",
                "sh",
                tag,
                "-c",
                "python -c 'import ssl; assert ssl.OPENSSL_VERSION_INFO == (3, 5, 0, 7, 0)' && "
                "dpkg-query -s libc6 | grep -qx 'Version: 2.41-12+deb13u4' && "
                "dpkg-query -s libc-bin | grep -qx 'Version: 2.41-12+deb13u4' && "
                'python --version && test "$(id -u)" = 65532 && test ! -e /usr/bin/perl && '
                "! command -v perl >/dev/null 2>&1",
            )
        )
    else:
        raise RuntimeError(f"No governed runtime probe exists for {image_id}")
    completed = _run(arguments, capture=True)
    stdout = completed.stdout.strip()
    if image_id == "document_worker":
        payload = json.loads(stdout)
        if payload.get("ok") is not True or payload.get("operation") != "probe":
            raise RuntimeError("Document Worker probe did not return the governed success contract")
    elif not stdout:
        raise RuntimeError(f"Runtime probe returned no version output for {image_id}")
    return {
        "id": f"{image_id}_v1",
        "status": "pass",
        "pull_policy": "never",
        "network": "none",
        "user": user,
        "stdout": stdout,
    }


def _security_evidence(image: dict[str, Any], output_root: Path, digest: str, commit: str) -> dict[str, Any]:
    image_id = image["id"]
    evidence_root = output_root / "evidence" / image_id
    evidence_root.mkdir(parents=True, exist_ok=True)
    sbom_path = evidence_root / "sbom.spdx.json"
    licenses_path = evidence_root / "licenses.json"
    vulnerabilities_path = evidence_root / "vulnerabilities.sarif.json"
    provenance_path = evidence_root / "provenance.intoto.json"

    scan_reference = f"local://{image['repository']}@{digest}"
    _run(("docker", "scout", "sbom", "--format", "spdx", "--output", str(sbom_path), scan_reference))
    _atomic_json(licenses_path, _license_inventory(sbom_path))

    vulnerability_status = "complete"
    try:
        _run(("docker", "scout", "cves", "--format", "sarif", "--output", str(vulnerabilities_path), scan_reference))
    except subprocess.CalledProcessError as exc:
        vulnerability_status = "unavailable"
        _atomic_json(
            vulnerabilities_path,
            {
                "schema_version": "1.0.0",
                "ok": False,
                "status": "unavailable",
                "tool": "docker scout cves",
                "exit_code": exc.returncode,
            },
        )

    metadata = json.loads((output_root / "round-2" / image_id / "build-metadata.json").read_text(encoding="utf-8"))
    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": image["repository"], "digest": {"sha256": digest.removeprefix("sha256:")}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://mobyproject.org/buildkit@v1",
                "externalParameters": {"platform": "linux/amd64", "source_commit": commit},
                "resolvedDependencies": metadata.get("buildx.build.provenance", {}).get("materials", []),
            },
            "runDetails": {"builder": {"id": "docker-buildx-local-verification"}},
        },
    }
    _atomic_json(provenance_path, provenance)
    evidence = {
        "sbom": {"path": str(sbom_path.relative_to(output_root)), "sha256": _sha256(sbom_path)},
        "licenses": {"path": str(licenses_path.relative_to(output_root)), "sha256": _sha256(licenses_path)},
        "vulnerabilities": {
            "path": str(vulnerabilities_path.relative_to(output_root)),
            "sha256": _sha256(vulnerabilities_path),
            "status": vulnerability_status,
        },
        "provenance": {"path": str(provenance_path.relative_to(output_root)), "sha256": _sha256(provenance_path)},
    }
    vex_source = VEX_DOCUMENTS.get(image_id)
    if vex_source is not None:
        vex_path = evidence_root / "openvex.json"
        _atomic_json(vex_path, json.loads(vex_source.read_text(encoding="utf-8")))
        evidence["vex"] = {"path": str(vex_path.relative_to(output_root)), "sha256": _sha256(vex_path)}
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and compare the three PLwC Personal runtime images")
    parser.add_argument("--output-root", type=Path, default=ROOT / "build" / "runtime-images")
    parser.add_argument("--allow-dirty", action="store_true", help="Development only; cannot satisfy the release gate")
    parser.add_argument("--allow-missing-vulnerability-scan", action="store_true")
    args = parser.parse_args()

    source_lock = json.loads(SOURCE_LOCK.read_text(encoding="utf-8"))
    if source_lock.get("target_platform") != "linux/amd64" or len(source_lock.get("images", [])) != 3:
        raise RuntimeError("Runtime image source lock is invalid")
    commit, epoch, created, source_clean = _source_identity(args.allow_dirty)
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for image in source_lock["images"]:
        first = _build_once(image, round_number=1, output_root=output_root, commit=commit, epoch=epoch, created=created, source_clean=source_clean)
        second = _build_once(image, round_number=2, output_root=output_root, commit=commit, epoch=epoch, created=created, source_clean=source_clean)
        if (
            first["digest"] != second["digest"]
            or first["config_digest"] != second["config_digest"]
            or first["content_bytes"] != second["content_bytes"]
        ):
            raise RuntimeError(f"Non-reproducible image build: {image['id']}")
        probe = _probe_image(image, second["tag"])
        evidence = _security_evidence(image, output_root, second["digest"], commit)
        if evidence["vulnerabilities"]["status"] != "complete" and not args.allow_missing_vulnerability_scan:
            raise RuntimeError(
                f"Vulnerability scan is unavailable for {image['id']}; install/authenticate an approved scanner or use the development-only override"
            )
        results.append(
            {
                "id": image["id"],
                "repository": image["repository"],
                "version": image["version"],
                "platform": "linux/amd64",
                "digest": second["digest"],
                "config_digest": second["config_digest"],
                "content_bytes": second["content_bytes"],
                "rounds": [first, second],
                "probe": probe,
                "evidence": evidence,
            }
        )
    report = {
        "schema_version": "1.0.0",
        "status": (
            "awaiting_license_review"
            if source_clean and all(item["evidence"]["vulnerabilities"]["status"] == "complete" for item in results)
            else "development_only"
        ),
        "source_clean": source_clean,
        "source_commit": commit,
        "source_date_epoch": epoch,
        "created": created,
        "target_platform": "linux/amd64",
        "source_lock_sha256": _sha256(SOURCE_LOCK),
        "images": results,
    }
    _atomic_json(output_root / "image-build-report.json", report)
    print(json.dumps({"status": report["status"], "source_commit": commit, "images": [{"id": item["id"], "digest": item["digest"]} for item in results]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
