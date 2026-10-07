# Rebuilding and replacing GNU libiconv inside lxml

GNU libiconv and libcharset retain LGPL-2.1-or-later rights. The complete
license is included in the adapted source archive and in
`../libiconv-linux/COPYING.LIB`. PLwC's own license does not restrict modifying
these independent libraries or debugging such modifications. Preserve their
copyright and license notices and identify your changes.

These libraries are statically linked into lxml's native modules. Replacing
an unrelated system `libiconv.so` will not replace that implementation. The
supplied preferred lxml source and the other four library sources let you
recompile and relink all seven modules with your modified libiconv.

Follow `README.md` to prepare the six source/build inputs. For a modification,
place your own `libiconv-edit.py` in the input directory. The build recipe runs
it after extraction and before configuring libiconv. It can edit the preferred
files under `/work/src/libiconv-1.18`, preserving the original notices. Baseline
archive hash checks still run before this optional modification. Build in an
independent disposable environment, retaining your changes and build outputs.

Copy each output module to a separate readable directory on your host. Obtain
the complete relative module list from `build-results.json`; do not substitute
the original module files. Add one read-only mount per module to your chosen
worker invocation:

```text
--mount type=bind,src=<absolute-output-path-for-module>,dst=/usr/local/lib/python3.12/site-packages/lxml/<relative-module-path>,readonly
```

For example, the destination for `etree.cpython-312-x86_64-linux-gnu.so` is
`/usr/local/lib/python3.12/site-packages/lxml/etree.cpython-312-x86_64-linux-gnu.so`.
Retain `--network none`, `--read-only`, `--user 10001:10001`, `--cap-drop ALL`,
`--security-opt no-new-privileges` and `PYTHONDONTWRITEBYTECODE=1`. The source
directory and every module must be readable by UID 10001. Use a separate writable
document directory for the worker's inputs and outputs.

Verify the actual loaded path with `--entrypoint python` and
`-c "from lxml import etree; print(etree.__file__)"`. Test the changed library's
behavior through lxml; a path print alone does not prove a modified static
implementation was linked. The private G3 exchange proof rebuilt all seven
modules with a harmless libiconv marker/counter, mounted them at these actual
locations, observed the marker and conversion calls, and exercised five
encodings and the real document worker. The current unmarked source build
passes the retained Schematron and worker tests. The next release candidate
still needs its own artifact binding and acceptance.

Your modified library files remain independently licensed. Official PLwC
signatures do not certify your replacements. No signing key or change to
the installed host worker is required for an independently started container.

Copyright 2026 Mirco Hoedt. Licensed under LGPL-2.1-or-later; see COPYING.LIB.
