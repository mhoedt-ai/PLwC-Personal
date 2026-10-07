"""Copy only approved, hash-bound files; never copy development Git history."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tarfile
from pathlib import Path, PurePosixPath


class PublicationError(ValueError):
    pass


FORBIDDEN_PARTS = {'.git', '.env', '.ssh', '.aws', '.docker', 'profiles', 'workspace',
    'workspaces', 'logs', 'state', '__pycache__', 'node_modules'}
SECRET_PATTERNS = [re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    re.compile(rb'\b(?:gh[pousr]_|github_pat_|sk-(?:proj-)?)[A-Za-z0-9_\-]{20,}'),
    re.compile(rb'\bAKIA[0-9A-Z]{16}\b'),
    re.compile(rb'"(?:auth|identitytoken)"\s*:\s*"[^"\s]{12,}"')]

# This complete public file contains only a key-format delimiter, no key data.
# Its bytes were checked against jose 6.2.3's SHA-512-pinned npm archive.
# Never exempt a path, substring, changed file, or another credential pattern.
PUBLIC_KEY_FORMAT_SOURCE_SHA256 = frozenset({
    'b4e122bd70624cdbca8ca2e002e85540ac6f20e2c5c72c2b4b93e8e8ba4f2f5d',
})


def safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise PublicationError('Path is not a portable relative file path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {'', '.', '..'} for p in value.split('/')):
        raise PublicationError('Path traversal or absolute path is forbidden')
    reserved={'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
    if any(p.endswith((' ','.')) or p.split('.')[0].casefold() in reserved or
           any(ord(c)<32 or c in '<>"|?*' for c in p) for p in path.parts):
        raise PublicationError('Nonportable or aliased Windows file path')
    public_template=len(path.parts)>2 and path.parts[:2]==('profiles','template')
    if any(p.casefold().startswith('.env') or p.casefold() in {'security.yaml','security.yml'} for p in path.parts):
        raise PublicationError('Private environment/security configuration is forbidden')
    if any(p.casefold() in FORBIDDEN_PARTS and not (p=='profiles' and public_template) for p in path.parts):
        raise PublicationError('Private build/runtime directory is forbidden')
    return path.as_posix()


def checked_file(root: Path, relative: str) -> Path:
    relative = safe_relative(relative)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        info = current.lstat()
        if current.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise PublicationError('Reparse points are forbidden')
    if not current.is_file():
        raise PublicationError('Approved input is not a regular file')
    return current


def scan_forbidden_bytes(data: bytes, *, private_roots: tuple[str, ...] = ()) -> None:
    key_marker = SECRET_PATTERNS[0].search(data)
    if (key_marker and hashlib.sha256(data).hexdigest() not in PUBLIC_KEY_FORMAT_SOURCE_SHA256) or any(
        pattern.search(data) for pattern in SECRET_PATTERNS[1:]
    ):
        raise PublicationError('Private key or credential marker in approved input')
    lowered = data.lower()
    variants=[]
    for root in private_roots:
        if root:
            variants.extend(value.encode('utf-8').lower() for value in (root,root.replace('\\','/'),json.dumps(root)[1:-1]))
            variants.append(root.encode('utf-16le').lower())
    if any(root in lowered for root in variants):
        raise PublicationError('Real private workspace/user path in approved input')


def file_record(root: Path, relative: str, *, target: str | None = None) -> dict:
    path = checked_file(root, relative)
    return {'path': relative, 'target': safe_relative(target or relative),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def scan_stream(handle, *, private_roots: tuple[str,...] = ()) -> None:
    tail=b''
    while True:
        chunk=handle.read(1024*1024)
        if not chunk:break
        data=tail+chunk
        scan_forbidden_bytes(data,private_roots=private_roots)
        tail=data[-4096:]


def scan_image_archive(path: Path, *, private_roots: tuple[str,...] = (), required_files: dict[str, bytes] | None = None) -> dict:
    """Inspect every exported Docker layer, including deleted lower-layer bytes, without extraction."""
    layers=0
    required_files=required_files or {}
    present={}
    with tarfile.open(path,'r:*') as archive:
        layer_names=set()
        if 'manifest.json' in archive.getnames():
            descriptor=json.load(archive.extractfile('manifest.json'))
            if not isinstance(descriptor,list) or not descriptor:
                raise PublicationError('Docker manifest is missing')
            for image in descriptor:layer_names.update(image.get('Layers',[]))
        names=set()
        for member in archive:
            name=member.name.removeprefix('./')
            if name in names or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise PublicationError('Unsafe or duplicate image archive entry')
            names.add(name)
            if not member.isfile():continue
            handle=archive.extractfile(member)
            if handle is None:raise PublicationError('Unreadable image archive member')
            prefix=handle.read(512);handle.seek(0)
            if name in layer_names or name.endswith('/layer.tar') or name.endswith('.tar.gz') or prefix[257:262]==b'ustar' or prefix.startswith(b'\x1f\x8b'):
                layers+=1
                added={}; removed=[]
                with tarfile.open(fileobj=handle,mode='r|*') as layer:
                    for item in layer:
                        p=PurePosixPath(item.name.removeprefix('./'))
                        if p.is_absolute() or '..' in p.parts:
                            raise PublicationError('Unsafe OCI layer entry')
                        normalized=p.as_posix()
                        if p.name=='.wh..wh..opq':removed.append(p.parent.as_posix()+'/')
                        elif p.name.startswith('.wh.'):removed.append((p.parent/p.name[4:]).as_posix())
                        scan_forbidden_bytes((item.name+' '+item.linkname).encode(),private_roots=private_roots)
                        if item.isfile():
                            content=layer.extractfile(item)
                            if content is None:raise PublicationError('Unreadable OCI layer entry')
                            if normalized in required_files:
                                data=content.read(len(required_files[normalized])+1)
                                if len(data)!=item.size:raise PublicationError('Artifact grant has unexpected size')
                                scan_forbidden_bytes(data,private_roots=private_roots)
                                added[normalized]=data
                            else:scan_stream(content,private_roots=private_roots)
                        elif normalized in required_files:
                            raise PublicationError('Artifact grant is not a regular file')
                for deleted in removed:
                    for target in list(present):
                        if target==deleted or target.startswith(deleted.rstrip('/')+'/'):present.pop(target)
                present.update(added)
            else:
                scan_stream(handle,private_roots=private_roots)
        if layer_names-set(names):raise PublicationError('Docker export omitted a declared layer')
    if layers==0:raise PublicationError('No complete Docker layers were inspected')
    if present!=required_files:raise PublicationError('Final image grants are missing or differ from approved bytes')
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return {'status':'pass','layers_inspected':layers,'archive_sha256':digest.hexdigest(),
        'required_files_checked':sorted(required_files)}


def copy_allowlisted_tree(root: Path, output: Path, records: list[dict], *, private_roots: tuple[str,...] = ()) -> dict:
    if root.is_symlink() or getattr(root.lstat(),'st_file_attributes',0)&0x400:
        raise PublicationError('Source root is a reparse point')
    root = root.resolve(strict=True)
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise PublicationError('Output must be a new directory')
    # Validate every byte before creating any output or invoking a builder.
    files = []
    targets = set()
    for record in records:
        if set(record) != {'path','target','sha256'}:
            raise PublicationError('File allowlist record is incomplete or unknown')
        source = checked_file(root, record['path'])
        target = safe_relative(record['target'])
        if target.casefold() in targets:
            raise PublicationError('Duplicate/case-aliased output path')
        targets.add(target.casefold())
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != record['sha256']:
            raise PublicationError('Approved input bytes changed')
        scan_forbidden_bytes(data, private_roots=private_roots)
        files.append((target,data,record['sha256']))
    if not files:
        raise PublicationError('Empty file allowlist')
    # Do not follow output parent junctions/symlinks either.
    current = output.parent
    while current != current.parent:
        if current.exists() and (current.is_symlink() or getattr(current.lstat(),'st_file_attributes',0)&0x400):
            raise PublicationError('Output parent is a reparse point')
        current = current.parent
    output.mkdir(parents=True, exist_ok=False)
    try:
        for target,data,_ in files:
            path=output/target;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as handle:handle.write(data)
    except BaseException:
        # Leave a partial new output for inspection; never recursively clean an unverified path.
        raise
    return {'schema_version':'1.0.0','status':'source_tree_prepared',
        'files':[{'path':p,'sha256':h,'size':len(b)} for p,b,h in files],
        'history_included':False,'publication_commit':None}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--allowlist',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    specification=json.loads(args.allowlist.read_text(encoding='utf-8'))
    if set(specification) != {'schema_version','files'} or specification['schema_version']!='1.0.0':
        raise PublicationError('Invalid explicit source allowlist')
    # A prepared tree still needs review and an actual new publication commit.
    report=copy_allowlisted_tree(args.root,args.output,specification['files'],
        private_roots=(str(args.root.resolve()), os.environ.get('USERPROFILE','')))
    args.output.with_suffix('.source-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'files':len(report['files']),'history_included':False}))
    return 0


if __name__=='__main__':raise SystemExit(main())
