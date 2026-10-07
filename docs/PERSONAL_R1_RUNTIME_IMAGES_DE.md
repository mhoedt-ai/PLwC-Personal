# PLwC Personal `personal-r1` – private Runtime-Images

**Migrations- und QA-Nachweis vom 26.09.2026, kein finaler Personal-Image-Lock.**
Die unten dokumentierten Digests enthalten noch die Apache-2.0-Metadaten der
früheren Linie. Für den offiziellen Release werden alle drei Images aus dem
eingefrorenen Personal-Commit neu gebaut und erhalten neue Digests. Maßgeblich
ist `docs/PLWC_PERSONAL_RELEASE_PLAN_DE.md`.

Stand: 26. September 2026

## Historischer privater Migrationsstand

Die nach der öffentlichen Beta entstandene Runtime-Linie wurde am 26.09.2026
in die folgenden privaten GHCR-Pakete gespiegelt. Diese Digests sind keine
offiziellen `personal-r1`-Runtime-Images:

| Komponente | Privates Paket | Unveränderter Digest |
| --- | --- | --- |
| Document Worker | `ghcr.io/mhoedt-ai/plwc-personal-document-worker` | `sha256:9f06960d30bc91701161d5490c24611f4e630ee8d0ab57eef04c6f7862df93e1` |
| Node Runner | `ghcr.io/mhoedt-ai/plwc-personal-node-runner` | `sha256:fccb8cc036d24c764504749d802674e6e6f3c9c72726334b73aa674830e7b6f2` |
| Python Runner | `ghcr.io/mhoedt-ai/plwc-personal-python-runner` | `sha256:83d7d224abbd287fab225a8d81c29b98795440af75edad3a70bf5f4b0c6278bc` |

Jedes Paket ist privat. Die Tags `0.1.0` und `personal-r1` zeigen direkt auf
den aufgeführten Digest.

## Provenienz und Lock

Die Image-Inhalte wurden nicht verändert oder neu gebaut. Sie stammen weiterhin
aus dem bereits abgenommenen Quellcommit
`1d8eaa4f82c2aec2fbe7212d446c7ebb05fa9fe8`. Deshalb bleiben OCI-Labels,
SBOM, Lizenznachweise, VEX-Dokumente, Scanberichte und Image-Digests erhalten.
Nur die Distributions-Repositorys wurden mit
`scripts/rebind_runtime_image_manifest_personal.py` umgebunden.

Der geprüfte Personal-Lock liegt im lokalen Release-Archiv unter
`T:\PLwC-Release-Archive\personal-r1-runtime-images-20260926\runtime-images-personal-r1.json`.

SHA-256 des Personal-Locks:

`f57ec7d6d9f3d93525a2f08446ba4f79205fc52396f0133fcb2e96f76534c051`

Das Verifikationspaket im gleichen Verzeichnis enthält die ursprünglichen
SBOM-, Lizenz-, VEX-, Provenienz- und Schwachstellenartefakte.

## Sicherheitsgrenzen und nächster Build

- Der frühere Workflow zur öffentlichen GHCR-Promotion ist entfernt.
- Der historische Migrations-Lock benennt die drei privaten
  `plwc-personal-*`-Repositorys. Er darf nicht in einen öffentlichen
  Personal-Installer übernommen werden.
- Die historischen lokalen Kurznamen bleiben ausschließlich als Eingabealias
  erhalten und werden auf den digestgesperrten Personal-Lock aufgelöst.
- Der neue Build verwendet `personal-r1-build-*` als lokale Prüftags. Der
  manuelle Staging-Workflow ist auf getrennte private Pakete mit dem Präfix
  `plwc-personal-private-staging-*` und commitgebundene
  `personal-r1-staging-*`-Tags vorbereitet. Ein Lauf benötigt die separate
  Freigabe für Produktionsbuild und GHCR-Push.
- Die spätere öffentliche Neuinstallation muss die neu gebauten, digestfixierten
  offiziellen `plwc-personal-*`-Images anonym laden können. Private
  Staging-Pakete sind nur für die kontrollierte Vorabprüfung bestimmt.
- Die öffentliche Beta `v0.2.0-rc18.dev9` verwendet diese r27/Personal-Images
  nicht und bleibt von dieser Umstellung unberührt.

## Gezielter Nachweis

Am 26. September 2026 bestanden die betroffenen Runtime-, Lock-, Manager-,
Installer- und Konfigurationstests mit `95 passed`. Dies ist ein gezielter
Migrationsnachweis und ausdrücklich keine erneute vollständige G5-Abnahme.
