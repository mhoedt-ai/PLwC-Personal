from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


verifier = _load("plwc_verify_runtime_images_test", ROOT / "scripts" / "verify_runtime_images.py")
finalizer = _load("plwc_finalize_runtime_images_test", ROOT / "scripts" / "finalize_runtime_image_manifest.py")
pusher = _load("plwc_push_runtime_images_test", ROOT / "scripts" / "push_runtime_images.py")
STAGING_REPOSITORY_PREFIX = "ghcr.io/mhoedt-ai/plwc-personal-private-staging"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return {"path": path.as_posix(), "sha256": _sha256(path)}


def _build_report(tmp_path: Path) -> Path:
    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    source = json.loads((ROOT / "docker" / "runtime-image-sources.json").read_text(encoding="utf-8"))
    images = []
    for index, locked in enumerate(source["images"], start=1):
        image_id = locked["id"]
        config_digest = "sha256:" + str(index + 3) * 64
        raw = json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {"digest": config_digest, "size": 512},
            "layers": [{"digest": "sha256:" + "f" * 64, "size": 2048}]}).encode()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        root = tmp_path / "evidence" / image_id
        sbom = _write_json(root / "sbom.spdx.json", {"spdxVersion": "SPDX-2.3", "packages": [{"name": "fixture-package", "versionInfo": "1.0.0"}]})
        notice = _write_json(root / "fixture-notice.json", {"fixture": "synthetic MIT license review"})
        notice["path"] = Path(notice["path"]).relative_to(tmp_path).as_posix()
        licenses = _write_json(root / "licenses.json", {"schema_version": "1.0.0", "source_sbom_sha256": sbom["sha256"], "packages": [
            {"name": "fixture-package", "version": "1.0.0", "license_concluded": "MIT", "reviewed_by": "synthetic-test-reviewer",
            "notice": notice, "source_required": False, "source": None, "lgpl_replacement": None}]})
        vulnerabilities = _write_json(
            root / "vulnerabilities.sarif.json",
            {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "docker scout", "rules": []}}, "results": []}]},
        )
        provenance = _write_json(
            root / "provenance.intoto.json",
            {
                "_type": "https://in-toto.io/Statement/v1",
                "subject": [{"name": locked["repository"], "digest": {"sha256": digest.removeprefix("sha256:")}}],
                "predicateType": "https://slsa.dev/provenance/v1",
                "predicate": {
                    "buildDefinition": {
                        "externalParameters": {"source_commit": commit, "platform": "linux/amd64"}
                    }
                },
            },
        )
        evidence = {
            "sbom": {**sbom, "path": Path(sbom["path"]).relative_to(tmp_path).as_posix()},
            "licenses": {**licenses, "path": Path(licenses["path"]).relative_to(tmp_path).as_posix()},
            "vulnerabilities": {
                **vulnerabilities,
                "path": Path(vulnerabilities["path"]).relative_to(tmp_path).as_posix(),
                "status": "complete",
            },
            "provenance": {**provenance, "path": Path(provenance["path"]).relative_to(tmp_path).as_posix()},
        }
        round_value = {
            "digest": digest,
            "config_digest": config_digest,
            "content_bytes": index * 10_000,
            "tag": f"fixture-{index}",
        }
        images.append(
            {
                "id": image_id,
                "repository": locked["repository"],
                "version": "1.0.0",
                "platform": "linux/amd64",
                "digest": digest,
                "config_digest": config_digest,
                "content_bytes": index * 10_000,
                "rounds": [dict(round_value), dict(round_value)],
                "probe": {
                    "id": f"{image_id}_v1",
                    "status": "pass",
                    "pull_policy": "never",
                    "network": "none",
                    "user": "10001:10001" if image_id == "document_worker" else "65532:65532",
                    "stdout": "fixture probe passed",
                },
                "evidence": evidence,
            }
        )
    report = {
        "schema_version": "1.0.0",
        "status": "pass",
        "source_clean": True,
        "source_commit": commit,
        "source_date_epoch": 1,
        "created": "2026-09-06T00:00:00Z",
        "target_platform": "linux/amd64",
        "source_lock_sha256": _sha256(ROOT / "docker" / "runtime-image-sources.json"),
        "images": images,
    }
    path = tmp_path / "image-build-report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def _attach_approved_vex(report_path: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    image = next(item for item in report["images"] if item["id"] == "document_worker")
    vex_path = report_path.parent / "evidence" / "document_worker" / "openvex.json"
    vex_payload = json.loads(
        (ROOT / "security" / "vex" / "document-worker-CVE-2026-52490.openvex.json").read_text(
            encoding="utf-8"
        )
    )
    # The repository VEX belongs to the historical Apache image. A new
    # Personal VEX must be assessed against the rebuilt digest in PERS-04.
    vex_payload["@id"] = "https://github.com/mhoedt-ai/PLwC-Personal/security/vex/CVE-2026-52490/document-worker-0.1.0"
    vex_payload["statements"][0]["products"][0]["@id"] = (
        "pkg:docker/mhoedt-ai/plwc-personal-document-worker@0.1.0"
    )
    vex_path.write_text(json.dumps(vex_payload, indent=2) + "\n", encoding="utf-8")
    image["evidence"]["vex"] = {
        "path": vex_path.relative_to(report_path.parent).as_posix(),
        "sha256": _sha256(vex_path),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return vex_payload


def _write_tiff_critical(report_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    image = next(item for item in report["images"] if item["id"] == "document_worker")
    descriptor = image["evidence"]["vulnerabilities"]
    vulnerability_path = report_path.parent / descriptor["path"]
    vulnerability_path.write_text(
        json.dumps(
            {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {
                            "driver": {
                                "name": "docker scout",
                                "rules": [
                                    {
                                        "id": "CVE-2026-52490",
                                        "properties": {
                                            "cvssV3_severity": "CRITICAL",
                                            "fixed_version": "not fixed",
                                            "purls": [
                                                "pkg:deb/debian/tiff@4.7.0-3%2Bdeb13u3?os_distro=trixie&os_name=debian&os_version=13"
                                            ],
                                        },
                                    }
                                ],
                            }
                        },
                        "results": [],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    descriptor["sha256"] = _sha256(vulnerability_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _release_repository_for_staging_reference(report: dict, reference: str) -> str:
    staging_repository = reference.rsplit(":", 1)[0]
    for image in report["images"]:
        expected = f"{STAGING_REPOSITORY_PREFIX}-{image['id'].replace('_', '-')}"
        if staging_repository == expected:
            return str(image["repository"])
    raise AssertionError(f"Unexpected staging reference: {reference}")


def test_source_lock_and_release_build_report_verify(tmp_path: Path) -> None:
    assert verifier.verify_source_lock()["target_platform"] == "linux/amd64"
    report = verifier.verify_build_report(_build_report(tmp_path))
    assert report["status"] == "pass"
    assert len(report["images"]) == 3


def test_high_vulnerability_is_recorded_but_does_not_block(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    descriptor = report["images"][0]["evidence"]["vulnerabilities"]
    vulnerability_path = tmp_path / descriptor["path"]
    vulnerability_path.write_text(
        json.dumps(
            {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "docker scout", "rules": [
                            {"id": "CVE-test", "properties": {"cvssV3_severity": "HIGH"}}
                        ]}},
                        "results": [{"ruleId": "CVE-test", "properties": {"severity": "HIGH"}}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    descriptor["sha256"] = _sha256(vulnerability_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    verified = verifier.verify_build_report(report_path)
    assert verified["status"] == "pass"


@pytest.mark.parametrize(
    "sarif",
    [
        {"version": "2.1.0", "runs": []},
        {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "docker scout"}}}]},
        {"version": "2.1.0", "runs": [{"tool": {"driver": {}}, "results": []}]},
        {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "fixture"}}, "results": []}]},
    ],
)
def test_missing_scan_run_cannot_pass_release_gate(tmp_path: Path, sarif: dict) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    descriptor = report["images"][0]["evidence"]["vulnerabilities"]
    vulnerability_path = tmp_path / descriptor["path"]
    vulnerability_path.write_text(json.dumps(sarif), encoding="utf-8")
    descriptor["sha256"] = _sha256(vulnerability_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(verifier.VerificationError, match="no complete Docker Scout SARIF run"):
        verifier.verify_build_report(report_path)


@pytest.mark.parametrize(
    "sarif",
    [
        {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "docker scout", "rules": []}},
                                       "results": [{"ruleId": "CVE-unknown"}]}]},
        {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "docker scout", "rules": [
            {"id": "CVE-unknown", "properties": {}}
        ]}}, "results": [{"ruleId": "CVE-unknown"}]}]},
    ],
)
def test_result_without_known_severity_cannot_pass_release_gate(tmp_path: Path, sarif: dict) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    descriptor = report["images"][0]["evidence"]["vulnerabilities"]
    vulnerability_path = tmp_path / descriptor["path"]
    vulnerability_path.write_text(json.dumps(sarif), encoding="utf-8")
    descriptor["sha256"] = _sha256(vulnerability_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(verifier.VerificationError, match="rule|severity"):
        verifier.verify_build_report(report_path)


def test_critical_vulnerability_fails_closed_and_extracts_package_from_purl(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    descriptor = report["images"][0]["evidence"]["vulnerabilities"]
    vulnerability_path = tmp_path / descriptor["path"]
    payload = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "docker scout",
                        "rules": [
                            {
                                "id": "CVE-test-purl",
                                "properties": {
                                    "cvssV3_severity": "CRITICAL",
                                    "fixed_version": "2.0",
                                    "purls": ["pkg:deb/debian/example-package@1.0?os_distro=bookworm"],
                                },
                            }
                        ]
                    }
                },
                "results": [],
            }
        ]
    }
    vulnerability_path.write_text(json.dumps(payload), encoding="utf-8")
    descriptor["sha256"] = _sha256(vulnerability_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    assert verifier._sarif_gate_findings(payload) == [
        "CVE-test-purl severity=CRITICAL package=example-package fixed=2.0"
    ]
    try:
        verifier.verify_build_report(report_path)
    except verifier.VerificationError as exc:
        assert "critical vulnerability" in str(exc)
        assert "document_worker" in str(exc)
        assert "CVE-test-purl" in str(exc)
    else:
        raise AssertionError("A CRITICAL vulnerability must fail the release gate")


def test_historical_openvex_cannot_waive_new_personal_critical_finding(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    _attach_approved_vex(report_path)
    _write_tiff_critical(report_path)

    with pytest.raises(verifier.VerificationError, match="approved exception policy"):
        verifier.verify_build_report(report_path)
    # Raw critical finding is still preserved.
    verified = json.loads(report_path.read_text(encoding="utf-8"))
    descriptor = verified["images"][0]["evidence"]["vulnerabilities"]
    raw_payload = json.loads((tmp_path / descriptor["path"]).read_text(encoding="utf-8"))
    assert verifier._sarif_gate_findings(raw_payload) == [
        "CVE-2026-52490 severity=CRITICAL package=tiff fixed=not fixed"
    ]


def test_openvex_outside_exact_policy_cannot_bypass_critical_gate(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    _attach_approved_vex(report_path)
    _write_tiff_critical(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    image = next(item for item in report["images"] if item["id"] == "document_worker")
    descriptor = image["evidence"]["vex"]
    vex_path = tmp_path / descriptor["path"]
    vex_payload = json.loads(vex_path.read_text(encoding="utf-8"))
    vex_payload["statements"][0]["justification"] = "vulnerable_code_not_in_execute_path"
    vex_path.write_text(json.dumps(vex_payload), encoding="utf-8")
    descriptor["sha256"] = _sha256(vex_path)
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(verifier.VerificationError, match="approved exception policy"):
        verifier.verify_build_report(report_path)


def test_cvss_boundary_blocks_only_critical_range() -> None:
    for accepted in ("HIGH", "MEDIUM", "LOW", "UNSPECIFIED"):
        assert verifier._has_unaccepted_severity({"properties": {"severity": accepted}}) is False
    assert verifier._has_unaccepted_severity({"properties": {"severity": "CRITICAL"}}) is True
    assert verifier._has_unaccepted_severity({"properties": {"severity": "CVSS 8.9"}}) is False
    assert verifier._has_unaccepted_severity({"properties": {"severity": "CVSS 9.0"}}) is True


def test_dirty_or_unscanned_build_is_development_only_and_never_release_grade(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["status"] = "development_only"
    report["source_clean"] = False
    for image in report["images"]:
        descriptor = image["evidence"]["vulnerabilities"]
        vulnerability_path = tmp_path / descriptor["path"]
        vulnerability_path.write_text(
            json.dumps({"schema_version": "1.0.0", "ok": False, "status": "unavailable"}),
            encoding="utf-8",
        )
        descriptor["sha256"] = _sha256(vulnerability_path)
        descriptor["status"] = "unavailable"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    try:
        verifier.verify_build_report(report_path)
    except verifier.VerificationError as exc:
        assert "release-grade PASS" in str(exc)
    else:
        raise AssertionError("Development-only evidence must not pass the release gate")
    verified = verifier.verify_build_report(report_path, allow_development_only=True)
    assert verified["source_clean"] is False
    assert verifier.main(["--build-report", str(report_path), "--allow-development-only"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["build_report"]["verification"] == "pass"
    assert output["build_report"]["grade"] == "development_only"


def test_finalizer_binds_remote_manifest_digest_and_reverifies(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    local_by_repository = {
        image["repository"]: {"digest": image["digest"], "config_digest": image["config_digest"]}
        for image in report["images"]
    }

    def runner(argv, **_kwargs):
        reference = argv[-1]
        repository = _release_repository_for_staging_reference(report, reference)
        if "--raw" in argv:
            payload = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": local_by_repository[repository]["config_digest"], "size": 512},
                "layers": [{"digest": "sha256:" + "f" * 64, "size": 2048}],
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload).encode(), stderr=b"")
        summary = f"Name: {reference}\nDigest: {local_by_repository[repository]['digest']}\n"
        return subprocess.CompletedProcess(argv, 0, stdout=summary.encode(), stderr=b"")

    manifest_path = tmp_path / "runtime-images.json"
    manifest = finalizer.finalize(
        report_path,
        manifest_path,
        staging_repository_prefix=STAGING_REPOSITORY_PREFIX,
        runner=runner,
    )
    assert len(manifest["images"]) == 3
    assert all("@sha256:" in image["reference"] for image in manifest["images"])
    assert all(image["download_bytes"] == 2560 for image in manifest["images"])
    assert all("vex" not in image for image in manifest["images"])
    verified = verifier.verify_manifest(manifest_path)
    assert verified["installer_revision"] == "r27"


def test_finalizer_rejects_changed_remote_manifest_digest(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    local_by_repository = {
        image["repository"]: {"digest": image["digest"], "config_digest": image["config_digest"]}
        for image in report["images"]
    }

    def runner(argv, **_kwargs):
        reference = argv[-1]
        repository = _release_repository_for_staging_reference(report, reference)
        if "--raw" in argv:
            payload = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": local_by_repository[repository]["config_digest"], "size": 512},
                "layers": [{"digest": "sha256:" + "f" * 64, "size": 2048}],
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload).encode(), stderr=b"")
        return subprocess.CompletedProcess(
            argv, 0, stdout=f"Name: {reference}\nDigest: sha256:{'9' * 64}\n".encode(), stderr=b""
        )

    try:
        finalizer.finalize(
            report_path,
            tmp_path / "runtime-images.json",
            staging_repository_prefix=STAGING_REPOSITORY_PREFIX,
            runner=runner,
        )
    except finalizer.VerificationError as exc:
        assert "manifest digest" in str(exc)
    else:
        raise AssertionError("A changed GHCR manifest digest must fail finalization")


def test_finalizer_rejects_changed_remote_config_digest(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    local_by_repository = {image["repository"]: image["digest"] for image in report["images"]}

    def runner(argv, **_kwargs):
        reference = argv[-1]
        repository = _release_repository_for_staging_reference(report, reference)
        if "--raw" in argv:
            payload = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {"digest": "sha256:" + "8" * 64, "size": 512},
                "layers": [{"digest": "sha256:" + "f" * 64, "size": 2048}],
            }
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload).encode(), stderr=b"")
        return subprocess.CompletedProcess(
            argv, 0, stdout=f"Name: {reference}\nDigest: {local_by_repository[repository]}\n".encode(), stderr=b""
        )

    try:
        finalizer.finalize(
            report_path,
            tmp_path / "runtime-images.json",
            staging_repository_prefix=STAGING_REPOSITORY_PREFIX,
            runner=runner,
        )
    except finalizer.VerificationError as exc:
        assert "manifest digest" in str(exc)
    else:
        raise AssertionError("A changed GHCR config digest must fail finalization")


def test_finalizer_rejects_unapproved_staging_repository_prefix(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    with pytest.raises(finalizer.VerificationError, match="approved GHCR path"):
        finalizer.finalize(
            report_path,
            tmp_path / "runtime-images.json",
            staging_repository_prefix="ghcr.io/foreign/private-staging",
        )
    with pytest.raises(finalizer.VerificationError, match="approved GHCR path"):
        finalizer.finalize(
            report_path,
            tmp_path / "runtime-images.json",
            staging_repository_prefix="ghcr.io/mhoedt-ai/plwc-personal",
        )


@pytest.mark.parametrize('fault',['index','unknown_media_type','float_schema'])
def test_registry_inspector_rejects_wrapped_or_unsupported_manifest(fault):
    payload={'schemaVersion':2,'mediaType':'application/vnd.oci.image.manifest.v1+json',
        'config':{'digest':'sha256:'+'a'*64,'size':512},'layers':[{'digest':'sha256:'+'b'*64,'size':2048}]}
    if fault=='index':payload['manifests']=[];payload['mediaType']='application/vnd.oci.image.index.v1+json'
    elif fault=='unknown_media_type':payload['mediaType']='application/unknown'
    else:payload['schemaVersion']=2.0
    raw=json.dumps(payload).encode();digest='sha256:'+hashlib.sha256(raw).hexdigest()
    def runner(argv,**kwargs):return subprocess.CompletedProcess(argv,0,stdout=raw if '--raw' in argv else f'Digest: {digest}\n'.encode(),stderr=b'')
    with pytest.raises(finalizer.VerificationError,match='supported image manifest'):
        finalizer.inspect_remote_image('ghcr.io/mhoedt-ai/plwc-personal-node-runner@'+digest,runner=runner)


@pytest.mark.parametrize('fault',['none','unreviewed','critical_scan','dirty'])
def test_review_completion_requires_actual_license_rights_and_all_release_gates(tmp_path,fault):
    path=_build_report(tmp_path);report=json.loads(path.read_text())
    report['status']='awaiting_license_review'
    if fault=='dirty':report['source_clean']=False
    if fault=='unreviewed':
        descriptor=report['images'][0]['evidence']['licenses'];license_path=tmp_path/descriptor['path']
        license_data=json.loads(license_path.read_text());license_data['packages'][0]['reviewed_by']=None
        license_path.write_text(json.dumps(license_data))
    path.write_text(json.dumps(report))
    if fault=='critical_scan':_write_tiff_critical(path)
    output=tmp_path/'reviewed-image-build-report.json'
    if fault=='none':
        assert verifier.complete_license_review(path,output)['status']=='pass'
        assert verifier.verify_build_report(output)['status']=='pass'
        assert json.loads(path.read_text())['status']=='awaiting_license_review'
    else:
        with pytest.raises(verifier.VerificationError):verifier.complete_license_review(path,output)
        assert not output.exists()


@pytest.mark.parametrize('fault', ['duplicate_images', 'missing_round', 'boolean_size', 'wrong_platform'])
def test_release_build_report_cannot_skip_an_image_or_build_round(tmp_path, fault):
    path = _build_report(tmp_path)
    report = json.loads(path.read_text())
    if fault == 'duplicate_images':
        report['images'][1] = report['images'][0]
    elif fault == 'missing_round':
        report['images'][0]['rounds'][1] = None
    elif fault == 'boolean_size':
        image = report['images'][0]
        for entry in [image, *image['rounds']]:
            entry['content_bytes'] = True
    else:
        report['images'][0]['platform'] = 'linux/arm64'
    path.write_text(json.dumps(report))
    with pytest.raises(verifier.VerificationError):
        verifier.verify_build_report(path)


def test_review_completion_cli_requires_pending_build_report(tmp_path, capsys):
    output = tmp_path / 'reviewed-image-build-report.json'
    with pytest.raises(SystemExit) as exc:
        verifier.main(['--complete-license-review', str(output)])
    assert exc.value.code == 2
    assert '--complete-license-review requires --build-report' in capsys.readouterr().err
    assert not output.exists()


def test_direct_pusher_rejects_release_repository_prefix(tmp_path: Path) -> None:
    report_path = _build_report(tmp_path)
    with pytest.raises(finalizer.VerificationError, match="approved GHCR path"):
        pusher.push_verified_images(
            report_path,
            tmp_path / "staging-push-report.json",
            staging_repository_prefix="ghcr.io/mhoedt-ai/plwc-personal",
        )


def test_direct_pusher_rebuilds_and_pushes_exact_verified_manifests(tmp_path: Path, monkeypatch) -> None:
    # Context/Git-byte safety has separate behavioral tests; this case isolates registry identity.
    import build_runtime_images
    monkeypatch.setattr(pusher,'prepare_image_context',lambda *_args: {'source_inputs':[]})
    monkeypatch.setattr(build_runtime_images,'verify_context_commit',lambda *_args: None)
    report_path = _build_report(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected = {image["id"]: image for image in report["images"]}
    calls: list[list[str]] = []

    def runner(argv, **_kwargs):
        calls.append(argv)
        metadata_path = Path(argv[argv.index("--metadata-file") + 1])
        image_id = metadata_path.parent.name
        metadata_path.write_text(
            json.dumps(
                {
                    "containerimage.digest": expected[image_id]["digest"],
                    "containerimage.config.digest": expected[image_id]["config_digest"],
                    "containerimage.descriptor": {
                        "platform": {"architecture": "amd64", "os": "linux"}
                    },
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    output_path = tmp_path / "staging-push-report.json"
    result = pusher.push_verified_images(
        report_path,
        output_path,
        staging_repository_prefix=STAGING_REPOSITORY_PREFIX,
        runner=runner,
        visibility=lambda _repository: "private",
    )
    assert result["status"] == "pass"
    assert len(result["images"]) == 3
    assert len(calls) == 3
    assert all("--no-cache" in call for call in calls)
    assert all("--output" in call for call in calls)
    assert all("type=registry,name=ghcr.io/mhoedt-ai/plwc-personal-private-staging-" in call[call.index("--output") + 1] for call in calls)
    assert result["staging_suffix"].startswith("personal-r1-staging-")


def test_direct_pusher_rejects_a_nonidentical_registry_build(tmp_path: Path, monkeypatch) -> None:
    import build_runtime_images
    monkeypatch.setattr(pusher,'prepare_image_context',lambda *_args: {'source_inputs':[]})
    monkeypatch.setattr(build_runtime_images,'verify_context_commit',lambda *_args: None)
    report_path = _build_report(tmp_path)

    def runner(argv, **_kwargs):
        metadata_path = Path(argv[argv.index("--metadata-file") + 1])
        metadata_path.write_text(
            json.dumps(
                {
                    "containerimage.digest": "sha256:" + "9" * 64,
                    "containerimage.config.digest": "sha256:" + "8" * 64,
                    "containerimage.descriptor": {
                        "platform": {"architecture": "amd64", "os": "linux"}
                    },
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    with pytest.raises(finalizer.VerificationError, match="not identical"):
        pusher.push_verified_images(
            report_path,
            tmp_path / "staging-push-report.json",
            staging_repository_prefix=STAGING_REPOSITORY_PREFIX,
            runner=runner,
            visibility=lambda _repository: "private",
        )
