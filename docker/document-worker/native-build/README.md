# Building the retained lxml native modules

This recipe builds lxml 6.1.0 with libxml2 2.14.6, libxslt 1.1.43,
zlib 1.3.2 and the supplied adapted GNU libiconv 1.18 source. It uses the
generated C files retained in the filtered lxml source, without Cython.
The supported target is CPython 3.12.14 on Linux x86-64, Debian trixie.
The result is not an upstream manylinux binary.

`input-manifest.json` names and hashes the six exact inputs. Obtain the five
library source archives from the corresponding-source collection, retaining
their original names in a separate input directory. The sixth input is the
unmodified external Setuptools 70.3.0 build-tool wheel. Download it during tool
preparation from the manifest's `url`; its size and SHA-256 are checked before
installation. The collection contains Setuptools's preferred source archive,
but does not bundle this build-tool wheel. Copy `build.sh`, the manifest, `syslimits.h`, `stdint.h` and `COPYING.LIB`
into that directory. The manifest checks the three routing/license inputs too. The adapted libiconv archive already includes its preferred
macro and regenerated configure script. The excluded upstream EILSEQ macro
is not needed. Keep all copyright, license and modification notices.

Prepare a disposable Linux build environment with Python 3.12.14 and the
versions checked at the beginning of `build.sh`. The measured compiler is
GCC 14.2.0-19, libc6-dev 2.41-12+deb13u4, binutils 2.44-3, make 4.4.1-2 and
pkg-config 1.8.1-4. Debian packages were obtained from the runtime's locked
20260928 snapshot repositories. Tool installation is a separate step; the
build recipe itself makes no network requests. Setuptools 70.3.0 is installed
from the separately prepared wheel with `--no-index --no-deps`.

Mount the input directory read-only at `/inputs`, an empty writable scratch
directory at `/work`, and an empty output directory at `/outputs`. Run
`sh /inputs/build.sh` with no network. The fixed `/work` path preserves the
measured include and link commands. Budget at least 1 GiB of scratch space
and 3 GiB of memory. Do not run this recipe inside an installed PLwC worker.

`/outputs/extensions` contains all seven native modules, with paths relative
to the installed `lxml` directory. `build-results.json` records their hashes,
sizes, ELF dependencies and installed build packages. The output also retains
the static library archives, actual GCC `-MD` dependency receipts and the
available source/header inputs. The recipe records the member names of all six static libraries. The five
removed configure-test files produce conftest/ztest objects which are absent
from those archives; their generated sources are not inputs to the shipped
modules. This is not a claim of complete assembler or linker input coverage.

The source-built modules can be loaded with the separate mounts described in
`LGPL-REPLACEMENT.md`. That procedure does not require the original native
wheel, a release signature or a proprietary linker. Official release hashes
identify the official artifact; independently modified modules have new hashes.

The source inputs and this recipe are prepared G3 evidence. The complete
source-archive rights review and binding to the next complete candidate remain
open. A successful build alone does not mark those reviews complete.

The compiler-header view copies the installed GCC 14 headers unchanged, then
uses the supplied two LGPL-2.1-or-later hosted-Linux routing headers for the
system limits/stdint interfaces. Original GCC wrappers without individual
runtime exceptions are not used in the native compilation. Direct exceptions
on other copied GCC headers remain intact. All 312 actually read routing/system
headers have hash-bound grants; the additional stdckdint header is byte-equal to
the exact original GCC 14.2.0 preferred source. This header routing produced
all seven native modules byte-equal to the preceding accepted source build.

Copyright 2026 Mirco Hoedt. This build and replacement documentation is
licensed under LGPL-2.1-or-later; see COPYING.LIB.
