"""Inventory license locations in the actual final runtime, without network access."""
import importlib.metadata
import json
import subprocess
from pathlib import Path

root=Path('/usr/share/doc/plwc')
root.mkdir(parents=True,exist_ok=True)
packages=[]
output=subprocess.check_output(['dpkg-query','-W','-f=${Package}\t${Version}\n'],text=True)
for line in output.splitlines():
    name,version=line.split('\t',1)
    copyright=Path('/usr/share/doc')/name/'copyright'
    packages.append({'ecosystem':'debian','name':name,'version':version,
        'license_path':str(copyright) if copyright.is_file() else None})
for dist in importlib.metadata.distributions():
    licenses=[str(dist.locate_file(p)) for p in dist.files or []
        if 'license' in str(p).casefold() or 'copying' in str(p).casefold() or 'notice' in str(p).casefold()]
    packages.append({'ecosystem':'python','name':dist.metadata['Name'],'version':dist.version,
        'license_paths':licenses,'declared_license':dist.metadata.get('License-Expression') or dist.metadata.get('License')})
if Path('/usr/local/bin/node').exists():
    packages.append({'ecosystem':'node-runtime','name':'node','version':subprocess.check_output(['node','--version'],text=True).strip(),
        'license_paths':[str(p) for p in [Path('/usr/local/LICENSE'),Path('/usr/local/share/doc/node/LICENSE') ] if p.is_file()]})
supplement=Path('/usr/share/doc/plwc-python-notices/PYTHON-PACKAGE-SUPPLEMENTAL-NOTICES.txt')
if supplement.is_file():
    packages.append({'ecosystem':'python-notice-supplement','name':'reviewed Python package subset',
        'version':'1.0.0','license_paths':[str(supplement),'/usr/share/doc/plwc-python-notices/SOURCE-NOTICE.md']})
generator_notice=Path('/usr/share/doc/debian-generator')
if (generator_notice/'DEBUERREOTYPE-LICENSE-MIT.txt').is_file():
    packages.append({'ecosystem':'base-generator-notice','name':'debuerreotype and copied Docker material',
        'version':'0.17','license_paths':[str(generator_notice/name) for name in
        ('DEBUERREOTYPE-LICENSE-MIT.txt','DOCKER-LICENSE-APACHE-2.0.txt','DOCKER-NOTICE.txt','SOURCE-NOTICE.md')]})
timezone_notice=Path('/usr/share/doc/plwc-timezone-notices/TIMEZONE-SUPPLEMENTAL-NOTICES.txt')
if timezone_notice.is_file():
    packages.append({'ecosystem':'timezone-notice-supplement','name':'pytz and tzdata with original IANA data',
        'version':'2026.2','license_paths':[str(timezone_notice),'/usr/share/doc/plwc-timezone-notices/SOURCE-NOTICE.md']})
reportlab_notice=Path('/usr/share/doc/plwc-reportlab-notices/REPORTLAB-SUPPLEMENTAL-NOTICES.txt')
if reportlab_notice.is_file():
    packages.append({'ecosystem':'reportlab-notice-supplement','name':'ReportLab with independent barcode, glyph and font notices',
        'version':'4.2.2','license_paths':[str(reportlab_notice),'/usr/share/doc/plwc-reportlab-notices/SOURCE-NOTICE.md']})
pip_notice=Path('/usr/share/doc/plwc-pip-notices/PIP-SUPPLEMENTAL-NOTICES.txt')
if pip_notice.is_file():
    packages.append({'ecosystem':'pip-notice-supplement','name':'pip with exact vendored and copied-component notices',
        'version':'25.0.1','license_paths':[str(pip_notice),'/usr/share/doc/plwc-pip-notices/SOURCE-NOTICE.md']})
packages.sort(key=lambda p:(p['ecosystem'],p['name']))
(root/'runtime-license-locations.json').write_text(json.dumps({'schema_version':'1.0.0','packages':packages,
    'review_status':'requires_exact_artifact_license_and_corresponding_source_review'},indent=2)+'\n')
(root/'THIRD_PARTY_NOTICES.txt').write_text('Third-party components retain their independent rights.\n'
    'Exact package versions and installed notice locations: runtime-license-locations.json.\n'
    'Debian license texts: /usr/share/doc/<package>/copyright and /usr/share/common-licenses/.\n'
    'Python license texts remain beside their installed distributions; odfpy notices: /usr/share/doc/odfpy/.\n'
    'Additional complete Python/copied-file notices, when present: /usr/share/doc/plwc-python-notices/.\n'
    'Complete timezone package and IANA notices, when present: /usr/share/doc/plwc-timezone-notices/.\n'
    'Complete ReportLab/copied-code/font notices, when present: /usr/share/doc/plwc-reportlab-notices/.\n'
    'Complete pip/vendor/copied-component notices, when present: /usr/share/doc/plwc-pip-notices/.\n'
    'The official release supplies the reviewed complete notice and corresponding-source archives.\n'
    'This machine inventory alone does not establish redistribution permission.\n')
