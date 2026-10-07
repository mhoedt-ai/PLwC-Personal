dnl Copyright (C) 2026 Mirco Hoedt.
dnl Linux build adaptation for the GNU libiconv library.
dnl This file is free software: you may redistribute and modify it under
dnl the GNU Lesser General Public License, version 2.1 or any later version.
dnl It is provided WITHOUT ANY WARRANTY; see the accompanying COPYING.LIB.

AC_DEFUN([AC_EILSEQ], [
  AC_REQUIRE([AC_PROG_CC])
  AC_CHECK_DECLS([EILSEQ], [],
    [AC_MSG_ERROR([This Linux build requires EILSEQ from errno.h.])],
    [[#include <errno.h>]])
  AC_SUBST([EILSEQ], [])
])
