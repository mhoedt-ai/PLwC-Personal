"""Rebind an approved r27 runtime-image lock to private PLwC Personal packages.

The image manifests, digests, OCI labels, SBOMs and security evidence remain
unchanged.  Only the distribution repository, digest reference and display tag
are replaced.  The source repository and source commit deliberately keep the
original build provenance.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


SOURCE_REPOSITORIES = {
    "document_worker": "ghcr.io/mhoedt-ai/plwc-document-worker",
    "node_runner": "ghcr.io/mhoedt-ai/plwc-node-runner",
    "python_runner": "ghcr.io/mhoedt-ai/plwc-python-runner",
}
PERSONAL_REPOSITORIES = {
    "document_worker": "ghcr.io/mhoedt-ai/plwc-personal-document-worker",
    "node_runner": "ghcr.io/mhoedt-ai/plwc-personal-node-runner",
    "python_runner": "ghcr.io/mhoedt-ai/plwc-personal-python-runner",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class RebindError(ValueError):
    pass


def rebind_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RebindError("Runtime image manifest must be an object.")
    result = dict(value)
    images = result.get("images")
    if not isinstance(images, list) or len(images) != len(PERSONAL_REPOSITORIES):
        raise RebindError("Runtime image manifest must contain exactly three images.")

    rebound: list[dict[str, Any]] = []
    observed: set[str] = set()
    for raw_image in images:
        if not isinstance(raw_image, Mapping):
            raise RebindError("Runtime image entry must be an object.")
        image = dict(raw_image)
        image_id = str(image.get("id", ""))
        if image_id in observed or image_id not in PERSONAL_REPOSITORIES:
            raise RebindError(f"Unexpected or duplicate runtime image ID: {image_id}")
        observed.add(image_id)

        digest = image.get("digest")
        source_repository = SOURCE_REPOSITORIES[image_id]
        if image.get("repository") != source_repository:
            raise RebindError(f"Unexpected source repository for {image_id}.")
        if image.get("version") != "0.1.0" or not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
            raise RebindError(f"Invalid version or digest for {image_id}.")
        if image.get("reference") != f"{source_repository}@{digest}":
            raise RebindError(f"Source reference is not digest-locked for {image_id}.")
        if image.get("display_tag") != f"{source_repository}:0.1.0":
            raise RebindError(f"Unexpected source display tag for {image_id}.")

        personal_repository = PERSONAL_REPOSITORIES[image_id]
        image["repository"] = personal_repository
        image["reference"] = f"{personal_repository}@{digest}"
        image["display_tag"] = f"{personal_repository}:0.1.0"
        rebound.append(image)

    if observed != set(PERSONAL_REPOSITORIES):
        raise RebindError("Runtime image IDs are incomplete.")
    result["images"] = rebound
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    source = args.source.resolve(strict=True)
    output = args.output.resolve(strict=False)
    if source == output:
        raise RebindError("Source and output paths must differ.")
    value = json.loads(source.read_text(encoding="utf-8-sig"))
    rebound = rebind_manifest(value)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rebound, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
