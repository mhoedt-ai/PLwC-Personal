# PLwC Personal – Veröffentlichungsplan

Stand: 2. Oktober 2026

Status: **G0, G1 UND G2 PASS / KEINE VERÖFFENTLICHUNGSFREIGABE**

## 1. Zielbild

PLwC wird als **PLwC Personal** weitergeführt. Die technische Produktversion
und Anfangsversion aller PLwC-eigenen Komponenten ist `1.0.0`; die erste
offizielle Freigabe heißt sichtbar `PLwC Personal` und verwendet den technischen
Git-Releasetag `v1.0.0`. Die bestehenden Chrome-/Edge-IDs erhalten als nächste
Store-Paketversion `2.0.0`, während das Bridge-Protokoll `1.0.0` bleibt. Vor
G3 wird erneut belegt, dass `2.0.0` größer als jede inzwischen an den
jeweiligen Store übermittelte Version ist.

Die Veröffentlichung soll vier Dinge gleichzeitig ermöglichen:

1. Der Quellcode darf öffentlich einsehbar sein.
2. Personen, Unternehmen und Organisationen dürfen PLwC intern verwenden und
   für den eigenen Gebrauch ändern.
3. Nur exakte, vollständige und unveränderte offizielle Releases dürfen
   kostenlos weitergegeben werden.
4. Verkauf, bezahlter Betrieb, Weitergabe geänderter Versionen und offizielle
   Sonderversionen benötigen eine gesonderte schriftliche Vereinbarung.

Die verbindlichen Lizenztexte stehen in `LICENSE`, `PERSONAL_USE_PERMISSION.md`,
`OFFICIAL_REDISTRIBUTION_PERMISSION.md`, `LICENSING.md` und
`COMMERCIAL-LICENSING.md`. Dieser Plan ist keine juristische Begutachtung und
ändert diese Texte nicht.

## 2. Offizielles Distributionsmodell

Das empfohlene Zielmodell ist:

| Bereich | Offizieller Kanal | Freigabegrenze |
| --- | --- | --- |
| Quellcode | öffentliches Repository `mhoedt-ai/PLwC-Personal` | erst nach G6-`GO-PUBLISH`; Root-Lizenz und historische Apache-Grenze müssen eindeutig sein |
| Windows-Setup | unveränderliches GitHub-Release plus Downloadverweis auf `plwc.de` | EXE, SHA-256, Größe, Commit, Signaturstatus, Lizenz- und Drittanbieterhinweise müssen zusammen veröffentlicht werden |
| Runtime-Images | öffentliche, nur lesbare GHCR-Pakete `plwc-personal-*` | erst nach G6-`GO-PUBLISH`; anonymer Pull, exakte Digests und OCI-Lizenzmetadaten werden danach geprüft |
| Browser-Erweiterung | offizielle Chrome- und Edge-Store-Einträge | Paket muss denselben Personal-Vertrag, dieselbe Privacy-Erklärung und den gültigen Setup-Link verwenden |
| Website | `plwc.de` | nennt ausschließlich freigegebene Artefakte und Hashes; Beta und Personal bleiben klar getrennt |
| Update Center | signiertes Personal-Release-Manifest | neuer Personal-Endpunkt und gepinnter Trustanker; kein Fallback auf alte öffentliche 1.0-Pre-Releases |

Ein öffentliches Personal-Setup darf keine Registry-Zugangsdaten enthalten.
Deshalb müssen die freigegebenen Runtime-Images zum Veröffentlichungszeitpunkt
anonym lesbar sein. Private GHCR-Pakete sind nur Build-, Staging- und
Abnahmequellen.

## 3. Kritischer Runtime-Befund

Die derzeit privaten Pakete `plwc-personal-document-worker`,
`plwc-personal-node-runner` und `plwc-personal-python-runner` bewahren die
bereits geprüften r27-Digests. Ihre Inhalte und OCI-Metadaten stammen jedoch aus
der früheren Apache-2.0-Linie. Sie sind deshalb gültige Migrations- und
QA-Artefakte, aber **kein sauber lizenzierter finaler Personal-Release**.

Vor dem ersten `PLwC Personal`-Release werden alle drei Images aus dem
eingefrorenen Personal-Quellcommit neu gebaut. Der neue Build muss:

- PLwC-eigene Schichten und OCI-Labels auf die Personal-Lizenz verweisen;
- Drittanbieter-Lizenzen unverändert und getrennt erhalten;
- neue Digests, SBOMs, Lizenzinventare, VEX-/Scanberichte und Provenienz
  erzeugen;
- weiterhin `linux/amd64`, `--network none`, `--pull never`, einen nur lesbaren
  Container-Root und den kontrollierten `/work`-Mount nachweisen;
- zunächst ausschließlich in privaten Staging-Paketen landen.

Erst die in G6 gebundenen neuen Digests dürfen als offizielle Personal-Images
öffentlich lesbar gemacht werden.

## 4. Umsetzungspakete

| ID | Arbeitspaket | Ergebnis |
| --- | --- | --- |
| PERS-01 | Produkt- und Versionsvertrag einfrieren | `PLwC Personal`, `1.0.0`, Git-Tag `v1.0.0`, Setupname `PLwC installer`, Storepakete `2.0.0` ohne Widerspruch |
| PERS-02 | Lizenz- und Drittanbietergrenze migrieren | Python-/MCPB-/Bridge-/Extension-/Installer-/Image-Metadaten nennen die korrekte Lizenz; Drittanbieterhinweise sind vollständig |
| PERS-03 | Personal-Quell- und Releasekanäle festlegen | Repository, GitHub-Release, Website, Update-Manifest und Supportlinks zeigen auf die Personal-Linie |
| PERS-04 | Runtime-Images neu bauen | drei neue digestfixierte Images samt SBOM, Lizenzbericht, Scan, VEX und Provenienz in privatem Staging |
| PERS-05 | Installer und Konfigurations-UI migrieren | Produktname, Setup-Texte, Safe Mode, Imagequelle, Update Center und Diagnosen sind Personal-konsistent |
| PERS-06 | Browserpakete migrieren | Chrome-/Edge-Pakete, Listings, Privacy, Support und Setup-Link sind Personal-konsistent; Extension-ID-Verträge bleiben stabil |
| PERS-07 | Reproduzierbaren Kandidaten bauen | EXE, Store-ZIPs, Manifest, Hashes, SBOM, Notices und neue Runtime-Locks sind auf einen Commit gebunden |
| PERS-08 | Komponenten- und Supply-Chain-Prüfung | Metadaten-, Lizenz-, Secret-, Payload-, Image- und Update-Verträge sind `PASS` |
| PERS-09 | G5-Delta-Abnahme | nur durch Personal-Änderungen betroffene Systempfade werden erneut real geprüft |
| PERS-10 | Release Review | Known Limitations, Release Notes, Hashes, Lizenztexte, Claims und Rollback sind vollständig |
| PERS-11 | Kontrollierte Veröffentlichung | jede externe Änderung wird separat freigegeben, ausgeführt und anonym gegengeprüft |

## 5. V-Modell-Zuordnung

### G0 – Personal-Anforderungsbaseline

- Produktname, Versionen, Lizenzgrenze, erlaubte Nutzung und offizielle
  Redistribution werden eingefroren.
- Öffentliche und private Kanäle werden getrennt festgelegt.
- Es wird entschieden, ob `mhoedt-ai/PLwC-Personal` beim Release öffentlich
  wird und welche Extension-Versionen eingereicht werden.
- Authenticode bleibt gemäß Product-Owner-Entscheidung optional; ein
  unsignierter Kandidat muss überall sichtbar als `NotSigned` bezeichnet
  werden.

Exit: keine offene Entscheidung verändert Lizenz, Paketidentität,
Distributionsweg, Update-Vertrauen oder Store-Identität.

### G1 – Architektur und Security

- Personal-Lizenzinventar und Drittanbietergrenze je Artefakt.
- Staging-zu-Public-Promotion ohne Rebuild oder Tag-only-Vertrauen.
- anonymer Runtime-Download ohne Zugangsdaten im Produkt.
- neuer Personal-Update-Endpunkt und Trustanker.
- Rücknahmeplan für Setup, Images, Stores und Website.

Exit: Ein unabhängiger Review bestätigt, dass kein privater Schlüssel, Token,
Workspace, Profil oder internes Releaseartefakt in öffentliche Payloads gelangt.

### G2 – Delta-Testplanung

Jede Änderung erhält eine Auswirkungszeile mit `REUSE`, `TARGETED-RERUN` oder
`FULL-RERUN`. Bereits bestandene G5-Nachweise dürfen wiederverwendet werden,
wenn Quellmodul, Konfiguration, Abhängigkeit, Buildinput und Produktclaim
unverändert sind. Eine reine Datums- oder Namensähnlichkeit genügt nicht.

Mindestens erneut zu prüfen sind:

- alle Lizenz- und Produktmetadaten im erzeugten Payload;
- Clean-Install gegen die exakten privaten Staging-Pakete mit einer nur auf
  dem disposable Testhost vorhandenen GHCR-Anmeldung; der Installer selbst
  erhaelt keine Credentials;
- Document-, Python- und Node-Operation plus Offline-Probes;
- Update, Repair und Upgrade von der vorhandenen r27/1.0-Testlinie;
- deutscher und englischer Personal-Installertext;
- Chrome und Edge mit dem finalen Storepaket;
- Update-Manifest, Hashfehler, Offlinepfad und Rücknahmeverhalten.

Ein vollständiger G5-Neulauf ist nur erforderlich, wenn eine funktionale,
Security-, Governance-, Installations- oder Runtime-Änderung die bisherige
Evidenz tatsächlich invalidiert.

### G3 – Eingefrorener Personal-Kandidat

- sauberer Checkout des privaten Personal-Repositories;
- neue Images aus demselben eingefrorenen Commit;
- versionierte EXE und Storepakete;
- `LICENSE`, Personal-Freigaben, Drittanbieterhinweise, SBOM und Hashlisten im
  tatsächlichen Payload;
- keine veralteten öffentlichen r22–r27-, Apache- oder Store-Downloadlinks in
  produktiven Dateien;
- zwei reproduzierbare Builds beziehungsweise vollständig erklärte,
  kontrollierte Abweichungen.

Exit: Commit, EXE-SHA256, Store-ZIP-SHA256, Runtime-Digests und
Release-Manifest-Hash sind unveränderlich gebunden.

### G4 – Komponentenverifikation

- bestehende Static-, Unit-, Contract- und Installer-Suiten;
- neuer Lizenz-/Produktname-/URL-Vertrag;
- vollständiges Drittanbieterinventar;
- Image-Label-, SBOM-, Provenienz-, Scan- und Secretprüfung;
- private Staging-Pakete sind nicht anonym erreichbar;
- Update Center akzeptiert ausschließlich den neuen Personal-Vertrag.

Exit: kein PLwC-eigener produktiver Apache-2.0-Claim, kein alter 1.0-
Downloadlink, kein Credential und kein ungeprüfter Artefaktwechsel bleibt offen.

### G5 – Systemvalidierung als Delta

Die in G2 freigegebene Auswirkungsmatrix bestimmt den Umfang. Für
Für das erste `PLwC Personal`-Release ist mindestens ein realer Windows-11-Pfad
mit Docker Desktop und WSL2 erforderlich. Vor `GO-PUBLISH` nutzt dieser Pfad
eine ausschliesslich auf
dem disposable Testhost eingerichtete GHCR-Anmeldung. Der neue Kandidat muss
Installation, Image-Erstdownload,
alle drei Runtime-Operationen, Repair/Upgrade, Neustart/Reconnect und die
finalen Browserpakete bestehen. Historische Funktionsnachweise dürfen nur mit
expliziter Begründung übernommen werden.

Exit: alle geänderten Claims sind real `PASS`; übernommene Evidenz ist auf
Commit, unveränderte Inputs und konkrete Test-IDs zurückgeführt.

### G6 – Release Acceptance und Veröffentlichung

G6 besitzt zwei getrennte Entscheidungen:

1. **GO-PUBLISH** bindet den exakten Kandidaten und erlaubt noch keine einzelne
   externe Aktion ohne deren benannte Product-Owner-Freigabe.
2. **GO-FINAL** folgt erst nach der Veröffentlichung und den anonymen
   Nachweisen für Quellcode, Setup, Hashes, einen sauberen Installerlauf ohne
   Registry-Anmeldung, GHCR-Pulls, alle drei Runtime-Operationen, Website,
   Update Center sowie Chrome-/Edge-Storestatus.

Fehlschlägt eine Post-Publication-Prüfung, wird der betroffene Kanal gestoppt
oder zurückgezogen. Ein anderes erfolgreiches Medium darf den Fehler nicht
verdecken.

## 6. Reihenfolge der Veröffentlichung

1. Personal-Commit und alle Artefakte einfrieren.
2. G6-Review, Lizenzinventar, Hashes und Release Notes abschließen.
3. Product Owner erteilt `GO-PUBLISH` für den exakten Kandidaten.
4. Quellrepository beziehungsweise offizielles Source-Archiv veröffentlichen.
5. exakt gebundene GHCR-Images öffentlich lesbar machen.
6. GitHub-Release mit EXE, Manifest, Hashliste und Notices veröffentlichen.
7. Website auf exakt diese Artefakte aktualisieren.
8. Chrome- und Edge-Pakete einreichen beziehungsweise veröffentlichen.
9. anonyme Downloads, Pulls, Storelinks und Update Center von einer sauberen
   Umgebung prüfen.
10. `GO-FINAL` oder kontrollierte Rücknahme dokumentieren.

Jeder Schritt besitzt eine eigene Freigabe. Das GO eines früheren Schritts ist
keine stillschweigende Zustimmung für den nächsten.

## 7. Aktueller Stand

| Bereich | Status am 02.10.2026 |
| --- | --- |
| G0-Produkt- und Versionsvertrag | **PASS / GO zu G1** |
| G1-Architektur-/Security-Design | **PASS / GO zu G2** nach unabhängiger Gegenprüfung; tatsächliche Umsetzung und Artefaktnachweise offen |
| G2-Delta-Testplanung | **PASS / GO zur Implementierung in G3**; alle 36 Anforderungen, neun G1-Kontrollen und reale Abnahmen zugeordnet; keine Übernahme historischer Ausführungsergebnisse |
| Lizenztexte im Repository | vorhanden |
| Öffentliche Beta-Grenze | hergestellt; Beta bleibt getrennt |
| Private Personal-Images | vorhanden und digestgeprüft; nur Migrations-/QA-Stand |
| Öffentliche alte r27-Images | entfernt |
| Personal-Metadaten in allen Artefakten | **offen** |
| neue Personal-Imagebuilds | **offen** |
| Personal-Updatekanal | **offen** |
| finaler Personal-Installer | **offen** |
| G4-Personal-Verifikation | **offen** |
| G5-Delta-Abnahme | **offen** |
| G6-Freigabe | **NO-GO** |

PERS-01 ist als G0-Entscheidung abgeschlossen, G1 als Entwurf nach unabhängiger
Gegenprüfung und G2 als Testdesign. Der nächste Schritt ist lokale
G3-Implementierung der neun Kontrollen P-G1-01 bis P-G1-09 und der geplanten
Tests. Nachweise stehen unter `installer/windows/evidence/G2/`, insbesondere
`personal-delta-test-plan.md` und `personal-g2-exit-review.md`. Metadatenmigration,
saubere Publikationsquellen, Kandidatenbuild und tatsächliche Artefaktprüfung
folgen nach der jeweiligen Freigabe. Eine externe Veröffentlichung ist dadurch
nicht freigegeben.
