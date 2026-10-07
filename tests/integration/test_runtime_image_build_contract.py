from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_source_lock_has_exact_three_digest_pinned_builds() -> None:
    lock = json.loads((ROOT / "docker" / "runtime-image-sources.json").read_text(encoding="utf-8"))
    assert lock["target_platform"] == "linux/amd64"
    assert [image["id"] for image in lock["images"]] == ["document_worker", "node_runner", "python_runner"]
    assert [image["repository"] for image in lock["images"]] == [
        "ghcr.io/mhoedt-ai/plwc-personal-document-worker",
        "ghcr.io/mhoedt-ai/plwc-personal-node-runner",
        "ghcr.io/mhoedt-ai/plwc-personal-python-runner",
    ]
    for image in lock["images"]:
        assert re.fullmatch(r"docker\.io/library/.+@sha256:[0-9a-f]{64}", image["base"])


def test_every_runtime_dockerfile_is_pinned_and_labelled() -> None:
    for path in sorted((ROOT / "docker").glob("*-runner/Dockerfile")) + [ROOT / "docker" / "document-worker" / "Dockerfile"]:
        text = path.read_text(encoding="utf-8")
        assert re.match(r"^FROM [^\s]+@sha256:[0-9a-f]{64}$", text.splitlines()[0])
        assert ":latest" not in text
        for label in (
            "org.opencontainers.image.source",
            "org.opencontainers.image.version",
            "org.opencontainers.image.licenses",
            "org.opencontainers.image.created",
            "org.opencontainers.image.revision",
        ):
            assert label in text


def test_document_worker_build_is_offline_for_python_and_snapshot_locked_for_apt() -> None:
    text = (ROOT / "docker" / "document-worker" / "Dockerfile").read_text(encoding="utf-8")
    assert "PIP_NO_INDEX=1" in text
    assert "pip install --no-index" in text
    assert "--require-hashes" in text
    assert "snapshot.debian.org" in text
    assert "/var/cache/ldconfig/*" in text
    assert "/var/log/dpkg.log" in text
    install_blocks = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "apt-get install -y --no-install-recommends" not in line:
            continue
        packages = []
        for package_line in lines[index + 1 :]:
            stripped = package_line.strip()
            if stripped.startswith("&&"):
                break
            packages.append(stripped.rstrip(" \\"))
        assert packages and all("=" in package for package in packages)
        install_blocks.append(packages)
    assert len(install_blocks) == 2
    assert install_blocks[0] == [
        "libc6=2.41-12+deb13u4",
        "libc-bin=2.41-12+deb13u4",
        "shared-mime-info=2.4-5+b2",
    ]
    assert "libc6=2.41-12+deb13u4" in install_blocks[1]
    assert "libc-bin=2.41-12+deb13u4" in install_blocks[1]
    assert all(
        not package.startswith((
            "shared-mime-info=", "libxml2=", "libgdk-pixbuf-2.0-0=",
            "libglib2.0-0t64=", "libpango-1.0-0=", "libpangoft2-1.0-0=",
        ))
        for package in install_blocks[1]
    )


def test_runners_require_fixed_glibc() -> None:
    node = (ROOT / "docker" / "node-runner" / "Dockerfile").read_text(encoding="utf-8")
    assert "Version: 2.41-12+deb13u4" in node
    assert "dpkg-query -s libc6" in node
    assert "dpkg-query -s libc-bin" in node
    python = (ROOT / "docker" / "python-runner" / "Dockerfile").read_text(encoding="utf-8")
    assert "snapshot.debian.org/archive/debian/20260928T000000Z" in python
    assert "libc6=2.41-12+deb13u4" in python
    assert "libc-bin=2.41-12+deb13u4" in python
    assert "APT::Update::Error-Mode=any" in python


def test_node_runner_exposes_node_but_removes_package_managers() -> None:
    text = (ROOT / "docker" / "node-runner" / "Dockerfile").read_text(encoding="utf-8")
    assert "/usr/local/lib/node_modules/npm" in text
    assert "/usr/local/lib/node_modules/corepack" in text
    assert "/opt/yarn-v1.22.22" in text
    for executable in ("npm", "npx", "corepack", "yarn", "yarnpkg"):
        assert f"/usr/local/bin/{executable}" in text


def test_every_runtime_image_removes_incidental_perl_runtime() -> None:
    paths = sorted((ROOT / "docker").glob("*-runner/Dockerfile")) + [
        ROOT / "docker" / "document-worker" / "Dockerfile"
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "dpkg --purge --force-remove-essential --force-depends perl-base" in text
        assert "test ! -e /usr/bin/perl" in text
        assert "! dpkg-query -W perl-base" in text
        assert "rm -f /var/log/dpkg.log" in text


def test_every_runtime_archive_starts_from_the_corrected_filesystem() -> None:
    # Deleting/upgrading in a later layer still distributes the old binaries.
    for component, stage in (("document-worker", "1"), ("python-runner", "0"), ("node-runner", "0")):
        text = (ROOT / "docker" / component / "Dockerfile").read_text(encoding="utf-8")
        final = text.rsplit("FROM scratch", 1)[1]
        assert f"COPY --from={stage} / /" in final
        assert "org.opencontainers.image.revision" in final
        assert "WORKDIR /work" in final
        if component != "node-runner":
            assert "PYTHON_VERSION=3.12.14" in final
            assert "PYTHONDONTWRITEBYTECODE=1" in final
            assert "PYTHONUNBUFFERED=1" in final
        if component == "document-worker":
            assert "USER 10001:10001" in final
            assert 'ENTRYPOINT ["python", "-m", "plwc_document_worker"]' in final
            assert "PYTHONPATH=/opt/plwc-document-worker" in final
        elif component == "python-runner":
            assert 'CMD ["python3"]' in final


def test_build_script_has_no_push_or_registry_login_path() -> None:
    path = ROOT / "scripts" / "build_runtime_images.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    assert tree is not None
    assert "docker push" not in text
    assert "docker login" not in text
    assert '"push"' not in text
    assert "--no-cache" in text
    assert "--platform" in text and "linux/amd64" in text
    assert "type=docker" in text and "rewrite-timestamp=true" in text
    assert 'observed.get("Id") not in {digest, config_digest}' in text
    assert '("docker", "load", "--input"' in text
    assert "Non-reproducible image build" in text
    assert '"source_clean": source_clean' in text
    assert "def _probe_image" in text
    assert '"--pull",' in text and '"never",' in text
    assert '"--network",' in text and '"none",' in text
    assert "npm npx corepack yarn yarnpkg" in text
    assert "test ! -e /usr/bin/perl" in text
    assert "! command -v perl" in text
    assert "! command -v tiffcrop" in text
    assert "ssl.OPENSSL_VERSION_INFO == (3, 5, 0, 7, 0)" in text
    assert "VEX_DOCUMENTS" in text
    assert 'evidence["vex"]' in text
    assert '"docker", "image", "tag"' not in text
    assert '_probe_image(image, second["tag"])' in text


def test_security_scans_use_the_verified_digest_not_a_mutable_tag(tmp_path: Path, monkeypatch) -> None:
    path = ROOT / "scripts" / "build_runtime_images.py"
    spec = importlib.util.spec_from_file_location("plwc_build_runtime_image_scan_test", path)
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = builder
    spec.loader.exec_module(builder)

    image = {"id": "document_worker", "repository": "ghcr.io/mhoedt-ai/plwc-personal-document-worker"}
    digest = "sha256:" + "a" * 64
    metadata = tmp_path / "round-2" / image["id"] / "build-metadata.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text("{}", encoding="utf-8")
    subjects = []

    def fake_run(arguments):
        subjects.append(arguments[-1])
        output = Path(arguments[arguments.index("--output") + 1])
        if arguments[2] == "sbom":
            output.write_text(json.dumps({"spdxVersion": "SPDX-2.3", "packages": []}), encoding="utf-8")
        else:
            output.write_text(
                json.dumps({"version": "2.1.0", "runs": [
                    {"tool": {"driver": {"name": "docker scout", "rules": []}}, "results": []}
                ]}),
                encoding="utf-8",
            )

    monkeypatch.setattr(builder, "_run", fake_run)
    evidence = builder._security_evidence(image, tmp_path, digest, "b" * 40)

    assert subjects == [f"local://{image['repository']}@{digest}"] * 2
    assert evidence["vulnerabilities"]["status"] == "complete"


def test_personal_build_does_not_inherit_historical_vex(tmp_path, monkeypatch) -> None:
    # The previous product's TIFF waiver is outside the Personal release.
    # Even an existing historical file must not become candidate evidence.
    spec = importlib.util.spec_from_file_location('personal_vex_selection_test', ROOT/'scripts/build_runtime_images.py')
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    assert builder.VEX_DOCUMENTS == {}
    legacy = tmp_path / 'security/vex/document-worker-CVE-2026-52490.openvex.json'
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({'historical_fixture': True, 'status': 'not_affected'}))
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    output = tmp_path / 'build'
    metadata = output / 'round-2/document_worker/build-metadata.json'
    metadata.parent.mkdir(parents=True)
    metadata.write_text(json.dumps({'buildx.build.provenance': {'materials': []}}))
    def fake_run(arguments, *, capture=False):
        target = Path(arguments[arguments.index('--output')+1])
        if arguments[2] == 'sbom':
            target.write_text(json.dumps({'spdxVersion': 'SPDX-2.3', 'packages': []}))
        else:
            target.write_text(json.dumps({'version': '2.1.0', 'runs': []}))
    monkeypatch.setattr(builder, '_run', fake_run)
    evidence = builder._security_evidence(
        {'id': 'document_worker', 'repository': 'ghcr.io/mhoedt-ai/plwc-personal-document-worker'},
        output, 'sha256:'+'a'*64, 'b'*40)
    assert 'vex' not in evidence
    assert not (output/'evidence/document_worker/openvex.json').exists()


def test_wheelhouse_builder_and_worker_acceptance_test_exist() -> None:
    builder = ROOT / "scripts" / "build_document_worker_wheelhouse.py"
    assert builder.is_file()
    builder_text = builder.read_text(encoding="utf-8")
    assert '"--require-hashes"' in builder_text
    assert '"--no-deps"' in builder_text
    assert "VENDORED_WHEELHOUSE" in builder_text
    assert "_write_outputs" not in builder_text
    assert "manylinux_2_28_x86_64" in builder_text
    refresher = ROOT / "scripts" / "refresh_document_worker_wheelhouse_lock.py"
    assert refresher.is_file()
    refresher_text = refresher.read_text(encoding="utf-8")
    assert "--accept-mutable-resolution" in refresher_text
    assert "_write_outputs" in refresher_text
    assert (ROOT / "scripts" / "verify_runtime_images.py").is_file()
    assert (ROOT / "scripts" / "finalize_runtime_image_manifest.py").is_file()
    assert (ROOT / "tests" / "integration" / "test_document_worker_mvp.py").is_file()


def test_registry_staging_workflow_is_manual_pinned_and_commit_scoped() -> None:
    path = ROOT / ".github" / "workflows" / "runtime-images.yml"
    text = path.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert not re.search(r"(?m)^\s{2}(?:push|pull_request|schedule):", text)
    assert "approved_commit:" in text
    assert '"$APPROVED_COMMIT" != "$GITHUB_SHA"' in text
    assert "PUBLISH_PRIVATE_PERSONAL_STAGING" in text
    assert "environment: personal-runtime-images-staging" in text
    assert "GHCR_STAGING_PAT" in text
    assert "secrets.GITHUB_TOKEN" not in text
    assert "plwc-personal-private-staging" in text
    assert "docker/staging-bootstrap" in text
    assert "packages: write" not in text
    assert text.index("Bootstrap absent private GHCR package shells") < text.index(
        "Push reproducible commit-scoped staging tags directly with BuildKit"
    )
    assert "personal-r1-staging-${GITHUB_SHA::12}" in text
    assert "python scripts/push_runtime_images.py" in text
    assert "staging-push-report.json" in text
    assert "docker image push \"${repository}:0.1.0\"" not in text
    assert "public" not in text.casefold().replace("publish_private", "")
    uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", text)
    assert uses
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", value) for value in uses)
    assert "plwc-r27-private-staging" not in text
    assert "PUBLISH_PRIVATE_R27_STAGING" not in text


def test_public_promotion_workflow_is_removed_for_personal_line() -> None:
    path = ROOT / ".github" / "workflows" / "runtime-images-public.yml"
    assert not path.exists()
    rebind = (ROOT / "scripts" / "rebind_runtime_image_manifest_personal.py").read_text(
        encoding="utf-8"
    )
    assert "plwc-personal-document-worker" in rebind
    assert "plwc-personal-node-runner" in rebind
    assert "plwc-personal-python-runner" in rebind


def test_direct_staging_push_uses_buildkit_registry_export_and_exact_identity_gate() -> None:
    text = (ROOT / "scripts" / "push_runtime_images.py").read_text(encoding="utf-8")
    assert "type=registry,name=" in text
    assert "rewrite-timestamp=true" in text
    assert "--no-cache" in text
    assert "--provenance=false" in text
    assert "--sbom=false" in text
    assert 'digest != image["digest"]' in text
    assert 'config_digest != image["config_digest"]' in text
    assert "docker image push" not in text


def test_staging_bootstrap_cannot_link_private_packages_to_the_source_repository() -> None:
    text = (ROOT / "docker" / "staging-bootstrap" / "Dockerfile").read_text(encoding="utf-8")
    assert text.splitlines()[0] == "FROM scratch"
    assert "org.opencontainers.image.source" not in text
