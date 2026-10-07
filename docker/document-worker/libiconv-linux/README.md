# GNU libiconv Linux build adaptation

The private source review did not establish an individual redistribution
grant for the upstream `m4/eilseq.m4`. This replacement uses Autoconf's
standard declaration check to require the POSIX `EILSEQ` constant from
`errno.h` on the supported Linux build target. It does not copy the upstream
macro's fallback implementation for historical non-POSIX systems.

The adaptation is part of the GNU libiconv source build and is explicitly
LGPL-2.1-or-later, preserving the library's independent modification and
redistribution rights. The complete LGPL 2.1 text is copied unchanged from
the exact libiconv source to `COPYING.LIB`. This narrow third-party build
adaptation does not change the licence of PLwC Core.

Replace `m4/eilseq.m4`, regenerate `configure` with Autoconf 2.72 and retain
the actual trace, all preferred inputs and the complete executed recipe.
The original unfiltered archive remains private. A new source bundle must
carry the adapted tree and generated configure script, excluding the
unapproved original macro. Production adoption requires the actual native
rebuild and its functional acceptance; this directory alone is not approval.
