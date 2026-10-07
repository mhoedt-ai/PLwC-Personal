#!/bin/sh
# PLwC LGPL replacement demonstration. Copyright 2026 Mirco Hoedt.
# Recipe and demonstration modifications: LGPL-2.1-or-later; see COPYING.LIB.
set -eu
python - <<'PY'
import pathlib,tarfile,shutil,subprocess,hashlib,json
root=pathlib.Path('/work');assert not any(root.iterdir())
assert subprocess.check_output(['gcc','-dumpfullversion'],text=True).strip()=='14.2.0'
for name in ['pillow-12.3.0.tar.gz','freetype-2.14.3.tar.gz','harfbuzz-14.2.1.tar.gz']:
 with tarfile.open('/inputs/'+name) as t:t.extractall(root,filter='data')
original=pathlib.Path(subprocess.check_output(['gcc','-print-file-name=include'],text=True).strip());view=root/'compiler-headers';shutil.copytree(original,view)
for name in ['syslimits.h','stdint.h']:shutil.copyfile('/inputs/'+name,view/name)
source=root/'pillow-12.3.0/src/thirdparty/fribidi-shim/fribidi.c';data=source.read_bytes()
assert hashlib.sha256(data).hexdigest()=='7e8cfa78dcd21cebeb0ad91c0cd23e0dba6496c0fbd66e1ec3d25c5b1b365d11'
modified=data.replace(b'int load_fribidi(void) {',b'static int plwc_g3_modified_shim_called = 0;\nint load_fribidi(void) {\n    plwc_g3_modified_shim_called = 1;')
assert modified!=data
modified+=b'\n/* PLwC demonstration modification, 2026 Mirco Hoedt; LGPL-2.1-or-later. */\nconst char *plwc_g3_modified_shim_marker(void) { return plwc_g3_modified_shim_called ? "PLwC modified LGPL shim executed" : "not called"; }\n'
source.write_bytes(modified);pathlib.Path('/outputs/modified-fribidi.c').write_bytes(modified)
pathlib.Path('/outputs/source-modification.json').write_text(json.dumps({'original_sha256':hashlib.sha256(data).hexdigest(),'modified_sha256':hashlib.sha256(modified).hexdigest(),'change':'Execution marker in load_fribidi, with an exported read-only getter; original dynamic loading behavior unchanged.','license':'LGPL-2.1-or-later'},indent=2)+'\n')
PY
cd /work/pillow-12.3.0
for unit in src/_imagingft.c src/thirdparty/raqm/raqm.c src/thirdparty/fribidi-shim/fribidi.c src/libImaging/Mode.c; do
 stem=$(basename "$unit" .c)
 gcc -O1 -g0 -fPIC -MD -MF "/outputs/$stem.d" -DHAVE_RAQM -isystem /work/compiler-headers -I/usr/local/include/python3.12 -Isrc -I/work/freetype-VER-2-14-3/include -I/work/harfbuzz-14.2.1/src -c "$unit" -o "/outputs/$stem.o"
done
gcc -shared /outputs/_imagingft.o /outputs/raqm.o /outputs/fribidi.o /outputs/Mode.o /inputs/pillow.libs/libfreetype-9fc94c80.so.6.20.6 /inputs/pillow.libs/libharfbuzz-172d1f63.so.0.61421.0 -ldl -Wl,-rpath,/usr/local/lib/python3.12/site-packages/pillow.libs -o /outputs/_imagingft.cpython-312-x86_64-linux-gnu.so
python - <<'PY'
import pathlib,json,hashlib,subprocess
root=pathlib.Path('/work');base=root/'pillow-12.3.0';captured={};receipts=[]
for p in sorted(pathlib.Path('/outputs').glob('*.d')):
 data=p.read_text();tokens=data.replace(chr(92)+chr(10),' ').split(':',1)[1].split();paths=[]
 for token in tokens:
  original=pathlib.Path(token);source=original if original.is_absolute() else base/original;source=source.resolve();assert source.is_file(),token
  category='preferred_or_modified_source' if source.is_relative_to(root) else 'system_or_python_header'
  relative=source.relative_to(root).as_posix() if source.is_relative_to(root) else source.as_posix().lstrip('/')
  b=source.read_bytes();key=category+'/'+relative;dest=pathlib.Path('/outputs/compiler-inputs')/key;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
  row={'path':key,'compiler_path':str(source),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
  if key in captured:assert captured[key]==row
  captured[key]=row;paths.append(key)
 receipts.append({'dependency_file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_paths':paths})
extension=pathlib.Path('/outputs/_imagingft.cpython-312-x86_64-linux-gnu.so')
result={'compiler':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],'compiler_inputs':list(captured.values()),'dependency_receipts':receipts,'extension_sha256':hashlib.sha256(extension.read_bytes()).hexdigest(),'extension_bytes':extension.stat().st_size,'ELF_dynamic_entries':subprocess.check_output(['readelf','-d',str(extension)],text=True),'all_original_native_compiler_inputs_identified':False,'upstream_binary_reproduction_claimed':False}
pathlib.Path('/outputs/build-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'extension_sha256':result['extension_sha256'],'actual_compiler_inputs':len(captured),'actual_translation_units':len(receipts)}))
PY
