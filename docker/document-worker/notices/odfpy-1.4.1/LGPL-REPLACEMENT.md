# Replacing the independent ODFPy library

ODFPy 1.4.1 retains its file-specific rights. PLwC's own license does not
restrict modification or redistribution of these independent library files,
or debugging modifications to them. Keep their copyright and license notices.
The complete exact source archive supplied with the release has SHA-256
`db766a6e59c5103212f3cc92ec8dd50a0f3a02790233ed0b52148b70d3c438ec`.

The normal import location is
`/usr/local/lib/python3.12/site-packages/odf/`. The library is Python source;
replacing it does not require relinking a native executable. Extract the
release's exact ODFPy source into a separate directory, retain the supplied
license files, and make the desired modifications in its `odf/` directory.
Mount that directory read-only over the import location in your independently
started worker. Disable bytecode writes so stale caches do not select the old
implementation. For example, with your chosen worker image and absolute
source-directory path:

```text
docker run --rm --pull never --network none --read-only --user 10001:10001 \
  --cap-drop ALL --security-opt no-new-privileges \
  --env PYTHONDONTWRITEBYTECODE=1 \
  --mount type=bind,src=<absolute-directory-containing-your-odf-files>,dst=/usr/local/lib/python3.12/site-packages/odf,readonly \
  --entrypoint python <worker-image> -c "import odf; print(odf.__file__)"
```

Adapt line continuation to your shell; `src` names the `odf` directory itself.
The host directory must be readable by UID 10001. Synthetic document outputs
need a separate writable `/work` mount; this leaves the image filesystem
read-only. Preserve the offline and non-root execution limits when testing.

The G3 candidate test mounted the complete exact source at this location with
a harmless marker appended to `odf/__init__.py`. It verified the changed
source hash and actual import path, created an ODT with `OpenDocumentText`,
loaded it again, and successfully inspected the result with the existing
worker. The worker's ODT inspector uses its own XML parser; this last check
establishes compatibility with the replacement output. It does not claim
that the inspector itself calls ODFPy.

This is an independent component modification. Official PLwC release
signatures continue to identify the unmodified official artifacts; they do
not certify your replacement. ODFPy and its embedded artwork/schema retain
their own licenses and attribution requirements.
