"""Remove exact unused Windows launcher binaries from the Linux-only images.

The remaining pip code is unchanged. Update RECORD and the bundled ensurepip
wheel so bootstrapping cannot put these binaries back into the image.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

EXPECTED = {
    "t32.exe": "6b4195e640a85ac32eb6f9628822a622057df1e459df7c17a12f97aeabc9415b",
    "t64-arm.exe": "ebc4c06b7d95e74e315419ee7e88e1d0f71e9e9477538c00a93a9ff8c66a6cfc",
    "t64.exe": "81a618f21cb87db9076134e70388b6e9cb7c2106739011b6a51772d22cae06b7",
    "w32.exe": "47872cc77f8e18cf642f868f23340a468e537e64521d9a3a416c8b84384d064b",
    "w64-arm.exe": "c5dc9884a8f458371550e09bd396e5418bf375820a31b9899f6499bf391c7b2e",
    "w64.exe": "7a319ffaba23a017d7b1e18ba726ba6c54c53d6446db55f92af53c279894f8ad",
}
RECORD = "pip-25.0.1.dist-info/RECORD"
NOTICE = "pip-25.0.1.dist-info/PLWC-LINUX-PACKAGING-NOTICE.txt"
NOTICE_BYTES = b"""PLwC Linux packaging change, 2026-10-05.
The six distlib Windows .exe launchers were removed from installed pip and
the bundled ensurepip wheel. The complete linked-runtime redistribution
rights of these binaries were not established by this engineering review.
This package supports the existing Linux runtime scope. Remaining upstream
pip Python code and original license/notice files are unchanged. RECORD is
updated. This change does not apply to Windows Python installations.
"""
PREFIX = "pip/_vendor/distlib/"


def check_launchers(files: dict[str, bytes]) -> None:
    actual = {name.removeprefix(PREFIX) for name in files if name.startswith(PREFIX) and name.endswith(".exe")}
    if actual != set(EXPECTED):
        raise ValueError("Unexpected pip launcher set")
    for name, digest in EXPECTED.items():
        if hashlib.sha256(files[PREFIX + name]).hexdigest() != digest:
            raise ValueError("Unexpected upstream launcher bytes: " + name)


def filtered_wheel(original: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(original)) as wheel:
        if len(wheel.namelist()) != len(set(wheel.namelist())):
            raise ValueError("Duplicate wheel entries")
        files = {name: wheel.read(name) for name in wheel.namelist()}
    check_launchers(files)
    if RECORD not in files:
        raise ValueError("Unexpected pip version")
    retained = {name: data for name, data in files.items() if name not in {PREFIX + name for name in EXPECTED} and name != RECORD}
    retained[NOTICE] = NOTICE_BYTES
    rows = []
    for name, data in sorted(retained.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        rows.append((name, "sha256=" + digest, str(len(data))))
    rows.append((RECORD, "", ""))
    record = io.StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerows(rows)
    retained[RECORD] = record.getvalue().encode()
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_STORED) as wheel:
        for name, data in sorted(retained.items()):
            item = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            wheel.writestr(item, data)
    return result.getvalue()


def filter_installed(root: Path) -> None:
    record = root / RECORD
    rows = list(csv.reader(io.StringIO(record.read_text())))
    files = {PREFIX + name: (root / PREFIX / name).read_bytes() for name in EXPECTED}
    check_launchers(files)
    remove = {PREFIX + name for name in EXPECTED}
    if {r[0] for r in rows if r[0] in remove} != remove:
        raise ValueError("Installed RECORD is missing launcher entries")
    for name in EXPECTED:
        (root / PREFIX / name).unlink()
    (root / NOTICE).write_bytes(NOTICE_BYTES)
    rows = [r for r in rows if r[0] not in remove and r[0] != NOTICE]
    digest = base64.urlsafe_b64encode(hashlib.sha256(NOTICE_BYTES).digest()).rstrip(b"=").decode()
    rows.append([NOTICE, "sha256=" + digest, str(len(NOTICE_BYTES))])
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(sorted(rows))
    record.write_text(stream.getvalue(), newline="\n")


def main() -> None:
    if sys.platform != "linux" or sys.version_info[:2] != (3, 12):
        raise ValueError("Filtering is restricted to the Linux CPython 3.12 runtime")
    root = Path("/usr/local/lib/python3.12")
    bundled = root / "ensurepip/_bundled/pip-25.0.1-py3-none-any.whl"
    # Validate both copies before changing the image filesystem.
    replacement = filtered_wheel(bundled.read_bytes())
    filter_installed(root / "site-packages")
    bundled.write_bytes(replacement)
    print(json.dumps({"removed_launchers_per_copy": len(EXPECTED), "bundled_wheel_sha256": hashlib.sha256(replacement).hexdigest()}))


if __name__ == "__main__":
    main()
