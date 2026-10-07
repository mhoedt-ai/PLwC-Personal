# PLwC Update Center

PLwC Personal uses one local Update Center shared by the Windows
installation and configuration experience. It is implemented in the Gateway
package rather than the browser bridge, so PLwC installations without the Chat
Bridge can use the same verification rules.

## Release manifest

An accepted manifest must be UTF-8 JSON matching
`config/release-manifest.schema.json`. It contains:

- manifest schema, product version, and installer revision;
- component versions and compatibility ranges;
- publication time and recommended/required classification;
- German and English release notes;
- HTTPS artifact URL, exact byte size, and SHA-256;
- the artifact build identity bound to the same SHA-256;
- one RSA/SHA-256 signature over the canonical JSON representation.

PLwC rejects duplicate JSON members, unknown keys, unsafe artifact names,
non-HTTPS URLs, unknown signing keys, invalid signatures, mismatched hashes, and
unsupported build identities. It verifies the signature before trusting any
artifact metadata.

## Trust and caching

Trusted public release keys are read from `config/release-trust.json`. Private
keys never belong in the repository or installation. The prior r26/r27 public
key is not trusted by the Personal line. The Personal source trust store pins
its own RSA-3072/e65537 public key. Its SPKI SHA-256 fingerprint is
`43b5314e2d46e3ca668fe409a9670582ab8af26c7dc6d4bcca44f3522c7079b8`.
The owner's encrypted private key and recovery copy are held outside the
repository and installation. A signed Personal release manifest bound to the
approved candidate remains required before this update channel can be used.
The Personal configuration also rejects a correctly signed manifest that names
a different product.

Only a signature-verified manifest becomes `last-valid-manifest.json`. A failed
or offline check records its own time and error but cannot replace that valid
cache. Automatic checks are limited to one attempt per six hours; the manual
check remains available. No profile, workspace, prompt, or document content is
sent by the updater, and there is no telemetry.

## Download and installation

The Update Center uses three distinct states:

1. Review a plan containing the immutable plan ID, artifact name, size,
   SHA-256, and build identity.
2. Explicitly confirm the download. A partial, short, oversized, or wrong-hash
   file is rejected and no executable remains.
3. Separately confirm the interactive installer start. PLwC rechecks size,
   SHA-256, and signed build identity immediately before launch.

The updater does not run silently. The installer owns migration, postflight,
failure reporting, and rollback. If it fails, the Update Center surfaces the
matching revision's rollback report under `logs/setup` when present.

## Status meanings

- `update_available`: the live manifest was verified; inspect `update_kind`
  (`recommended` or `required`).
- `offline`: the check failed without a trusted live response; the last valid
  time and cached release remain visible.
- `rejected`: received content failed the manifest or signature contract.
- `never_checked`: no check has completed on this installation.

A missing or empty trust store is fail-closed, not an indication that an
unsigned manifest should be accepted.
