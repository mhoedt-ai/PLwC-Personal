"""Inventory PLwC release metadata without rewriting historical or third-party data."""

from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "evidence" / "plwc-personal-metadata-inventory.csv"
PATTERNS = {
    "license": re.compile(r"Apache-2\.0|Apache 2\.0|LicenseRef-PLwC-Personal-1\.0|PolyForm(?: Internal Use)?", re.I),
    "repository": re.compile(r"(?:https://)?github\.com/mhoedt-ai/PLwC(?:-Personal)?(?:\.git)?", re.I),
    "download": re.compile(r"PLwC(?:-Personal)?-Setup-[A-Za-z0-9_.-]+\.exe|releases/(?:download|latest)/[^\s\"'<>]+", re.I),
    "update": re.compile(r"plwc(?:-personal)?-release-manifest\.json|release-trust\.json", re.I),
    "product": re.compile(r"PLwC Personal|PLwC Gateway|PLwC Chat Bridge", re.I),
    "oci": re.compile(r"org\.opencontainers\.image\.(?:source|licenses|version)", re.I),
}
EXCLUDED = {
    "scripts/inventory_personal_metadata.py",
    "docs/evidence/plwc-personal-metadata-inventory.csv",
    "docs/evidence/personal-r1-metadata-inventory.csv",
}
HISTORICAL_PREFIXES = ("docs/evidence/", "installer/windows/evidence/", "LICENSES/", "security/vex/")
HISTORICAL_FILES = {
    "BETA_TESTING.md",
    "docs/BRIEFING_PLWC_PERSONAL_NEUER_CHAT.md",
    "docs/BRIEFING_R26_NEUER_CHAT.md",
    "docs/EXTERNAL_TESTER_GUIDE.md",
    "docs/GITHUB_BETA_WORKFLOW.md",
    "docs/R27_WINDOWS_IMAGE_DELIVERY_PLAN_DE.md",
    "docs/R26_WINDOWS_TEST_MATRIX.md",
    "docs/PERSONAL_R1_RUNTIME_IMAGES_DE.md",
    "docs/PROGRAM_AND_SOFTWARE_DESCRIPTION_OPEN_BETA.md",
    "docs/PROGRAM_AND_SOFTWARE_DESCRIPTION_1_0.md",
    "integrations/plwc-chat-bridge/extension/store/README.md",
    "installer/windows/README.md",
    "scripts/rebind_runtime_image_manifest_personal.py",
}
FIELDNAMES = ("path", "line", "kind", "ownership", "disposition", "value")


def classify(path: str, kind: str, value: str) -> tuple[str, str]:
    if (path.endswith("package-lock.json") or path == "docker/document-worker/vendored-wheels/README.md") and kind == "license":
        return "third_party", "preserve"
    if (
        path == "integrations/plwc-chat-bridge/extension/scripts/build-store-packages.ps1"
        and kind == "license"
        and value.casefold() == "apache-2.0"
    ):
        return "historical_or_policy_reference", "preserve"
    if path.startswith(HISTORICAL_PREFIXES) or path in HISTORICAL_FILES:
        return "historical", "preserve"
    if kind in {"license", "download"} and path == "installer/windows/V_MODEL.md":
        return "historical_or_policy_reference", "preserve"
    if kind == "license" and path in {
        "LICENSING.md", "README.md", "docs/PLWC_PERSONAL_1_0_LOCAL_POLICY.md",
        "docs/PLWC_PERSONAL_PRODUCT_CONTRACT_DE.md", "docs/PLWC_PERSONAL_RELEASE_PLAN_DE.md",
        "installer/windows/build.ps1", "scripts/build-mcpb.ps1",
    }:
        return "historical_or_policy_reference", "preserve"
    if path.startswith("tests/") or "/tests/" in path or path.endswith(".test.ts"):
        return "test_fixture", "review"
    if kind == "repository" and re.search(r"/PLwC(?:\.git)?$", value.rstrip("`")):
        return "plwc_owned_or_productive", "migrate_or_justify"
    if kind == "license" and value.casefold() in {"apache-2.0", "apache 2.0"}:
        return "plwc_owned_or_productive", "justify_historical_or_third_party"
    if kind == "download" and "installer-r" in value.casefold():
        return "plwc_owned_or_productive", "retire_old_download"
    return "plwc_owned_or_productive", "verify"


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"),
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return sorted({name.decode("utf-8").replace("\\", "/") for name in result.stdout.split(b"\0") if name})


def inventory() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for path in tracked_paths():
        if path in EXCLUDED:
            continue
        try:
            raw = (ROOT / path).read_bytes()
            if b"\0" in raw or len(raw) > 2_000_000:
                continue
            contents = raw.decode("utf-8-sig")
        except (OSError, UnicodeError):
            continue
        for line_number, line in enumerate(contents.splitlines(), start=1):
            for kind, pattern in PATTERNS.items():
                for match in pattern.finditer(line):
                    ownership, disposition = classify(path, kind, match.group(0))
                    rows.append({
                        "path": path,
                        "line": line_number,
                        "kind": kind,
                        "ownership": ownership,
                        "disposition": disposition,
                        "value": match.group(0),
                    })
    return rows


def render(rows: list[dict[str, str | int]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    rendered = render(inventory())
    if arguments.check:
        return 0 if arguments.output.read_text(encoding="utf-8") == rendered else 1
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(rendered, encoding="utf-8", newline="")
    print(f"Wrote {len(rendered.splitlines()) - 1} metadata occurrences to {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
