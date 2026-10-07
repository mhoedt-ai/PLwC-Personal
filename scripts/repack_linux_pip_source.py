"""Prepare the corresponding Linux pip/distlib source tree without PE launchers."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("linux_pip_filter", ROOT / "docker/filter-linux-pip.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def repack(source: Path, output: Path, expected_sha256: str) -> str:
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("Source archive identity differs")
    retained = {}
    removed = set()
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for entry in archive:
            if not entry.isfile():
                if not entry.isdir():
                    raise ValueError("Unsupported source entry type")
                continue
            path = Path(entry.name)
            if path.is_absolute() or ".." in path.parts or entry.name in retained:
                raise ValueError("Unsafe or duplicate source path")
            body = archive.extractfile(entry).read()
            if path.suffix.lower() == ".exe":
                if path.name not in module.EXPECTED or "distlib" not in path.parts:
                    raise ValueError("Unexpected executable in source tree")
                if hashlib.sha256(body).hexdigest() != module.EXPECTED[path.name]:
                    raise ValueError("Unexpected launcher bytes")
                removed.add(path.name)
                continue
            retained[entry.name] = (body, entry.mode)
    if removed != set(module.EXPECTED):
        raise ValueError("Expected six launchers are missing")
    prefix = next(iter(retained)).split("/", 1)[0]
    retained[prefix + "/PLWC-LINUX-PACKAGING-NOTICE.txt"] = (module.NOTICE_BYTES, 0o644)
    with tarfile.open(output, "x", format=tarfile.PAX_FORMAT) as archive:
        for name, (body, mode) in sorted(retained.items()):
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode, entry.mtime = len(body), mode, 946684800
            archive.addfile(entry, io.BytesIO(body))
    return hashlib.sha256(output.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--input-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(repack(args.input, args.output, args.input_sha256))
