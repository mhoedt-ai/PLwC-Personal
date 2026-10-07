# Debian base generator notices

The actual Debian slim bases report debuerreotype 0.17. Their manifest and
configuration bytes match the official docker-debian-artifacts commits:

- Python/document bases: bae6d64d90b4068b09ff9d8b564c2773ef5d8d83 (2026-08-24).
- Node base: 8f962b15d7884a90e17876a9303cbac909d119aa (2026-09-18).

The reported 0.17 release source is pinned to debuerreotype commit
308cd89b8f84045d51f7e7f78d9e7ee98c1ab92a. Six actual installed generated
configuration files match its emitted source literals byte for byte. This
does not claim an independently rebuilt Debian base or a cryptographic
attestation of the generator's complete upstream build working tree.

debuerreotype's MIT notice is retained in full. Its minimizing-config script
identifies copied Docker mkimage material at commit
d6f4fe9e38b60f63e429fff7ffced9c26cbf8236. That original Apache-2.0 LICENSE and
NOTICE are also retained in full; copied Docker material is not assigned a
blanket MIT license. The generator adapts the old mkimage recipe as recorded
in the pinned source. PLwC makes no changes to these six emitted files.

Sources:
https://github.com/debuerreotype/debuerreotype/tree/308cd89b8f84045d51f7e7f78d9e7ee98c1ab92a
https://github.com/moby/moby/tree/d6f4fe9e38b60f63e429fff7ffced9c26cbf8236/contrib/mkimage

Third-party rights remain independent. This notice does not establish the
complete Debian package or runtime license inventory.
