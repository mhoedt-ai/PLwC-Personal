# odfpy 1.4.1 upstream notices

The `odfpy-1.4.1` source distribution on PyPI has SHA-256
`db766a6e59c5103212f3cc92ec8dd50a0f3a02790233ed0b52148b70d3c438ec`.
`README.md`, `APACHE-LICENSE-2.0.txt`, and `GPL-LICENSE-2.txt` in this directory
are byte-for-byte copies from that source distribution. The runtime image
also copies Debian's `/usr/share/common-licenses/LGPL-2.1` here as
`LGPL-2.1.txt`.

The upstream README describes an Apache-2.0 or GPL-2.0-or-later choice for
the project except OpenDocument schemas. Some installed source files, such as
`odf/element.py` and `odf/grammar.py`, carry LGPL-2.1-or-later headers;
`odf/grammar.py` contains the OASIS schema notice. These file-level notices
remain in the installed Python files. The package metadata alone does not
describe this distinction. `FILE-LICENSES.json` records the reviewed grants
for the 34 Python source modules and 11 installed standalone scripts.
The Apache alternative is selected only where that file explicitly offers
it. `odf/easyliststyle.py` and `odf/teletype.py` retain GPL-2.0-or-later;
the LGPL library files retain their independent LGPL rights.

`odf/thumbnail.py` embeds an unmodified LibreOffice icon with an explicit
CC-BY-SA-3.0 notice. Its exact upstream attribution is reproduced in
`THUMBNAIL-NOTICE.txt`; the complete license is `CC-BY-SA-3.0.txt`, copied
from Creative Commons' official legal text, SHA-256
`3f941b3b89cf7b8370ceb83cc76d2120d471b58735d8ca60238a751a48d7f72f`.
The complete generated-schema notice from `odf/grammar.py` is also readable
in `OASIS-ODF-1.2-NOTICE.txt`. `odf/element.py` preserves the additional
notice for copied Python `xml.dom.minidom` code; the full installed Python
license remains at `/usr/local/lib/python3.12/LICENSE.txt`.

The installed modules match the exact source distribution byte for byte.
The eleven standalone scripts preserve the complete code and notice bodies;
the vendored wheel changes their line endings and installation selects
`#!/usr/local/bin/python`. These transformations and the actual file hashes
are recorded in the candidate's corresponding-source review.
`LGPL-REPLACEMENT.md` describes an independent library replacement. Compiled
bytecode retains the rights of its corresponding source file.

PLwC's own license does not relicense or restrict these third-party files.
This package-specific review does not replace review of the other runtime
components or the final candidate's complete notice/source archives.

Source: https://pypi.org/project/odfpy/1.4.1/
Upstream repository: https://github.com/eea/odfpy
