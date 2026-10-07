from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "rebind_runtime_image_manifest_personal.py"
SPEC = importlib.util.spec_from_file_location("personal_runtime_rebind", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _manifest() -> dict[str, object]:
    images: list[dict[str, object]] = []
    for index, (image_id, repository) in enumerate(MODULE.SOURCE_REPOSITORIES.items(), start=1):
        digest = "sha256:" + str(index) * 64
        images.append(
            {
                "id": image_id,
                "version": "0.1.0",
                "digest": digest,
                "repository": repository,
                "reference": f"{repository}@{digest}",
                "display_tag": f"{repository}:0.1.0",
                "evidence": {"kept": True},
            }
        )
    return {"schema_version": "1.0.0", "source_commit": "a" * 40, "images": images}


def test_rebind_changes_only_distribution_references() -> None:
    source = _manifest()
    rebound = MODULE.rebind_manifest(source)

    assert source["images"][0]["repository"] == MODULE.SOURCE_REPOSITORIES["document_worker"]
    for image in rebound["images"]:
        image_id = image["id"]
        repository = MODULE.PERSONAL_REPOSITORIES[image_id]
        assert image["repository"] == repository
        assert image["reference"] == f"{repository}@{image['digest']}"
        assert image["display_tag"] == f"{repository}:0.1.0"
        assert image["evidence"] == {"kept": True}


def test_rebind_rejects_an_unexpected_source_repository() -> None:
    source = _manifest()
    source["images"][0]["repository"] = "ghcr.io/foreign/image"

    with pytest.raises(MODULE.RebindError, match="Unexpected source repository"):
        MODULE.rebind_manifest(source)
