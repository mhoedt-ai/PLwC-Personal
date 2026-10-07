# Replacing NumPy's LGPL libquadmath

NumPy's original wheel contains libquadmath-96973f99-934c22de.so.0.0.0.
Its code, read-only data, unwinding section and build ID match the captured
CentOS libquadmath 4.8.5-44.el7 binary; the corresponding source RPM is retained.
This proof independently modifies and rebuilds its preferred GNU libquadmath
source. It does not reproduce the original CentOS build or apply every CentOS
patch. The original runtime library is unchanged.

Extract gcc-4.8.5-20150702.tar.bz2 from the corresponding source RPM in the
source collection. Verify its SHA-256 against input-manifest.json. Supply it
with build.sh and adjacent native-build/syslimits.h, stdint.h and COPYING.LIB
in a separate input directory. Prepare the disposable GCC 14.2.0-19 tool
environment described by native-build/README.md. Mount inputs read-only at
/inputs, empty output at /outputs and at least 1 GiB executable scratch at
/work. Run sh /inputs/build.sh with no network. No Fortran compiler is needed
for this C library. All retained original source/license notices apply.

The script adds an execution marker to expq and two probe exports to the
original version map. It builds the shared library and captures 107 GCC
translation-unit receipts plus all available actual compiler inputs. Copy
output libquadmath.so.0.0.0 to a private path accessible to a separately
started worker. Mount it read-only over
/usr/local/lib/python3.12/site-packages/numpy.libs/libquadmath-96973f99-934c22de.so.0.0.0.
Start with --network none --read-only --user 10001:10001 --cap-drop ALL
--security-opt no-new-privileges and writable temporary /tmp. Run python with
runtime-probe.py through standard input. Normal NumPy import must have already
loaded the replacement: the probe uses RTLD_NOLOAD, verifies the modified
expq execution and expq(0)==1 at quad precision, then checks NumPy solve and
SVD reconstruction. All checks passed in the frozen V7 worker.

Independently modified libraries have their own hashes and can be used in
a separately started worker without the original signing key. This proof
does not certify every original native compiler input or complete archive
rights. Copyright 2026 Mirco Hoedt. Recipe/instructions/modification:
LGPL-2.1-or-later; see COPYING.LIB. Specific original notices stay in force.
