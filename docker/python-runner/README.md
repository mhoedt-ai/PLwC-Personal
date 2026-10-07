# plwc-personal-python-runner

Minimal Python 3.12 image for `plwc_sandbox_run(lang="python")`.

The release build uses the digest-pinned base in `Dockerfile` and publishes the
result as `ghcr.io/mhoedt-ai/plwc-personal-python-runner:0.1.0`. The new digest
is pending. Runtime execution uses the complete digest from the Personal
runtime-image lock, with `--pull never`,
`--network none`, a read-only root, dropped capabilities, no-new-privileges and
UID/GID 65532.

The digest-pinned Python 3.12 Trixie base supplies the fixed OpenSSL 3.5.7
runtime. Both glibc runtime packages are pinned to Debian's fixed
`2.41-12+deb13u4` from the 2026-09-28 snapshot. The incidental Debian
`perl-base` interpreter is removed because it
is not part of the Python sandbox contract.

No package is installed at runtime. User code can import only modules already
present in the fixed image or supplied under the governed workspace mount.
