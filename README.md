# PLwC Personal 1.0.0

**Controlled local access for AI assistants, persistent profiles and governed changes.**

PLwC lets compatible AI assistants read and organise allowed local files, create and read documents, and run Python or Node.js in isolated Docker environments under locally configured rules. Persistent profiles retain preferences and working context across sessions and compatible clients. The Governor separates proposed lasting profile changes from their explicitly confirmed application.

PLwC provides the local gateway and tools; you choose the AI client and model. Requests and returned contents can still be processed by an external AI provider.

## Downloads and documentation

- [Official release: Windows setup, checksums, sources and browser packages](https://github.com/mhoedt-ai/PLwC-Personal/releases/tag/v1.0.0)
- [Full software description in German: 65 pages, 22 diagrams](https://github.com/mhoedt-ai/PLwC-Personal/releases/download/v1.0.0/PLwC-Personal-1.0.0-Programm-und-Softwarebeschreibung-DE.pdf)
- [Full software description in English: 62 pages, 22 diagrams](https://github.com/mhoedt-ai/PLwC-Personal/releases/download/v1.0.0/PLwC-Personal-1.0.0-Program-and-Software-Description-EN.pdf)
- [Website and installation guidance](https://www.plwc.de/)

PLwC Personal and its gateway use version **1.0.0**. The browser extension, **PLwC Personal Chat Bridge**, uses version **2.0.0** for Chrome and Edge; its store publication is separate. The bridge protocol is **1.0.0**.

## What is included

- A bilingual Windows installer with the gateway, configuration and selectable client integrations.
- Bounded workspace file and directory operations.
- DOCX, XLSX, PPTX, PDF and ZIP operations through the document worker.
- Separate Docker runtimes for documents, Python and Node.js. Sandbox execution has no network access and no automatic host-shell fallback.
- Local profiles, Compile, Reflection, memory and Governor Plan/Apply workflows.
- A local Chat Bridge for ChatGPT in supported browsers; native STDIO integration for compatible MCP clients.

The gateway exposes exactly eight tools: `plwc_status`, `plwc_describe`, `plwc_profile`, `plwc_reflection`, `plwc_governor`, `plwc_sandbox_run`, `plwc_workspace_operation` and `plwc_document_operation`.

## Installation and integrity

Use Windows 11 x64. Python is required for the gateway; Node.js is additionally required for the Chat Bridge. Docker Desktop with Linux containers and WSL 2 is required for document and sandbox operations. The installer checks prerequisites and asks before optional runtime downloads.

Without available Docker runtimes, profile and workspace functions remain usable in Safe Mode; document and sandbox operations are unavailable.

The official installer is `PLwC-Setup-1.0.0-installer-r27.exe`, SHA-256:

`aa1650fd560b73d0920ce6a4f070f290602cafe271b35e6b6314fa3af25ffe23`

**The EXE has no Windows Authenticode signature (`NotSigned`).** Its release manifest has an independently verified RSA signature. The release includes the signed manifest, the public trust anchor, the final runtime lock and `SHA256SUMS.txt`.

The unchanged V9 runtime digests are:

| Runtime | GHCR digest |
| --- | --- |
| Document worker | `sha256:cab60f93f65a1a5827b03757b59b8d026826bee0e4ca1e5a60d014d70d294064` |
| Node.js runner | `sha256:d190b3e3f160be8f3aaf69d14b6b99f558fd66bff869d423c6e4aedc74cdd6f8` |
| Python runner | `sha256:51d0bf8c0d6d1b4fc22a1f69d5b0ccd97369091f2654d17ce6d33b206f621a17` |

## Sources, licenses and support

The release sources are bound to commit `0c1c367c00bb7f5bb265d129f4daa7b73167b313` and tag `v1.0.0`. Changes to this README do not alter that release tag or its runtime/installer artifacts.

[Corresponding GPL/LGPL sources, image mapping and replacement instructions](https://github.com/mhoedt-ai/PLwC-Personal/releases/tag/v1.0.0) are provided alongside the binaries. Third-party components retain their own licenses and applicable modification and replacement rights.

PLwC-owned components use the [PolyForm Internal Use License 1.0.0](LICENSE), with [Personal Use Permission](PERSONAL_USE_PERMISSION.md) and [Official Redistribution Permission](OFFICIAL_REDISTRIBUTION_PERMISSION.md). These permit the specified private/internal use and free sharing of complete, unmodified official releases. Modified distribution and commercial offerings require a separate agreement. Earlier lawfully published Apache 2.0 content retains its original rights; see [licensing](LICENSING.md).

Known status inconsistency: successful Python and Node.js executions can report `sandbox_ready: false`. The agreed execution tests completed successfully; this display inconsistency is documented.

Contact: [info@plwc.de](mailto:info@plwc.de). [Voluntary support on Ko-fi](https://ko-fi.com/mhoedtai).
