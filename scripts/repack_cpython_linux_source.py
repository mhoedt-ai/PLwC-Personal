"""Preserve exact CPython sources while applying the Linux ensurepip packaging recipe."""
from __future__ import annotations
import argparse,hashlib,importlib.util,io
from pathlib import Path,PurePosixPath
import tarfile

ROOT=Path(__file__).resolve().parents[1]
EXPECTED='5c8462af5790baf43a321a1559dbe0db06d1be4300fb85fb53c40060668e548a'
BUNDLED='Python-3.12.14/Lib/ensurepip/_bundled/pip-25.0.1-py3-none-any.whl'

def repack(source:Path,output:Path)->str:
    data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=EXPECTED:raise ValueError('CPython archive identity differs')
    spec=importlib.util.spec_from_file_location('filter_linux_pip',ROOT/'docker/filter-linux-pip.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    replaced=False;seen=set()
    with tarfile.open(fileobj=io.BytesIO(data)) as source_tar,tarfile.open(output,'x',format=tarfile.PAX_FORMAT) as dest:
        for entry in source_tar:
            path=PurePosixPath(entry.name)
            if path.is_absolute() or '..' in path.parts or entry.name in seen:raise ValueError('Unsafe or duplicate source entry')
            seen.add(entry.name)
            if entry.isdir():continue
            if not entry.isfile():raise ValueError('Unexpected source entry type')
            body=source_tar.extractfile(entry).read()
            if entry.name==BUNDLED:body=module.filtered_wheel(body);replaced=True
            item=tarfile.TarInfo(entry.name);item.size=len(body);item.mode=entry.mode;item.mtime=946684800
            dest.addfile(item,io.BytesIO(body))
        if not replaced:raise ValueError('Expected ensurepip wheel is absent')
        notice=module.NOTICE_BYTES
        item=tarfile.TarInfo('Python-3.12.14/PLWC-LINUX-PACKAGING-NOTICE.txt');item.size=len(notice);item.mode=0o644;item.mtime=946684800
        dest.addfile(item,io.BytesIO(notice))
    return hashlib.sha256(output.read_bytes()).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(repack(args.input,args.output))
