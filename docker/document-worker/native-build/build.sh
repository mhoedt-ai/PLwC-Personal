#!/bin/sh
# Copyright 2026 Mirco Hoedt.
# This library-build recipe is licensed under LGPL-2.1-or-later.
# Full text: COPYING.LIB accompanies this recipe in /inputs.
# Run with read-only /inputs and fresh writable /work and /outputs on Linux.
set -eu
# Build tools are prepared separately; this recipe makes no network requests.
python - <<'PY'
import platform,subprocess
assert platform.system()=='Linux' and platform.machine()=='x86_64'
assert platform.python_version()=='3.12.14'
expected={'gcc-14-x86-64-linux-gnu':'14.2.0-19','g++-14-x86-64-linux-gnu':'14.2.0-19','libc6-dev':'2.41-12+deb13u4','binutils':'2.44-3','make':'4.4.1-2','pkg-config':'1.8.1-4'}
for name,version in expected.items():
    assert subprocess.check_output(['dpkg-query','-W','-f=${Version}',name],text=True)==version,name
import pathlib,hashlib,json
manifest=json.loads(pathlib.Path('/inputs/input-manifest.json').read_text())
for record in manifest['inputs']+manifest['recipe_inputs']:
    p=pathlib.Path('/inputs')/record['name']
    assert p.stat().st_size==record['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],record['name']
assert not any(pathlib.Path('/work').iterdir()),'Use a fresh empty /work'
PY
python -m pip install --no-index --no-deps /inputs/setuptools-70.3.0-py3-none-any.whl
mkdir -p /work/src /work/prefix
cd /work/src
python - <<'PY'
import tarfile,pathlib
for fn in ['lxml-6.1.0-plwc-filtered.tar','libiconv-1.18-linux-source.tar','libxml2-2.14.6.tar.xz','libxslt-1.1.43.tar.xz','zlib-1.3.2.tar.gz']:
    with tarfile.open('/inputs/'+fn) as t: t.extractall('/work/src',filter='data')
PY
python - <<'PYHEADERS'
import pathlib,shutil,subprocess,hashlib,json
original=pathlib.Path(subprocess.check_output(['gcc','-print-file-name=include'],text=True).strip())
assert str(original)=='/usr/lib/gcc/x86_64-linux-gnu/14/include'
target=pathlib.Path('/work/src/compiler-headers')
shutil.copytree(original,target)
for name in ['syslimits.h','stdint.h']:shutil.copyfile('/inputs/'+name,target/name)
records=[]
for p in sorted(target.rglob('*')):
    if p.is_file():
        old=original/p.relative_to(target);data=p.read_bytes()
        records.append({'path':p.relative_to(target).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'original_toolchain_path':str(old),'original_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'authored_replacement':p.name in ['syslimits.h','stdint.h']})
pathlib.Path('/outputs/header-routing-inputs.json').write_text(json.dumps(records,indent=2))
PYHEADERS
export CFLAGS='-O1 -g0 -fPIC -MD -isystem /work/src/compiler-headers'
export LDFLAGS='-fPIC'
cd /work/src/zlib-1.3.2
./configure --static --prefix=/work/prefix
make -j2
make install
cd /work/src/libiconv-1.18
# The supplied tree already contains the adapted macro and generated configure.
# Optional user modification is applied to preferred source before compilation.
if test -f /inputs/libiconv-edit.py; then python /inputs/libiconv-edit.py; fi
./configure --disable-dependency-tracking --disable-shared --prefix=/work/prefix
make -j2
make install
cd /work/src/libxml2-2.14.6
./configure --disable-dependency-tracking --disable-shared --prefix=/work/prefix --without-python --with-iconv=/work/prefix --with-zlib=/work/prefix --without-lzma --enable-rebuild-docs=no
make -j2
make install
cd /work/src/libxslt-1.1.43
./configure --disable-dependency-tracking --disable-shared --prefix=/work/prefix --without-python --with-libxml-prefix=/work/prefix --without-crypto
make -j2
make install
cd /work/src/lxml-6.1.0
export LXML_STATIC_INCLUDE_DIRS='/work/prefix/include:/work/prefix/include/libxml2:/work/prefix/include/libxslt:/work/prefix/include/libexslt'
export LXML_STATIC_LIBRARY_DIRS='/work/prefix/lib'
export LXML_STATIC_BINARIES='/work/prefix/lib/libexslt.a:/work/prefix/lib/libxslt.a:/work/prefix/lib/libxml2.a:/work/prefix/lib/libz.a:/work/prefix/lib/libiconv.a:/work/prefix/lib/libcharset.a'
python setup.py build_ext --inplace --static --without-cython --with-xml2-config=/work/prefix/bin/xml2-config --with-xslt-config=/work/prefix/bin/xslt-config
python - <<'PY'
import hashlib,json,pathlib,subprocess,shutil
root=pathlib.Path('/work/src/lxml-6.1.0/src/lxml');out=pathlib.Path('/outputs/extensions');out.mkdir()
extensions=[]
for p in root.rglob('*.so'):
 rel=p.relative_to(root);target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 extensions.append({'path':str(rel),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'elf_dependencies':subprocess.check_output(['ldd',str(p)],text=True)})
assert len(extensions)==7,extensions
archives=[]
for p in pathlib.Path('/work/prefix/lib').glob('*.a'):
 target=pathlib.Path('/outputs/static-libraries')/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
 archives.append({'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'members':subprocess.check_output(['ar','t',str(p)],text=True).splitlines()})
# Capture actual GCC -MD dependency inputs, including system/Python/prefix headers.
import re
source_root=pathlib.Path('/work/src');prefix_root=pathlib.Path('/work/prefix')
dependencies=[];all_inputs={};missing=[]
def identify(p):
    if p.is_relative_to(source_root):return 'source_tree',p.relative_to(source_root).as_posix()
    if p.is_relative_to(prefix_root):return 'prefix',p.relative_to(prefix_root).as_posix()
    return 'system',p.as_posix().lstrip('/')
for dep in sorted(source_root.rglob('*.d')):
    text=dep.read_text(errors='strict');logical=text.replace(chr(92)+chr(10),' ').splitlines()[0]
    assert ':' in logical
    tokens=logical.split(':',1)[1].split();paths=[];unresolved=[]
    for token in tokens:
        if token.endswith(':'):continue
        original=pathlib.Path(token)
        candidates=[original] if original.is_absolute() else [parent/original for parent in [dep.parent,*dep.parents]]
        p=next((p.resolve() for p in candidates if p.exists() and p.is_file()),None)
        if p is None:
            unresolved.append(token);continue
        category,relative=identify(p);key=category+'/'+relative
        b=p.read_bytes();dest=pathlib.Path('/outputs/compiler-inputs')/key
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
        owner=[]
        if category=='system':
            query=subprocess.run(['dpkg-query','-S',str(p)],capture_output=True,text=True)
            if query.returncode==0:owner=query.stdout.strip().splitlines()
        rec={'category':category,'path':relative,'compiler_path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'dpkg_owner_receipts':owner}
        if key in all_inputs:assert rec==all_inputs[key]
        all_inputs[key]=rec;paths.append(key)
    relative=dep.relative_to(source_root).as_posix()
    dependencies.append({'path':relative,'sha256':hashlib.sha256(dep.read_bytes()).hexdigest(),'bytes':dep.stat().st_size,'input_paths':paths,'unresolved_paths':unresolved,'raw_dependency_output':text})
    if unresolved:missing.append({'dependency':relative,'tokens':unresolved})
pathlib.Path('/outputs/compiled-full-inputs.json').write_text(json.dumps({'dependency_files':dependencies,'input_files':list(all_inputs.values()),'unresolved':missing,'scope':'Actual adapted unmarked-library rebuild preprocessing dependencies from GCC -MD. This does not identify the original wheel toolchain, assembler/linker inputs, or grant approval.'},indent=2)+'\n')
result={'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'extensions':extensions,'static_archives':archives,'packages':subprocess.check_output(['dpkg-query','-W','-f=${Package}\t${Version}\n'],text=True),'source_build':True,'upstream_binary_identity_claimed':False}
pathlib.Path('/outputs/build-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'seven_lxml_extensions_compiled':True,'etree':next(p for p in extensions if p['path'].startswith('etree.'))}))
PY
