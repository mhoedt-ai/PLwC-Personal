# Vendored Document Worker wheels

`odfpy` 1.4.1 is the only locked Document Worker dependency for which PyPI
does not publish a universal wheel. The repository therefore carries the small
pure-Python wheel consumed by the offline image build.

- upstream sdist: `odfpy-1.4.1.tar.gz`
- upstream PyPI SHA-256:
  `db766a6e59c5103212f3cc92ec8dd50a0f3a02790233ed0b52148b70d3c438ec`
- deterministic wheel SHA-256:
  `47943c88ca1ce11e2dd37f3629752680f4332f381b695c3cc1fbbdd322fae313`
- build environment used for the recorded wheel: Python 3.12,
  `SOURCE_DATE_EPOCH=0`, pip 26.1.2, setuptools 82.0.1
- actual grants: Apache-2.0, LGPL-2.1-or-later, GPL-2.0-or-later and
  file-specific Python/OASIS/thumbnail notices. Complete reviewed notices and
  the replacement instructions are in `../notices/odfpy-1.4.1/`; the upstream
  wheel metadata alone does not cover every installed file.

## ReportLab 4.2.2 font packaging

The second vendored wheel retains ReportLab's original Python code, standard
font metrics and the Vera, DarkGarden and Callig15 assets. It removes only
16 legacy Adobe/Monotype Type 1 font programs for which the G3 review did not
establish a separate redistribution grant. This is a packaging decision;
no inference of illegality is made from the absence of an established grant.

- exact upstream PyPI wheel SHA-256:
  `927616931637e2f13e2ee3b3b6316d7a07803170e258621cff7d138bde17fbb5`
- filtered portable wheel SHA-256:
  `57ab146c68055b9e67f9cd4fc1b76b99e80af85e18a80c5ebbcf953d69554a40`
- reproducible recipe: `scripts/repack_reportlab_wheel.py` with the exact
  upstream wheel as `--input` and a new wheel path as `--output`.
- retained files are byte-for-byte original; the wheel's `RECORD` is
  recomputed and `PLWC-PACKAGING-NOTICE.txt` records the exact exclusions.
- fixed ZIP entry order, timestamp, mode and uncompressed storage avoid
  platform-dependent recompression. The recipe requires no package installs.

An isolated runtime probe passed the seven unchanged Document Worker tests,
all fourteen PDF standard fonts and PDF text extraction, four Vera fonts,
and DarkGarden/Callig15 Type 1 embedding. The portable wheel contains the
same logical payload as that tested wheel. A new complete candidate still
needs its own artifact-bound verification. The existing installation and
frozen v5 images are unchanged.

ReportLab's BSD grant does not replace the retained fonts' independent
Bitstream, GPL plus embedding exception, and Callig15 grants. Their complete
notices and DarkGarden's preferred `.sfd` source are retained.

The normal CI download path never rebuilds this wheel. It verifies the
versioned SHA-256 and copies it into the ignored build wheelhouse. Updating it
requires an explicit dependency-lock review.

## chardet 7.4.3: official pure Python wheel

The unmodified upstream `chardet-7.4.3-py3-none-any.whl` is retained with
SHA-256 `1173b74051570cf08099d7429d92e4882d375ad4217f92a6e5240ccfb26f231e`.
It uses the upstream 0BSD grant and retains its complete original LICENSE.
All 25 Python modules are byte equal to the SHA-256-verified 7.4.3 source
distribution (`cc1d4eb92a4ec1c2df3b490836ffa46922e599d34ce0bb75cf41fd2bf6303d56`).
This replaces the upstream compiled wheel at the same package version; the
pure wheel contains no native extensions. The expired upstream build logs
did not establish the exact mypyc compiler/runtime identity of the old wheel.

Isolated comparison on 2026-10-04: 540 unchanged selected upstream tests pass
in each variant, seven document-worker tests pass, and 64 synthetic inputs
produce identical results through four detection APIs. Synthetic medians
for about 128 KiB were 4.5–21.7 ms for the pure wheel and 0.4–9.6 ms for the
compiled wheel. These measurements are not a performance or equivalence
guarantee for every input. No package API, package version, or PLwC policy
was changed. Frozen v5 and the existing installation were not changed.
A fresh candidate build must bind the new image and verify that old native
chardet bytes are absent from every distributed layer.

Retrieve the exact wheel from the versioned PyPI JSON metadata and verify
its SHA-256 before use. Explicit lock refreshes preserve this wheel instead
of selecting the platform-specific compiled wheel.

## lxml 6.1.0: current Linux source build

The current vendored wheel is `lxml-6.1.0-cp312-cp312-linux_x86_64.whl`,
SHA-256 `e258ff2edd61d72d1e0c746dbe2c53ee4b9f874d66eb83cbbca0c6b643eefe7e`.
All seven native modules are compiled from the retained filtered lxml source
and exact native libraries, with the LGPL GNU libiconv Linux EILSEQ adaptation.
The private replacement-test marker is absent. The Linux tag states the
actual CPython 3.12 Debian trixie target; upstream manylinux compatibility is
not claimed. The two excluded resources and disabled helpers remain excluded.

Two source-wheel package reproductions are byte-identical. Actual acceptance
passes all 23 retained Schematron tests, seven document tests, five encodings
with ten conversion calls, XPath, XSLT, objectify and HTML. The explicit
packaging recipe is `scripts/repack_lxml_source_wheel.py`; the source rebuild
and its complete inputs are recorded separately in G3 evidence. The normal
offline wheelhouse and immutable lock bind this wheel. Full runtime/file
rights review and a complete new candidate remain required.

## Initial filtered wheel: historical source evidence

The current PLwC Document Worker and its runtime dependencies do not call the
embedded-Schematron extraction helpers. Following the owner's conditional
approval on 2026-10-04 and the actual usage review, this vendored wheel excludes
`RNG2Schtrn.xsl` and `XSD2Schtrn.xsl`, whose redistribution grants were not
established. No inference of illegality is made. The exact module is patched
to make those two helper calls fail explicitly instead of breaking imports.

- package version and seven native extensions remain unchanged: lxml 6.1.0
- exact upstream wheel SHA-256:
  `bc783ee3147e60a25aa0445ea82b3e8aabb83b240f2b95d32cb75587ff781814`
- portable filtered wheel SHA-256:
  `4d128c9f6996bc25c86c547dfae28c8c35e2b997f92909b3d388b3bc7d754382`
- reproducible recipe: `scripts/repack_lxml_wheel.py`, exact upstream wheel
  as `--input`, new wheel path as `--output`; two runs produced identical bytes
- all original entries except the two excluded resources, initialization module
  and recomputed RECORD are byte equal; the packaging notice records the change
- native XML Schema/Relax NG validation, XML/XPath/XSLT, standalone ISO
  Schematron validation and current PLwC document operations are retained

The exact portable wheel, combined with the prepared chardet and ReportLab
wheels, passes 23 unchanged retained Schematron tests and all seven unchanged
Document Worker tests without failures or skips. The two embedded-extraction
Upstream tests are outside the owner-approved scope. The small initialization
modification preserves the module's BSD-3-Clause grant. Native GNU and other
file-specific grants are separate; this is not a blanket BSD package approval.

This earlier wheel is retained as private historical source evidence.
The existing installation and frozen v5 images remain unchanged. The upcoming
complete candidate requires new artifact-bound source/rights/security checks;
the old resources must be absent from every distributed layer and source bundle.
