# PLwC Personal 1.0 – Lizenz- und Veröffentlichungsgrenze

Stand: 2026-09-26

## Entscheidung des Product Owners

Ab Commit `dc542117966f7d7d805edeafe1124f6bbd1b7e8b` wird die weitere
Entwicklung als **PLwC Personal 1.0** fortgeführt. PLwC-eigene Inhalte dieser
Linie stehen unter der unveränderten PolyForm Internal Use License 1.0.0.
Eine zusätzliche PLwC Personal Use Permission 1.0 erlaubt Privatpersonen die
private Nutzung und Änderung. Eine separate PLwC Official Redistribution
Permission 1.0 erlaubt nur die kostenlose Weitergabe exakter, vollständiger
und unveränderter offizieller Releases.

Neue Änderungen, Builds, Images, Browserpakete und Dokumentation dürfen nicht
mehr unter Apache 2.0 veröffentlicht werden. Bis ein neuer PLwC-Personal-
Kandidat mit korrekten Lizenzmetadaten gebaut und ausdrücklich freigegeben
wurde, bleibt diese Entwicklungslinie privat und darf nicht über GitHub, GHCR,
Browser Stores oder andere öffentliche Kanäle verteilt werden.

Diese Grenze gilt für alle Arbeiten nach dem zuletzt öffentlich erreichbaren
Entwicklungsstand `030384e025f1f0a4f03c5678cfb9aa7a837f5453`.

## Bereits veröffentlichte Inhalte

Bereits unter Apache 2.0 veröffentlichte Inhalte und eingeräumte Rechte bleiben
unter ihren damaligen Lizenzbedingungen bestehen. Das gilt auch nach dem
Löschen von Release-Seiten, Tags oder öffentlichen Branchreferenzen. Lizenzen
von Drittanbieterkomponenten bleiben unverändert und ihre Hinweise müssen in
jeder späteren PLwC-Personal-Distribution erhalten bleiben.

Die öffentliche Zielbasis ist die Open Beta `v0.2.0-rc18.dev9` auf dem
geschützten Branch `main`. Spätere öffentliche 1.0-Pre-Releases und der
öffentliche Entwicklungsbranch sollen nach gesonderter ausdrücklicher Freigabe
zur Löschung zurückgezogen werden.

## Lokale technische Sperren

- lokaler Branch: `codex/plwc-personal-1.0-local`;
- kein konfigurierter Upstream;
- lokaler `.git/hooks/pre-push` blockiert jeden Push;
- keine GitHub-Releases, Tags, Actions-Veröffentlichungen oder Pull Requests;
- keine neuen oder aktualisierten GHCR-Pakete;
- keine Chrome-, Edge- oder sonstigen Store-Einreichungen;
- keine öffentliche Website-Aktualisierung auf den lokalen 1.0-Stand.

Diese Sperren schützen die noch nicht migrierten Artefakte. Sie werden nicht
allein durch die Auswahl der Lizenz aufgehoben.

## Gewählte Lizenzregeln

- private und interne Nutzung durch Personen, Unternehmen und Organisationen
  ist erlaubt;
- Änderungen für den eigenen privaten oder internen Gebrauch sind erlaubt;
- nur ein vom Lizenzgeber bezeichnetes offizielles und vollständig
  unverändertes Release darf kostenlos weitergegeben werden;
- modifizierte Quellen, Forks, neu gepackte Archive, eigene Builds und
  abgeleitete Versionen dürfen nicht veröffentlicht oder weitergegeben werden;
- Verkauf, Vermietung, OEM-/Embedded-/White-Label-Nutzung, bezahltes Hosting,
  Software-as-a-Service und Managed Services benötigen eine separate
  schriftliche Vereinbarung;
- offizielle Sonderversionen und kommerzielle Rechte können über
  `info@plwc.de` beauftragt werden;
- Namen, Logos und sonstige PLwC-Kennzeichen werden nicht mitlizenziert.

Die Browser-Erweiterungen gehören zu PLwC Personal. Sie werden nicht unter MIT
freigegeben. Die MIT-Lizenz des nachgewiesenen MCP-SuperAssistant-Fremdanteils
bleibt davon unberührt und muss weiterhin mitgeliefert werden.

Öffentliche Protokollspezifikationen oder Connector-SDKs sind erst dann offen
lizenziert, wenn sie in einem getrennten Bereich mit einer eigenen ausdrücklichen
MIT- oder Apache-2.0-Lizenz veröffentlicht werden.

Der lokale Kandidat mit SHA-256
`906033D6AC6626DEA41FDD6AAC230455AB2FF5AD96ABCF05D92C5B105C15178F`
ist ausschließlich ein interner QA-Kandidat. Er ist kein freigegebenes
PLwC-Personal-Distributionsartefakt.

## Vor einer PLwC-Personal-Distribution

Vor jeder Weitergabe außerhalb des privaten Testkreises sind mindestens diese
Punkte umzusetzen:

1. PLwC-eigene Lizenzmetadaten in Python-, MCPB-, Bridge-, Extension-, Image-
   und Installerartefakten auf diese Lizenz umstellen;
2. Apache-/MIT-/BSD- und sonstige Hinweise für bereits veröffentlichte oder
   übernommene Bestandteile korrekt erhalten und getrennt ausweisen;
3. einen vollständigen Drittanbieterhinweis für die tatsächlich ausgelieferten
   Abhängigkeiten erzeugen und mitliefern;
4. Produktname und Benutzertexte auf **PLwC Personal 1.0** umstellen;
5. einen neuen lokalen Kandidaten bauen und gezielt abnehmen;
6. eine neue ausdrückliche Product-Owner-Entscheidung über Empfänger und
   Verteilweg einholen.

Der verbindliche Standardlizenztext steht in `LICENSE`; die zusätzlichen
Freigaben stehen in `PERSONAL_USE_PERMISSION.md` und
`OFFICIAL_REDISTRIBUTION_PERMISSION.md`. Diese Datei dokumentiert die interne
Entwicklungs- und Veröffentlichungsgrenze.
