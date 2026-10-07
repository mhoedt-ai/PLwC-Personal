# PLwC Document Worker MVP

This directory defines the prepared Docker worker image for future governed
document operations.

Release repository and version label:

```text
ghcr.io/mhoedt-ai/plwc-personal-document-worker:0.1.0
```

This Personal image still requires a new build and digest before release. The
worker is separate from the `plwc-gateway` runtime. It is not a public MCP
server and must be invoked only through PLwC-controlled policy and audit code.

## Runtime Rules

- The gateway must run the worker with `--pull never`.
- The gateway must run the worker with `--network none`.
- The worker must mount the user workspace at `/work`.
- The worker must not assume `/workspace`.
- The worker must not run `pip install` at runtime.
- The r27 installer may acquire the manifest-locked GHCR digest only after the
  user explicitly opts in. Gateway execution never pulls an image.
- Generated artifacts must remain under `/work`.
- The digest-pinned Python 3.12 Trixie base supplies the fixed OpenSSL runtime.
  Both glibc runtime packages are pinned to Debian's fixed
  `2.41-12+deb13u4` from the 2026-09-28 snapshot. Incidental `perl-base` is
  removed because Perl is not part of the worker contract.
- `shared-mime-info` generates the MIME database in a separate build stage.
  The runtime image retains the generated database and its copyright notice.
  The legacy GDK-PixBuf package and its mandatory `shared-mime-info`/system
  `libxml2` dependencies are absent. Current PDF creation uses ReportLab.
  WeasyPrint and Pango are omitted because HTML-to-PDF is not implemented;
  their GLib/GIO runtime dependency is absent as well. The governed probe checks
  these boundaries before the image can be used as release evidence.
- PDF regression note: If later PDF tests fail, check the WeasyPrint/Pango/GLib
  removal first. Existing ReportLab-based PDF creation and pypdf operations
  must pass their acceptance tests. Adding HTML/CSS-to-PDF in the future
  requires a separate dependency and security review.
- Pillow retains TIFF support without Debian's `libtiff6` package. The governed
  probe checks TIFF availability and fails if the vulnerable `tiffcrop` tool is
  present. Fresh scan evidence for the final image is still required.
- The vendored `odfpy==1.4.1` wheel omits upstream license files. The image
  includes its SHA-256-verified source distribution's Apache and GPL texts and
  README under `/usr/share/doc/odfpy/`, together with Debian's LGPL 2.1 text
  and a source notice. Some installed files carry LGPL and OASIS notices;
  these file-level terms remain subject to the release license review.

## Offline Wheelhouse Build Strategy

Release-quality builds consume the committed lock and verified hashes without
re-resolving dependencies:

```powershell
python scripts\build_document_worker_wheelhouse.py --clean --download
```

This command downloads only the exact files recorded in
`wheelhouse-manifest.json`, verifies every hash and copies the deterministic,
vendored `odfpy==1.4.1` wheel. It never rewrites the lock or manifests.
Trixie supports the recorded `manylinux_2_28_x86_64` wheels as well as the
older `manylinux2014_x86_64` wheels retained by unchanged dependencies.

A dependency refresh is a separate, deliberate maintainer operation:

```powershell
python scripts\refresh_document_worker_wheelhouse_lock.py --accept-mutable-resolution
```

That command preserves compatible transitive pins from the previous lock,
resolves the explicitly pinned direct requirements, then rewrites
`requirements-doc-worker.lock` and both wheelhouse manifests. The resulting
diff and all worker tests must be reviewed before commit. CI never performs
this mutable refresh.

The wheel files are local build artifacts under `docker/document-worker/wheelhouse/`
and are intentionally ignored by Git.

After the wheelhouse is present:

```powershell
python scripts/build_runtime_images.py
```

Release digests are never documented as mutable README values. They are frozen
in the generated, installer-hashed `runtime-images.json` after reproducibility,
security-evidence and GHCR staging gates pass. Build-time internet is used for
wheelhouse preparation and the pinned Debian snapshot. Runtime execution remains
offline and uses `--pull never` plus `--network none`.

## MVP Commands

Inside the worker image:

```text
python -m plwc_document_worker probe
python -m plwc_document_worker create-docx --output /work/example.docx
python -m plwc_document_worker create-xlsx --output /work/example.xlsx
python -m plwc_document_worker create-pptx --output /work/example.pptx
python -m plwc_document_worker create-pdf --output /work/example.pdf
python -m plwc_document_worker inspect-zip --input /work/example.zip
python -m plwc_document_worker extract-zip --input /work/example.zip --output-dir /work/extracted
python -m plwc_document_worker create-zip --inputs-json "[\"/work/project\"]" --output /work/project.zip
```

These commands are worker-level smoke commands. Public access remains only
through `plwc_document_operation`; the worker is not a public MCP server.
Conversion, LibreOffice, Pandoc, non-ZIP archive formats, encrypted/password
ZIPs, nested archive extraction and delete are not implemented in this MVP.

## Verification

```powershell
docker run --rm --pull never --network none <repository>@sha256:<approved-digest> probe
python -m pytest tests\integration\test_document_worker_mvp.py -q -rs
```

Expected current result:

```text
22 passed
```
