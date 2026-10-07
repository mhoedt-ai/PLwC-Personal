# Pillow 12.3.0 source and replacement notices

The original wheel retains its full mixed-component LICENSE. This supplement
retains the Pillow-authored FriBidi shim LGPL declaration, the full LGPL 2.1
text, matching FreeType 2.14.3 / HarfBuzz 14.2.1 source grants, bundled Raqm,
pythoncapi_compat at its exact referenced commit, and Apache Arrow notices.
Specific individual file grants remain in force. Optional component entries
in the original SBOM do not prove that those binaries are installed.

The LGPL shim is compiled into PIL/_imagingft, not a separate libfribidi.so.
The source-compiled modified module was loaded at Pillow's ordinary path in
the frozen V7 worker. Normal import executed its modified load_fribidi code;
TrueType BASIC rendering and PNG creation passed as uid/gid 10001 with a
read-only filesystem and no network. FriBidi and RAQM were unavailable, as in
the original runtime. This does not waive obligations for compiled shim code.

The corresponding-source collection supplies the exact original Pillow source
and the executed replacement recipe. See pillow-lgpl-replacement/README.md.
All 308 actual recipe compiler inputs have individual hash-bound grants.
This is a modification/replacement proof, not upstream binary reproduction
or a complete original-wheel compiler-input or whole-archive rights review.
The frozen V7 image is unchanged. Next complete candidate binding is pending.
PLwC's own license does not restrict these original component grants.
