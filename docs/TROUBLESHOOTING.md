# Troubleshooting

This guide describes PLwC Personal 1.0. Its exact Setup artifact and SHA-256
are pending the approved release candidate. Do not use an earlier Beta or
test installer as a Personal installer.

## Update Center Says `rejected`

Stop the update flow. `rejected` means the live manifest, its signing key, its
canonical signature, an HTTPS URL, or signed build metadata failed validation.
Do not download the artifact directly as a workaround. A missing or empty
Personal trust store is deliberately fail-closed. The old r26/r27 public key is
not a Personal trust anchor; an unknown key ID or mismatched signature must be
treated as a rejected update.

## Update Center Says `offline`

PLwC remains usable. The page shows both the failed check time and the last
valid manifest time. A cached manifest is usable only because its signature is
reverified on every plan/download operation. Automatic checks are interval
limited; use the manual check after network or proxy access is restored.

## Update Download Or Installer Fails

A short download, wrong size, or wrong SHA-256 leaves no executable. An
installer return-code failure surfaces the matching revision's rollback report
under the configured `logs\setup` directory when present. Do not repeatedly
start the same installer after an ambiguous result; inspect that report and run
the read-only PLwC Doctor diagnosis first.

## Docker Missing

PLwC runs in Safe Mode.

Sandboxed code execution is disabled until Docker is installed and running.

## Claude Shows Multiple MCP Servers

This is a configuration error.

Only `plwc-gateway` should be active.

## Windows Shows Unknown Publisher

The planned Personal Setup is unsigned (`NotSigned`), so Windows may show an
unknown-publisher warning. Before running it, compare the exact file name,
size and SHA-256 against the approved Personal release record from the
official `PLwC-Personal` repository. No final Personal hash exists yet. Stop
if any value differs; do not substitute an earlier test installer.

## Setup Asks For Every Directory During An Update

A complete installation should be detected before the directory and runtime
pages. If Setup asks again, inspect the installation summary and
`selection.ini` under `%APPDATA%\PLwC\config\installer` (or the selected
configuration root). The prior installation may be incomplete or its persisted
state may be missing.

Do not create new version-suffixed Gateway or Bridge directories as a repair.
New installs use `app\gateway` and `app\bridge`; valid older paths are preserved
automatically.

## Workspace Change Is Not Visible

Open **PLwC Configuration**, enter an absolute path under the workspace-change
control and select **Save settings**. PLwC creates missing `Tagebuch`, `Temp`
and `Trashcan` directories but does not move existing files. Restart only the
client that still shows the old value.

The shared value is stored in `gateway-settings.json` and mirrored into the
installer selection state so later updates continue to use it.

## Duplicate PLwC Configuration Shortcuts

The Personal installer owns the canonical desktop shortcut
`PLwC-Konfiguration`. Once an exact Personal Setup candidate is approved,
use its Repair flow to remove installer-owned legacy variants and recreate the
shortcut with the PLwC icon. A manually created shortcut is outside this
cleanup contract.

## Chat Bridge Does Not Reach 8 / 8 Tools

1. Open the PLwC panel and select **Status**.
2. Select **Reconnect** once.
3. Confirm that the endpoint is `ws://127.0.0.1:3007/message`.
4. If the Launcher is missing, run Repair with the approved Personal Setup.
5. If the Launcher is available but the Bridge remains offline, inspect the
   setup summary and Bridge logs referenced by the installed diagnostics.

Setup registers `plwc.chat_bridge.launcher` per user for Chrome, Edge and
Brave. Do not run maintainer scripts from a repository as an end-user repair.

## Browser Store Page Is Unavailable

On 2026-09-27 Chrome showed an accepted, unpublished `1.0.1` draft; Edge
showed a `1.0.1` draft while its old listing was `Unpublish in Progress`.
Personal extension `1.0.4` is only a local candidate. A public Store link is
not a valid Personal installation path until the exact packages have passed
review and publication is separately authorized.

Loading the installed extension folder in Developer mode uses the separate
development identity. It can test local behavior, but it cannot prove Chrome or
Edge Store-ID acceptance.
