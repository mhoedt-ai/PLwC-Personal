#!/bin/sh
# PLwC demonstration changes: Copyright 2026 Mirco Hoedt, LGPL-2.1-or-later.
set -eu
python - <<'PY'
from pathlib import Path
import tarfile,hashlib,shutil,subprocess,json
root=Path('/work');assert not any(root.iterdir())
archive=Path('/inputs/gcc-4.8.5-20150702.tar.bz2');assert hashlib.sha256(archive.read_bytes()).hexdigest()=='0ae59dc99f382e2d60736359f89eabf7616fe5a4410bbbda065c233e059d5f32'
with tarfile.open(archive) as t:
 selected=[m for m in t if m.name.startswith(('gcc-4.8.5-20150702/libquadmath/','gcc-4.8.5-20150702/config/','gcc-4.8.5-20150702/libgcc/','gcc-4.8.5-20150702/include/')) or m.name.count('/')<=1]
 t.extractall(root,members=selected,filter='data')
view=root/'compiler-headers';shutil.copytree(Path(subprocess.check_output(['gcc','-print-file-name=include'],text=True).strip()),view)
for name in ['syslimits.h','stdint.h']:shutil.copyfile('/inputs/'+name,view/name)
source=root/'gcc-4.8.5-20150702/libquadmath/math/expq.c';original=source.read_bytes()
needle=b'__float128\nexpq (__float128 x)\n{';assert original.count(needle)==1
modified=original.replace(needle,b'static int plwc_quadmath_modified_called = 0;\n'+needle+b'\n  plwc_quadmath_modified_called = 1;')
modified+=b'\n/* PLwC modification: 2026 Mirco Hoedt, LGPL-2.1-or-later. */\nint plwc_quadmath_modified_probe(void) { volatile __float128 x = 0.0Q; return expq(x) == 1.0Q; }\nconst char *plwc_quadmath_modified_marker(void) { return plwc_quadmath_modified_called ? "PLwC modified quadmath executed" : "not called"; }\n'
source.write_bytes(modified);Path('/outputs/modified-expq.c').write_bytes(modified)
mapping=source.parents[1]/'quadmath.map';original_map=mapping.read_bytes();assert original_map.count(b'  global:\n')==1
new_map=original_map.replace(b'  global:\n',b'  global:\n    plwc_quadmath_modified_probe;\n    plwc_quadmath_modified_marker;\n');mapping.write_bytes(new_map);Path('/outputs/modified-quadmath.map').write_bytes(new_map)
Path('/outputs/source-modification.json').write_text(json.dumps({'source_original_sha256':hashlib.sha256(original).hexdigest(),'source_modified_sha256':hashlib.sha256(modified).hexdigest(),'map_original_sha256':hashlib.sha256(original_map).hexdigest(),'map_modified_sha256':hashlib.sha256(new_map).hexdigest(),'license':'LGPL-2.1-or-later','scope':'Adds an execution marker and two probe exports without altering numerical formulas.'},indent=2)+'\n')
PY
mkdir /work/quadmath-build
cd /work/quadmath-build
/work/gcc-4.8.5-20150702/libquadmath/configure --disable-multilib --disable-static --enable-shared --prefix=/work/install CFLAGS='-O1 -g0 -fPIC -MD -isystem /work/compiler-headers'
make -j2
cp .libs/libquadmath.so.0.0.0 /outputs/libquadmath.so.0.0.0
python - <<'PY'
from pathlib import Path
import hashlib,json,subprocess,shutil
base=Path('/work/quadmath-build');root=Path('/work');captured={};receipts=[]
for d in sorted(base.rglob('*.Plo')):
 text=d.read_text().replace(chr(92)+chr(10),' ');first=text.splitlines()[0];assert ':' in first
 tokens=first.split(':',1)[1].split();paths=[]
 for token in tokens:
  p=Path(token);p=(p if p.is_absolute() else base/p).resolve();assert p.is_file(),str(p)
  category='preferred_or_generated_source' if p.is_relative_to(root) else 'system_header'
  relative=p.relative_to(root).as_posix() if p.is_relative_to(root) else p.as_posix().lstrip('/')
  key=category+'/'+relative;b=p.read_bytes();dest=Path('/outputs/compiler-inputs')/key;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
  row={'path':key,'compiler_path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
  if key in captured:assert captured[key]==row
  captured[key]=row;paths.append(key)
 receipts.append({'path':d.relative_to(base).as_posix(),'sha256':hashlib.sha256(d.read_bytes()).hexdigest(),'input_paths':paths})
assert len(receipts)>30
for n in ['config.log','config.status','config.h','Makefile']:shutil.copyfile(base/n,Path('/outputs')/n)
library=Path('/outputs/libquadmath.so.0.0.0')
r={'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'library_bytes':library.stat().st_size,'compiler_inputs':list(captured.values()),'dependency_receipts':receipts,'ELF_dynamic_entries':subprocess.check_output(['readelf','-d',str(library)],text=True),'ELF_symbols':subprocess.check_output(['readelf','-Ws',str(library)],text=True),'upstream_binary_reproduced':False,'original_CentOS_patches_applied':False}
Path('/outputs/build-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'library_sha256':r['library_sha256'],'compiler_inputs':len(captured),'translation_units':len(receipts)}))
PY
