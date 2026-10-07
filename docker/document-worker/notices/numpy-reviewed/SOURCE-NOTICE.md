# NumPy 2.2.6 source and native-library notices

The exact original wheel LICENSE, all 29 captured preferred-source notices
and individual copied-source notices are retained. All 1,291 actual V7 files
are hash-bound: 838 source files equal the preferred archive, 411 bytecode
code objects compile identically from actual source, and remaining native or
generated files equal the original publisher wheel or installation generator.
Original generator execution and native compiler identity are not claimed.

The original libgfortran and libquadmath ELF code/data/unwind/build-ID sections
match their captured CentOS libraries, with exact corresponding source RPMs.
Libgfortran has its individual GPL/GCC exception. Libquadmath has LGPL and
specific SunPro/public-domain notices; no blanket GCC exception is applied.
The actual modified libquadmath replacement loads through ordinary NumPy
import and passes quad-precision expq(0), solve and SVD probes. The complete
source and executed recipe are supplied in numpy-lgpl-replacement/README.md.

This is original publisher grant and LGPL replacement evidence. Complete
source archive rights, original native compiler coverage and next complete
runtime binding remain separate. The frozen V7 image is unchanged. PLwC's
own license does not restrict original component grants or lawful replacement.
