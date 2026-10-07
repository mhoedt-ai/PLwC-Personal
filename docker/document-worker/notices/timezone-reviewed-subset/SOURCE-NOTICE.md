# Exact timezone sources, grants and observed rebuild

This supplement covers pytz 2026.2 and tzdata 2026.2 in the frozen v5 document
worker. It preserves the original PyPI source distributions, IANA tzdata and
tzcode 2026b source archives, full grants, exact installed tzdata.zi inputs,
observed compiler package versions and the actually executed recipes.

Combine the two original IANA archives, retaining byte-equal overlapping files.
The observed build used make -j2 zic with GCC in a private Debian environment.
The rebuild script compacts IANA main-form input and executes zic -b fat for
pytz and zic -b slim for tzdata. All 598 files in each family matched the actual
frozen image byte for byte. Complete Rule and Link order and each complete Zone
continuation block were also verified; only independent whole Zone blocks
are sorted for comparison. The package headers remain unchanged.

The compiled zic executable is not part of this source supplement. Its exact
observed hash is bound in the receipt. The wrapper grants are MIT and Apache
2.0 respectively, and the timezone data carries the original IANA public-domain
dedication. IANA's listed BSD exceptions for compiler-source files are retained
in the complete source archives and supporting notice files.

This is an explicit two-package subset, not approval of the whole runtime.
Frozen v5 and the user's original installation remain unchanged. Notice
packaging is prepared for a later candidate and still needs verification.
