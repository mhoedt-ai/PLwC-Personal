# pip 25.0.1 and bundled libraries

PIP-SUPPLEMENTAL-NOTICES.txt retains original full vendor notices, additional
copied-file grants, Unicode notices and the complete MPL 2.0 text. Original
license files and inline copyrights remain inside pip as well.

The exact verified pip source archive has SHA-256 `88f96547ea48b940a3a385494e181e29fb8637898f88d88737c5049780f196ea`.
Its complete pip source subtree is byte equal to the upstream Git commit
`bc7c88cb3de9c9af769c51517833ea48bbe70d9a`. The private G3 review retains the 18 original pinned vendor source
archives, `vendor.txt`, the complete vendoring configuration and six upstream
patches. This is a byte correspondence check; no independent signature check
or complete re-execution of upstream vendoring is claimed.

Independent grants include MIT, Apache-2.0, BSD, ISC, the complete Python
licence stack, Unicode and MPL 2.0. Packaging's original BSD/Apache alternative
is retained and its copied MIT licence parser keeps its own notice. The exact
distlib launcher source has an independent Vinay Sajip BSD-2-Clause notice.
This does not establish all linked-runtime rights of its six Windows binaries.

The next Linux candidate excludes those six Windows binaries from installed
pip and the bundled ensurepip wheel using the exact-hash guarded portable
recipe `docker/filter-linux-pip.py`. Remaining upstream code and original
notices stay unchanged; RECORD and a packaging-change notice are updated.
Original unfiltered archives remain private evidence. The final sources must
use the corresponding filtered pip tree and must not include these binaries.

certifi's modified Python source and editable PEM bundle are retained in the
exact pip source. Their Source Code Form and original notices must accompany
distribution under MPL 2.0. PLwC's licence does not restrict those files' own
rights. A final corresponding-source archive must bind the actual image.

This preparation preserves complete texts. Full filewise grants, copied-code
origin review, binary/toolchain provenance, exact-source and image binding
remain G3 release prerequisites. The whole pip package and runtime are not
approved by this notice file. Existing installations and frozen v5 are intact.
