# Replacing Pillow's LGPL font shim

The exact recipe was built offline with GCC 14.2.0-19 and Python 3.12.14 on
Debian trixie. Use the disposable tool environment described by the adjacent
native-build/README.md. Obtain Pillow 12.3.0, FreeType 2.14.3 and HarfBuzz
14.2.1 preferred archives from the corresponding-source collection; their
exact names/hashes are in input-manifest.json. Verify every input hash first.

Put those three archives, build.sh, and native-build/syslimits.h, stdint.h and
COPYING.LIB in a separate input directory. In its pillow.libs/ directory place
the original runtime's libfreetype-9fc94c80.so.6.20.6 and
libharfbuzz-172d1f63.so.0.61421.0, or extract them from the original wheel
identified in the manifest. These unchanged external runtime libraries are
not bundled as source files. The manifest binds all 18 original wheel DSOs;
only those two are explicit link arguments. Keep all original notices.

Mount inputs read-only at /inputs, empty writable output at /outputs and at
least 1 GiB executable scratch at /work. Run sh /inputs/build.sh with no
network in the disposable build environment. The script modifies the LGPL
fribidi.c execution marker, compiles three extension translation units plus
the upstream Mode.c support library and links matching original DSOs.
The actual executed input hashes, four GCC dependency receipts, 308 compiler
input files and resulting module hash are retained in the G3 proof.

Start a separate document worker with --network none --read-only,
--user 10001:10001 --cap-drop ALL --security-opt no-new-privileges and writable
temporary /tmp. Mount output _imagingft.cpython-312-x86_64-linux-gnu.so read-only
over /usr/local/lib/python3.12/site-packages/PIL/_imagingft.cpython-312-x86_64-linux-gnu.so.
Run python with runtime-probe.py through standard input. Normal Pillow import
must call the modified shim without directly invoking load_fribidi in the
probe. The exported getter, actual file hash, memory mapping, BASIC font mask
and PNG creation are checked. FreeType reports 2.14.3; the original runtime's
optional FriBidi remains unavailable. No original wheel bit reproduction is
claimed. Independently modified modules have their own hashes; replacing
them in a separately started worker does not require the release signing key.

Copyright 2026 Mirco Hoedt. Recipe and instructions: LGPL-2.1-or-later.
Original files retain their individual grants; see COPYING.LIB and notices.
