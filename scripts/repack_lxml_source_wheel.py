"""Package the reviewed filtered lxml files with seven measured source-built modules."""
from __future__ import annotations
import argparse,base64,csv,hashlib,io,json
from pathlib import Path
import zipfile

FILTERED_INPUT_SHA256='4d128c9f6996bc25c86c547dfae28c8c35e2b997f92909b3d388b3bc7d754382'
RECORD='lxml-6.1.0.dist-info/RECORD'
WHEEL='lxml-6.1.0.dist-info/WHEEL'
NOTICE='lxml-6.1.0.dist-info/licenses/PLWC-PACKAGING-NOTICE.txt'

def repack(source:Path,extensions:Path,results:Path,output:Path)->str:
    data=source.read_bytes()
    if hashlib.sha256(data).hexdigest()!=FILTERED_INPUT_SHA256:
        raise ValueError('Input must be the exact previously reviewed filtered wheel')
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        if len(wheel.namelist())!=len(set(wheel.namelist())):raise ValueError('Duplicate paths')
        files={n:wheel.read(n) for n in wheel.namelist()}
    measured=json.loads(results.read_text(encoding='utf-8'))['extensions']
    native={n for n in files if n.endswith('.so')}
    paths={'lxml/'+r['path'] for r in measured}
    if len(measured)!=7 or paths!=native:raise ValueError('Expected seven exact module paths')
    for row in measured:
        p=Path(row['path'])
        if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe module path')
        b=(extensions/p).read_bytes()
        if hashlib.sha256(b).hexdigest()!=row['sha256'] or len(b)!=row['bytes']:
            raise ValueError('Compiled module identity differs')
        files['lxml/'+row['path']]=b
    files[WHEEL]=b'Wheel-Version: 1.0\nGenerator: PLwC measured source-build packaging\nRoot-Is-Purelib: false\nTag: cp312-cp312-linux_x86_64\n'
    files[NOTICE]=b'''PLwC filtered source-build packaging, 2026-10-05.
The seven native modules were built from the retained lxml 6.1.0 source and
libxml2 2.14.6, libxslt 1.1.43, zlib 1.3.2 and GNU libiconv 1.18.
GNU libiconv uses the supplied LGPL-2.1-or-later Linux EILSEQ build adaptation.
This is a CPython 3.12 Linux x86-64 build for the pinned Debian trixie runtime;
no upstream manylinux compatibility or original upstream binary identity is
claimed. Native source, compiler inputs and the executed recipe are retained.
The unused RNG2Schtrn.xsl and XSD2Schtrn.xsl resources remain excluded.
Their extraction helpers raise NotImplementedError; direct ISO Schematron,
XML Schema and Relax NG validation remain. Other upstream package files and
original notices are unchanged. WHEEL, this packaging notice and RECORD are
updated. Third-party file-specific and LGPL rights remain independent of the
PLwC Core licence. This packaging record is not a whole-package rights approval.
'''
    files.pop(RECORD)
    rows=[]
    for name,b in sorted(files.items()):
        digest=base64.urlsafe_b64encode(hashlib.sha256(b).digest()).rstrip(b'=').decode()
        rows.append((name,'sha256='+digest,str(len(b))))
    rows.append((RECORD,'',''));stream=io.StringIO(newline='');csv.writer(stream,lineterminator='\n').writerows(rows)
    files[RECORD]=stream.getvalue().encode()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_STORED) as wheel:
        for name,b in sorted(files.items()):
            entry=zipfile.ZipInfo(name,(1980,1,1,0,0,0));entry.create_system=3;entry.external_attr=0o100644<<16;wheel.writestr(entry,b)
    return hashlib.sha256(output.read_bytes()).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--extensions',type=Path,required=True)
    parser.add_argument('--build-results',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(repack(args.input,args.extensions,args.build_results,args.output))
