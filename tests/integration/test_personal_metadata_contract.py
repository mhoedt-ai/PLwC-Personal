"""Personal-owned metadata must not describe the old Apache release line."""

from __future__ import annotations

import json
from pathlib import Path

from plwc_gateway.installation.update_center import load_trusted_release_keys


ROOT = Path(__file__).resolve().parents[2]
SOURCE = "https://github.com/mhoedt-ai/PLwC-Personal"
LICENSE = "LicenseRef-PLwC-Personal-1.0"
PERSONAL_KEY_ID = "plwc-personal-rsa-43b5314e2d46e3ca668fe409a9670582ab8af26c7dc6d4bcca44f3522c7079b8"


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_product_and_license_metadata() -> None:
    mcpb = _json("manifest.json")
    assert mcpb["display_name"] == "PLwC Personal Gateway"
    assert mcpb["version"] == "1.0.0"
    assert mcpb["license"] == LICENSE

    registry = _json("server.json")
    assert registry["title"].startswith("PLwC Personal")
    assert registry["repository"]["url"] == SOURCE
    assert all(SOURCE in package["identifier"] for package in registry["packages"])


def test_installer_and_update_identity() -> None:
    installer = (ROOT / "installer/windows/PLwCSetup.iss").read_text(encoding="utf-8")
    assert '#define MyAppName "PLwC Personal"' in installer
    assert "UninstallDisplayName=PLwC Personal" in installer

    config = (ROOT / "installer/windows/assets/configuration/plwc-config.py").read_text(
        encoding="utf-8"
    )
    assert f"{SOURCE}/releases/latest/download/plwc-personal-release-manifest.json" in config
    assert "mhoedt-ai/PLwC/releases/latest" not in config
    # Public identity cross-checked after the owner's real recovery ceremony.
    # No private key or signing passphrase is a test dependency.
    assert set(load_trusted_release_keys(ROOT / "config/release-trust.json")) == {PERSONAL_KEY_ID}
    manifest_schema = _json("config/release-manifest.schema.json")
    assert manifest_schema["properties"]["product"]["properties"]["name"] == {
        "const": "PLwC Personal"
    }

    store = _json("integrations/plwc-chat-bridge/extension/store/store-contract.json")
    assert store["setupDownload"]["releasesUrl"] == f"{SOURCE}/releases"
    assert store["setupDownload"]["reviewerArtifactUrl"] is None
    assert store["setupDownload"]["reviewerArtifactSha256"] is None


def test_runtime_source_and_oci_license_identity() -> None:
    source = _json("docker/runtime-image-sources.json")
    assert source["source_repository"] == SOURCE
    assert all("/plwc-personal-" in image["repository"] for image in source["images"])
    for component in ("document-worker", "node-runner", "python-runner"):
        dockerfile = (ROOT / "docker" / component / "Dockerfile").read_text(encoding="utf-8")
        assert f'org.opencontainers.image.source="{SOURCE}"' in dockerfile
        assert f'org.opencontainers.image.licenses="{LICENSE}"' in dockerfile


def test_third_party_apache_licenses_are_not_rewritten() -> None:
    lock = _json("integrations/plwc-chat-bridge/extension/package-lock.json")
    third_party = [
        package for name, package in lock["packages"].items()
        if name.startswith("node_modules/") and package.get("license") == "Apache-2.0"
    ]
    assert third_party


def test_installer_and_mcpb_package_personal_grants() -> None:
    required = ("PERSONAL_USE_PERMISSION.md", "OFFICIAL_REDISTRIBUTION_PERMISSION.md", "LICENSING.md")
    for script in ("installer/windows/build.ps1", "scripts/build-mcpb.ps1"):
        contents = (ROOT / script).read_text(encoding="utf-8")
        for name in required:
            assert f'"{name}"' in contents


def test_personal_package_guides_do_not_offer_old_setup() -> None:
    packaged_guides = (
        "README.md",
        "docs/INSTALLATION.md",
        "docs/TROUBLESHOOTING.md",
        "docs/SECURITY_MODEL.md",
        "docs/CONFIGURATION.md",
        "integrations/plwc-chat-bridge/extension/store/listing-en.md",
    )
    obsolete = (
        "https://github.com/mhoedt-ai/PLwC/releases/download/",
        "PLwC-Setup-1.0.0-installer-r24.exe",
        "b00c5298bf6faa76c5910ecbb36497a8aa4764a8a3720f73a450851a3fc3e4d0",
    )
    for path in packaged_guides:
        text = (ROOT / path).read_text(encoding="utf-8")
        for value in obsolete:
            assert value not in text, f"Old Setup instruction in {path}: {value}"
