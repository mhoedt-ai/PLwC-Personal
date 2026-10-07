# PLwC Windows Installer - V-Modell und Quality Gates

Status: verbindliche Arbeitsbasis fuer Implementierung und Verifikation
Geltungsbereich: `installer/windows/`, PLwC Gateway, Claude Desktop MCPB,
Codex- und Odysseus-STDIO-Integration, PLwC Chat Bridge sowie die von PLwC
kontrollierten GHCR-Runtime-Images unter Windows. Fuer PLwC Personal gilt
zusaetzlich das Personal-Releaseprofil dieses Dokuments.

## 1. Zweck und normative Sprache

Dieses Dokument uebersetzt die Nutzeranforderungen in eine durchgaengige
V-Modell-Kette. Jede Anforderung wird links spezifiziert und entworfen, unten
implementiert und rechts gegen dieselbe Anforderung verifiziert. Ein Gate ist
nur bestanden, wenn seine Exit-Kriterien erfuellt und seine Evidenzen
reviewfaehig abgelegt sind.

Die Begriffe **MUSS**, **DARF NICHT**, **SOLL** und **KANN** sind normativ. Eine
Freigabe ohne MUSS-Nachweis ist nicht zulaessig.

Normative Quellen:

- `docs/WINDOWS_INSTALLER_PLAN.md`
- `docs/INSTALLATION.md`
- `docs/GITHUB_BETA_WORKFLOW.md`
- `docs/R27_WINDOWS_IMAGE_DELIVERY_PLAN_DE.md`
- `docs/PLWC_PERSONAL_1_0_LOCAL_POLICY.md`
- `docs/PLWC_PERSONAL_RELEASE_PLAN_DE.md`
- `docs/PERSONAL_R1_RUNTIME_IMAGES_DE.md`
- `docs/evidence/R26_FIELD_INCIDENT_2026-09-05_DE.md`
- `docs/LOCAL_CHATGPT_CLIENT_ADAPTER.md`
- `integrations/plwc-chat-bridge/README.md`
- `integrations/plwc-chat-bridge/extension/README.md`
- `integrations/plwc-chat-bridge/bridge/README.md`

Bei Widerspruechen gilt diese Reihenfolge: explizite Nutzeranforderung,
Security-/Privacy-Grenze, dieses Dokument, danach die uebrigen Quellen. Ein
Widerspruch MUSS in G0 dokumentiert und vor G1 entschieden werden.

## 2. Rollen und Unabhaengigkeit

| Rolle | Verantwortung |
| --- | --- |
| A-REQ | Anforderungen, Traceability und Abnahmekriterien |
| A-ARCH | Installer-, Payload- und Integrationsdesign |
| A-BUILD | Implementierung, reproduzierbarer Build und technische Nachweise |
| A-TEST | Testdesign, Windows-VM-Matrix und Ergebnisbewertung |
| A-SEC | Security-, Privacy-, Hash-, Lizenz- und Payload-Pruefung |
| A-REL | Gate-Entscheidung, Releasekandidat und Freigabedokumentation |

A-BUILD darf eigene Ergebnisse vorpruefen, aber G4 bis G6 benoetigen mindestens
eine dokumentierte Gegenpruefung durch A-TEST oder A-SEC. A-REL darf ein
fehlgeschlagenes Security-, Privacy- oder Integritaetskriterium nicht
ueberstimmen.

## 3. Anforderungsbaseline

### 3.1 Nutzeranforderungen

| ID | Verbindliche Anforderung | Abnahmebeobachtung |
| --- | --- | --- |
| UR-001 | Das auslieferbare Windows-Setup MUSS eine startbare `.exe` sein. Installation und Ersteinrichtung DUERFEN den Nutzer nicht zum manuellen Ausfuehren einer `.ps1` auffordern. | Doppelklick auf die EXE startet den Setup-Assistenten; der komplette Standardfluss endet ohne Terminalarbeit. |
| UR-002 | Der Assistent MUSS Claude Desktop MCPB, STDIO fuer Codex, STDIO fuer Odysseus und PLwC Chat Bridge einzeln, in beliebiger Kombination und gemeinsam auswaehlbar machen. Der gemeinsame Gateway-Runtime-Kern bleibt erforderlich. | Alle 16 Bitmasken der vier optionalen Komponenten werden korrekt aufgeloest; `1111` installiert alle Ziele. |
| UR-003 | App-, Gateway-, Bridge-, Workspace-, Profile-, globale Config-, State-, Log- und Backup-Verzeichnisse MUESSEN editierbar sein und sichere Defaults besitzen. | UI zeigt die Defaultwerte; gueltige Alternativen werden uebernommen; unzulaessige Verschachtelungen werden vor dem Schreiben blockiert. |
| UR-004 | Der Assistent MUSS eine erste Profil-/Runtime-Konfiguration anbieten und fuer jedes Feld einen Default setzen. | Preview und installierte Konfiguration stimmen fuer Default- und Override-Fall ueberein. |
| UR-005 | Installerquellen, PLwC Gateway und Chat Bridge MUESSEN in diesem einen PLwC-Repository versioniert und gemeinsam baubar sein. | Ein sauberer Checkout enthaelt alle Buildquellen; der Build referenziert keinen privaten zweiten Source-Checkout. |
| UR-006 | Nach einmaliger Native-Launcher-Registrierung MUSS `Status -> Reconnect` die lokale Chat Bridge auch nach einem Windows-Neustart starten koennen, ohne den Launcher erneut zu installieren. | Reboot-Test: Browser oeffnen, Reconnect klicken, Bridge und Gateway werden erreichbar; Registry-Installation wird nicht wiederholt. |
| UR-007 | Vor der finalen Bestaetigung MUSS eine vollstaendige Schreibvorschau sichtbar sein; Verzeichnisse und Hostkonfigurationen DUERFEN vorher nicht angelegt oder veraendert werden. | Abbruch auf der Preview-Seite hinterlaesst keine neuen PLwC-Dateien, Registry-Eintraege oder Hostkonfigurationsaenderungen. |
| UR-008 | Der Assistent MUSS vor der Schreibvorschau komponentenabhaengige Voraussetzungen erkennen und sichtbar mit `ready`, `blocked`, `prepared` oder `safe-mode` bewerten. Fehlendes Python `>=3.11` oder fehlendes `mcp` im erkannten Interpreter blockiert den erforderlichen Gateway und damit die Installation. Fehlendes Claude Desktop blockiert Claude MCPB. Fehlendes Node.js oder fehlendes Chrome/Edge/Brave blockiert die Chat Bridge. Fehlendes Codex oder Odysseus warnt und erlaubt nur einen klar bezeichneten `prepared`-Snippet ohne Hostmutation. Fehlendes Docker warnt, setzt `safe_mode_expected=true` und blockiert den Kern nicht. | Clean-Windows-11-Negativmatrix: Jede fehlende Voraussetzung erzeugt die geforderte Block-/Warnreaktion; Preview, Installationszusammenfassung und Dateisystem-/Registry-Diff stimmen mit dem Status ueberein. |
| UR-009 | Alle Standard- und Custom-Seiten des Installers MUESSEN bei `1366x768` vollstaendig sichtbar und bedienbar sein. Titel, Texte, Eingaben und Navigationsschaltflaechen DUERFEN weder ueberlappen noch abgeschnitten werden. Lange Formulare MUESSEN auf mehrere Seiten verteilt werden. Boolean-Werte MUESSEN als Checkboxen statt als editierbare `true/false`-Textfelder erscheinen. | Screenshot-/Control-Tree-Abnahme jeder Seite bei `1366x768` in beiden Sprachen und fuer laengste dynamische Texte; Qdrant und Persona-Layer werden ausschliesslich per Checkbox geaendert. |
| UR-010 | Der Installer MUSS eine vollstaendige deutsche und englische Oberflaeche anbieten. Die gewaehlte Sprache MUSS fuer alle installer-eigenen Standard-/Custom-Texte, Komponenten- und Prerequisite-Meldungen, Validierungs-/Fehler-/Rollback-Texte, Preview sowie Abschluss- und Next-Action-Texte ohne Sprachmischung gelten. | Zwei vollstaendige Doppelklick-Durchlaeufe in Deutsch und Englisch einschliesslich Negativfehlern und Abschlussseite; String-Inventar und Screenshots zeigen keine fehlenden oder gemischten Texte. |
| UR-011 | Wenn Python, Node.js oder Docker fehlt, MUSS der Installer wahlweise eine ausdrücklich ausgewählte automatische Installation oder eine Schaltfläche zur offiziellen Downloadseite anbieten. Automatische Optionen sind standardmäßig aus. Die systemweite Node.js-MSI MUSS eine Windows-Administratorbestätigung anfordern. Fehlendes Claude Desktop oder Chrome/Edge/Brave MUSS bereits auf der Prüfseite stoppen, bevor irgendein Download oder Zusatzprogramm startet. Vor der Akquisition MUSS der vollständige Plan erneut nebenwirkungsfrei geprüft werden. `Weiter` MUSS deaktiviert bleiben, solange eine fehlende Pflichtvoraussetzung weder vorhanden noch ausdrücklich zur Installation ausgewählt ist. Ein fehlgeschlagener Versuch MUSS genau eine benannte Meldung erzeugen, die Auswahl in einen bewussten Wiederholungszustand versetzen und alle nachfolgenden Aktionen stoppen. Lange Downloads und Herstellerinstallationen MÜSSEN lokalisierte Fortschrittsseiten zeigen. Nach jedem Versuch werden alle Voraussetzungen erneut geprüft. | Clean-Windows-11-Matrix für Zustimmung, Ablehnung, DNS-/Proxyfehler, Abbruch, UAC-Abbruch, Fehler und Neustart; ohne vollständigen lösbaren Plan erfolgt kein Download/Prozessstart, mit Zustimmung folgt `preflight -> download -> hash verification -> visible install wait -> recheck`. Ein fehlgeschlagener Download zeigt keine zusätzliche generische Gate-Meldung; Wiederholung erfordert einen neuen Klick. |
| UR-012 | Der Installer MUSS bei jedem ersten interaktiven Start vor der Begruessungsseite eine sichtbare Sprachauswahl fuer Deutsch und Englisch anzeigen. Die Windows-Anzeigesprache wird vorausgewaehlt, eine manuelle Auswahl bleibt moeglich und eine unbekannte Sprache faellt auf Englisch zurueck. | Clean-VM-Start in deutscher, englischer und nicht unterstuetzter Windows-Anzeigesprache; der erste sichtbare Setup-Dialog erlaubt die Auswahl. `/LANG=german` und `/LANG=english` werden separat geprueft. |
| UR-013 | Vor dem Download oder Start von Python-, Node.js-, Docker- oder Windows-Komponenten MUSS der Installer die erforderlichen Administratorrechte erklaeren und pruefen. Bei fehlenden Rechten MUSS er einen kontrollierten Neustart als Administrator anbieten, Sprache und Auswahl bewahren und die PLwC-Daten weiterhin dem urspruenglichen Benutzerprofil zuordnen. | Standardbenutzer-, lokaler-Administrator- und alternatives-Administratorkonto-Matrix; vor Rechtepruefung startet kein Download. UAC-Abbruch und Hersteller-Exitcodes werden einmalig, lokalisiert und mit Protokollpfad gemeldet. |
| UR-014 | Der Installer MUSS die Groesse des PLwC-Payloads getrennt von den geschaetzten Downloads und Speicherbedarfen fuer Python, Node.js, Docker Desktop, WSL und variable Images/Modelldaten anzeigen. Unbekannte Werte duerfen nicht als null ausgewiesen werden. | Komponenten-, Akquisitions- und Preview-Seite zeigen exakten PLwC-Payload, einzelne Downloads, bekannte Summe, Mindest-Speicherbedarf und variablen Zusatzbedarf. Ein Free-Space-Negativtest stoppt vor Akquisition beziehungsweise Schreiben. |
| UR-015 | Der r27-Installer MUSS bei erreichbarem Docker-Dienst eine standardmaessig ausgeschaltete, ausdrueckliche Auswahl zur Installation der drei digest-fixierten PLwC-Runtime-Images fuer Document Worker, Node-Sandbox und Python-Sandbox anbieten. Nach Zustimmung MUSS er Quelle, Version, Plattform, Download- und Speicherbedarf anzeigen, die Images ohne GitHub-Anmeldung von `ghcr.io/mhoedt-ai` laden, jeden Digest verifizieren und fuer jede Laufzeit einen echten netzwerklosen Probe ausfuehren. Ohne Zustimmung oder bei einem Fehler bleibt die Kerninstallation im sichtbar dokumentierten Safe Mode moeglich. | Clean-Windows-11 ohne lokale Images: Ablehnung startet keinen Pull und endet ehrlich im Safe Mode; Zustimmung laedt exakt die manifestierten Digests, alle drei Probes bestehen und `plwc_document_operation` erzeugt ein validiertes Testdokument. Falscher Digest, Offline/Proxy, Abbruch und Wiederholung liefern eindeutige lokalisierte Ergebnisse. |
| UR-016 | Jeder von Setup gestartete Wartungs-, Migrations-, Image- oder Probeprozess MUSS bei Erfolg und Fehler mindestens Phase, Befehlskategorie, Startstatus, Exitcode, redigiertes stdout/stderr, Exceptiontyp und Reportpfad dauerhaft protokollieren. Der Diagnoseexport MUSS Preflight-, Transaktions-, Image-Akquisitions-, Postflight- und Rollbackberichte einschliessen. Ein angezeigter Berichtspfad DARF NICHT auf eine fehlende Datei zeigen. | Fault Injection mit erwarteten und unerwarteten Python-Ausnahmen sowie Exitcodes 1/20/30/40/50: Setup zeigt genau einen Fehler, der referenzierte Bericht existiert, der Export enthaelt ihn und es gehen keine Geheimnisse oder absoluten fremden Benutzerpfade in Releaseevidenz ein. |

### 3.2 Verbindliche System- und Sicherheitsanforderungen

| ID | Verbindliche Anforderung |
| --- | --- |
| SR-001 | Alle Ziele verwenden genau einen oeffentlichen MCP-Server `plwc-gateway` mit genau acht oeffentlichen Facade-Tools. Raw PBA, PLfC, Commander, Filesystem, Host-Shell oder ein zweiter PLwC-Server DUERFEN NICHT registriert werden. |
| SR-002 | Workspace und Profiles MUESSEN getrennt sein; Profiles DARF NICHT unter Workspace liegen. App, Config, State, Logs und Backups DUERFEN NICHT als Workspace exponiert werden. |
| SR-003 | Die Chat Bridge MUSS an `127.0.0.1:3007` gebunden bleiben, nur zugelassene Extension-Urspruenge akzeptieren und genau einen Gateway-Child starten. Mutierende Aufrufe, Sandbox und Governor `apply` behalten ihre Bestaetigungsgrenzen. |
| SR-004 | Bestehende Hostkonfigurationen DUERFEN nur bei bekanntem, versionsgeprueftem Schema nach Backup und anschliessender Validierung veraendert werden. Andernfalls wird ausschliesslich ein vorbereiteter Konfigurationsausschnitt erzeugt. |
| SR-005 | Jeder Releasekandidat MUSS SHA256, Dateigroesse, Dateiliste/SBOM, Lizenznachweis und den wahrheitsgemaessen Signaturstatus besitzen. PLwC 1.0 DARF nach ausdruecklicher Product-Owner-Entscheidung als unsignierter Release erscheinen. In diesem Fall MUESSEN Setup, Buildidentitaet, Downloadseite und Release Notes sichtbar `unsigned` beziehungsweise `Nicht signiert` nennen, den exakten SHA256, den zugehoerigen Quell-Commit/-Tag und die tatsaechliche Lizenzart angeben und auf die zu erwartende Windows-Warnung zum unbekannten Herausgeber hinweisen. PLwC Personal DARF NICHT als Open Source bezeichnet werden, sofern die gewaehlte Lizenz nicht den einschlaegigen Open-Source-Kriterien entspricht. Der Release DARF NICHT als signiert, publisher-verifiziert oder production-certified bezeichnet werden; eine Umgehung oder Deaktivierung von Windows-Sicherheitsfunktionen DARF NICHT empfohlen werden. |
| SR-006 | Releasepayload und Evidenzen DUERFEN keine realen Profile, Workspaces, Logs, Secrets, `.env`, echte `security.yaml`, privaten Transkripte oder absoluten Benutzerpfade enthalten. |
| SR-007 | Das Setup MUSS bei Fehlern geschlossen abbrechen oder gezielt rueckrollen. Eine teilweise registrierte Hostintegration darf nicht als Erfolg gemeldet werden. |
| SR-008 | Docker DARF ausschließlich nach ausdrücklicher Auswahl durch den Benutzer installiert werden. Der Installer DARF Docker-Lizenzbedingungen NICHT automatisch annehmen und KEIN Image implizit ziehen. Bei fehlender CLI, nicht erreichbarem Dienst oder fehlendem erforderlichen Image MUSS er sichtbar warnen, `safe_mode_expected=true` dokumentieren und die nicht verfügbaren Sandbox-/Document-Worker-Funktionen nennen. Profil- und Kerninstallation bleiben möglich. |
| SR-009 | Automatische Voraussetzungspakete MÜSSEN über HTTPS von offiziellen Hersteller-Domains, mit festgelegter Version und festgelegtem SHA-256 bezogen werden. Die vollständige Python-Paketmenge MUSS exakt versionsgebunden sein und für jedes Paket SHA-256-Hashes erzwingen. Python-Pakete und Docker Desktop werden benutzerbezogen installiert. Node.js DARF nur nach ausdrücklicher Auswahl über die offizielle, hashgeprüfte und signierte LTS-MSI systemweit mit Windows-Administratorbestätigung installiert werden. Silent-Modi erteilen keine Zustimmung. Claude Desktop und Browser werden nicht automatisch installiert. |
| SR-010 | Eine Erhoehung mit anderen Administrator-Anmeldedaten DARF App-, Config-, State-, Log-, Workspace- und Profildaten nicht unbemerkt in das Profil des Administratorkontos umleiten. Der urspruengliche Benutzerkontext MUSS explizit bewahrt oder die Installation vor jeder Schreibaktion sicher beendet werden. |
| SR-011 | Alle PLwC-Runtime-Images MUESSEN aus reproduzierbaren, digest-gepinnten Basen gebaut, fuer `linux/amd64` manifestiert, als unveraenderliche `@sha256:`-Referenzen verwendet und mit OCI-Quell-/Versions-/Lizenzlabels, SBOM, Lizenzinventar, Schwachstellenbericht und Provenienz belegt werden. `latest`, Tag-only-Vertrauen, modellgesteuerte Imageauswahl und im Installer gespeicherte Registry-Zugangsdaten sind verboten. Ein GHCR-Push, die oeffentliche Paketsichtbarkeit und ein Produktionsbuild benoetigen jeweils die ausdrueckliche Freigabe des Product Owners. |

### 3.3 PLwC-Personal-Releaseanforderungen

| ID | Verbindliche Anforderung |
| --- | --- |
| PR-001 | PLwC-eigene Inhalte der Personal-Linie MUESSEN in Quell-, Installer-, MCPB-, Bridge-, Extension-, Image- und Release-Metadaten die verbindliche Personal-Lizenzgrenze nennen. Historisch oder durch Drittanbieter unter Apache-2.0, MIT, BSD oder anderen Bedingungen lizenzierte Inhalte MUESSEN getrennt und unveraendert ausgewiesen werden. |
| PR-002 | Die sichtbare Produkt- und erste Releasebezeichnung MUSS `PLwC Personal`, der sichtbare Setupname `PLwC installer` und die technische Anfangsversion aller PLwC-eigenen Komponenten `1.0.0` lauten. Fuer bestehende Chrome-/Edge-IDs MUSS die naechste Store-Paketversion `2.0.0` sein; die Bridge-Protokollversion bleibt `1.0.0`. Produktversion, Releasetag, interne Installerrevision, Bridge-Buildidentitaet und monotone Storeversionen MUESSEN vor G3 widerspruchsfrei eingefroren sein. Ein Artefakt mit alter Produkt- oder Lizenzidentitaet DARF NICHT als Personal-Release bezeichnet werden. |
| PR-003 | Ein offizielles Personal-Release MUSS als exakte unveraenderliche Einheit mit Commit, Dateiname, Groesse, SHA-256, Signaturstatus, Lizenzsatz, Drittanbieterhinweisen und allen Runtime-Digests bezeichnet werden. Nur diese Einheit darf unter der Official Redistribution Permission als offiziell weitergegeben werden. |
| PR-004 | Ein oeffentlich einsehbarer Personal-Quellstand MUSS die aktuelle Personal-Lizenz am Repository-Root und die historische Apache-Grenze wahrheitsgemaess dokumentieren. Die Oeffentlichkeit des Quellcodes DARF NICHT als Erlaubnis zur Weitergabe geaenderter Builds beschrieben werden. |
| PR-005 | Ein oeffentliches Setup DARF keine Registry-Credentials enthalten. Die von ihm angebotenen offiziellen Runtime-Images MUESSEN nach der ausdruecklichen G6-Publikationsfreigabe anonym lesbar, digestfixiert und mit Personal-konsistenten OCI-Lizenzlabels, SBOM, Lizenzinventar, Scan und Provenienz belegt sein. Private Staging-Images sind kein Endnutzer-Distributionsweg. |
| PR-006 | Chrome- und Edge-Pakete MUESSEN dieselbe Personal-Produkt-, Lizenz-, Privacy-, Support- und Setup-Identitaet wie der eingefrorene Kandidat verwenden. Storeversionen MUESSEN monoton sein; bestehende Extension-IDs und Native-Messaging-Vertraege duerfen nur kontrolliert geaendert werden. |
| PR-007 | GitHub-Release, GHCR-Sichtbarkeit, Source-Repository, Website, Update Center, Chrome Store und Edge Store sind getrennte externe Freigaben. Keine Gate-Entscheidung oder Kanalveroeffentlichung erteilt stillschweigend eine andere Freigabe. |
| PR-008 | Bestehende Testevidenz DARF fuer Personal nur wiederverwendet werden, wenn eine dokumentierte Auswirkungsmatrix unveraenderte Quellmodule, Buildinputs, Abhaengigkeiten, Konfigurationen und Produktclaims nachweist. Betroffene Pfade MUESSEN gezielt erneut ausgefuehrt werden; funktionale oder Security-relevante Aenderungen koennen einen vollstaendigen Ruecksprung erzwingen. |
| PR-009 | G6 MUSS `GO-PUBLISH` und `GO-FINAL` trennen. `GO-PUBLISH` bindet den exakten Kandidaten; `GO-FINAL` ist erst nach anonymen Post-Publication-Pruefungen aller beanspruchten Kanaele zulaessig. Ein fehlgeschlagener Kanal MUSS gestoppt oder zurueckgezogen und als Abweichung dokumentiert werden. |

### 3.4 Bekannter Clean-Windows-11-Fund

| Fund-ID | Beobachtung | Bewertung | Ruecksprung |
| --- | --- | --- | --- |
| WIN11-PREREQ-001 | Der Kandidat `PLwC-Setup-0.2.0-rc18.dev9.exe` schloss eine Auswahl aller Komponenten auf einem reinen Windows 11 ohne Python, Node.js, Chrome, Claude Desktop, Codex und Odysseus erfolgreich ab. Er kopierte Payloads und erzeugte Snippets, ohne die nicht lauffaehigen Ziele als blockiert oder vorbereitet zu kennzeichnen. Docker fehlte ohne sichtbaren Safe-Mode-Hinweis. | `FAIL`; der Kandidat ist `superseded` und nicht freigabefaehig. Fehlende Produktpruefung darf nicht als `BLOCKED` bewertet werden. | G1 bis G4 werden wieder geoeffnet. G5 bleibt `HOLD`, G6 bleibt `NO-GO`, bis ein neuer gehashter Kandidat UR-008 nachweist. |
| WIN11-UI-001 | Bei `1366x768` war die Runtime-Seite unten abgeschnitten. Boolean-Werte wurden als editierbare `false/true`-Felder gezeigt; der deutsche Ablauf enthielt englische installer-eigene Feldtexte. | `FAIL`; Layout und Sprachumfang des Kandidaten erfuellen UR-009/UR-010 nicht. | G1 bis G4 bleiben wieder geoeffnet. Der neue Kandidat muss beide Sprachen und jede Seite bei der Mindestaufloesung nachweisen. |
| WIN11-PREREQ-002 | Bei ausgewähltem Claude MCPB und Chat Bridge wurden fehlendes Claude Desktop und Node.js zwar erkannt, aber erst nach einer zuvor ausgewählten Docker-Installation als Fehler gemeldet. Während der stillen Docker-Installation war keine Warteseite sichtbar; die Docker-Auswahl blieb danach gesetzt und `Weiter` wiederholte Meldung oder Installation. | `FAIL`; der Kandidat `5AD2BE5882F24B2930CABFF8717ADE78B58C654A85B5E67AAEAA9264EFE5F399` ist `superseded`. | G2 bis G5 werden wieder geöffnet. Der Nachfolger benötigt Vorab-Gate, einmalige Aktionen, sichtbaren Installationsfortschritt und Neustart-/Fehler-Short-Circuits. |
| WIN11-R26-IMAGE-001 | Der r26-Kandidat `d604e771…97dc65` wurde auf einem realen Windows-11-System ohne vorbereitetes `plwc-document-worker:0.1.0` ausgeführt. Gateway und Bridge waren erreichbar, ein echter Dokumentaufruf endete jedoch mit `UNAVAILABLE/worker_missing`. | `FAIL`; der positive Abnahmehost hatte das Image bereits lokal. `docker image inspect` ist keine Imagebereitstellung. | G0 bis G5 werden fuer r27 wieder geoeffnet. UR-015 und SR-011 muessen vor einer neuen Releaseentscheidung vollstaendig nachgewiesen werden. |
| WIN11-R26-PREFLIGHT-001 | Ein erneuter Lauf desselben r26-Kandidaten endete im Preflight mit Exitcode 1. Der in der UI genannte JSON-Bericht fehlte im bereitgestellten Diagnoseexport. | `FAIL`; der unerwartete Ausnahme- und Exportpfad ist nicht beweiskraeftig. | G0 bis G5 werden fuer r27 wieder geoeffnet. UR-016 muss fuer erwartete und unerwartete Fehler nachgewiesen werden. |
| WIN11-PREREQ-003 | Auf der Aktionsseite blieb `Weiter` bei fehlender, nicht ausgewählter Python-Installation aktiv. Nach Downloadfehler `12007` war die Auswahl gelöscht und der nächste Klick zeigte wieder den unvollständigen Plan. Fehlendes Node.js war ein manueller Blocker und erreichte deshalb keine automatische oder offizielle Installationsoption. | `FAIL`; der Kandidat `B8A388795F2ECD904E9B0521400EFFE2CA079BF7D75A373250CC774E76A2772C` ist `superseded`. | G2 bis G4 werden erneut geöffnet. Der Nachfolger benötigt Pflichtauswahl-gesteuerte Navigation, benannten Retry-Zustand, DNS-Diagnose mit hashgeprüftem Fallback und ausdrückliche Node.js-Akquisition. |
| WIN11-UI-002 | Lange dynamische Beschriftungen wie `Installieren und weiter`, `Installation erneut versuchen` und `Pflichtauswahl treffen` wurden auf der festen Navigationsschaltflaeche abgeschnitten. Eine explizite Sprachauswahl war im beobachteten Startfluss nicht sichtbar. | `FAIL`; Navigation und Sprachstart erfuellen UR-009, UR-010 und UR-012 nicht. | G2 bis G5 werden geoeffnet. Die Navigationsschaltflaeche bleibt bei `Weiter`/`Next`; der Aktionsstatus steht im Seiteninhalt. |
| WIN11-PREREQ-004 | Die Node.js-Installation scheiterte ohne auswertbaren MSI-Exitcode, ohne sichtbaren Logpfad und ohne belastbaren Umgang mit UAC-Abbruch, Neustartbedarf oder einer nach Installation veralteten PATH-Umgebung. | `FAIL`; die Bridge darf nach kopierten Dateien nicht als installiert gelten. | G1 bis G5 werden geoeffnet. Erhoehung, MSI-Logging, absolute Runtime-Pfade und Neustartcodes muessen nachgewiesen werden. |
| WIN11-BRIDGE-001 | Die Erweiterung meldete einen fehlenden Native Host und verwies Endbenutzer auf ein Repository-PowerShell-Skript. Reconnect erreichte weder den WebSocket-Server noch acht Tools. | `FAIL`; UR-001, UR-006 und SR-003 sind verletzt. | G1 bis G5 werden geoeffnet. Native Host und Launcher werden durch Setup oder Repair eingerichtet; Erfolg erfordert Listener und `8/8`. |
| WIN11-SIZE-001 | Die sichtbare Setup-Groesse deckte nur den kleinen PLwC-Payload ab und nannte weder den Docker-Download noch den mehrgigabytegrossen WSL-, Image- und Modelldatenbedarf. | `FAIL`; die Installationsentscheidung war unvollstaendig informiert. | G0 bis G5 werden geoeffnet. Ein versioniertes Groessenmanifest und getrennte Anzeigen gemaess UR-014 sind Pflicht. |
| WIN11-UI-003 | Der Kandidat `8E5744FB18422F5CBDB5CA9A6DD53CF768A0F24AF76876CF2DB0D5BF66BDF94D` meldete auf der Voraussetzungenseite `Runtime error ... Type Mismatch`; Auswahl und `Weiter` reagierten nicht zuverlässig auf den gerade geänderten Checkboxzustand. Auf der Bereit-Seite blieb außerdem `Weiter` statt `Installieren` stehen. | `FAIL`; der Kandidat ist `superseded`. Die Voraussetzungenliste verwendete das allgemeine Listenauswahl-Ereignis statt `OnClickCheck`, und `CurPageChanged` überschrieb Innos Bereit-Seiten-Beschriftung. | G2 bis G5 werden geöffnet. Der Nachfolger benötigt Checkbox-, Pflichtplan-, Download- und zweisprachige Bereit-Seiten-UI-Regressionen; G5 bleibt bis zum exakten Clean-VM-Lauf `HOLD`. |
| WIN11-SETUP-001 | Der weiterhin gemeldete `Type Mismatch` war nicht eindeutig einem Build zuzuordnen, weil mehrere VM-/Download-Kopien denselben Dateinamen trugen. Zusätzlich verwendeten importierte WinAPI-Funktionen Pascal `Boolean` statt Windows `BOOL`; dieser Pfad wird insbesondere beim Docker-Recheck aktiv. | `RESOLVED` im automatisierten G4-Umfang für `PLwC-Setup-0.2.0-rc18.dev9-installer-r3.exe`, SHA256 `E2CCE9A263607DCA152A338D2A9251739B6AA6C3952A4FC924F03D20AC19BB3F`. Native Signaturen und Record-Initialisierung sind korrigiert; fünf EXE-Fixtures liefen ohne Runtime-Fehler. | G2 bis G4 sind erneut verifiziert. G5 bleibt `HOLD`, bis echte Python-, Node- und Docker-Installationen samt Neustart gegen exakt diesen Hash in der Clean-VM abgeschlossen sind. |
| WIN11-SETUP-002 | `installer-r3` scheiterte nach erfolgreichem Python-Download und SHA-256-Prüfung, aber vor dem Start des Python-Installers mit `Type Mismatch`. Der Logdateiname rief `GetDateTimeString` mit zwei leeren Strings auf, obwohl Pascal Script dort einzelne `Char`-Werte verlangt. Der `finally`-Block überschrieb zusätzlich die Ursprungsphase mit „Abschließende Prüfung“. | `RESOLVED` im automatisierten G4-Umfang für `PLwC-Setup-0.2.0-rc18.dev9-installer-r4.exe`, SHA256 `C9E09004AEE95235B8CFA9D81DBD2E5D5B6018291827A1ED03E10105FAC11801`. Die Trenner sind dokumentationsgemäß `#0`; das geschützte Download-Gate erreicht Logpfad- und Parametererzeugung ohne Fremdinstallation. | G2 bis G4 sind erneut verifiziert. G5 bleibt `HOLD`, bis echte Python-, Node- und Docker-Installationen samt Neustart gegen exakt diesen Hash in der Clean-VM abgeschlossen sind. |
| WIN11-SETUP-003 | `installer-r4` meldete nach der Installation der Pythonmodule Exitcode `0`, erkannte die PLwC-Laufzeit danach aber weiterhin nicht. Die kombinierte Importprüfung nannte weder das fehlerhafte Modul noch eine native DLL-Ursache; die für ONNX Runtime erforderliche Microsoft-Visual-C++-Laufzeit wurde nicht verwaltet. | `RESOLVED` im automatisierten G4-Umfang für `PLwC-Setup-0.2.0-rc18.dev9-installer-r5.exe`, SHA256 `B9EEA7BED206D58BACD5220CC286BBCA69E0E694E83E615FE9B1C00747E30624`. Setup installiert die gepinnte VC++-Laufzeit, hält einen absoluten Pythonpfad fest, importiert vier Module einzeln mit Traceback und repariert VC++ höchstens einmal. | Installer-Verträge `49/49`, Bridge `19/19`, Extension `88/88`, Gateway `12/12`, geschützte Auswahlmatrix sowie sichere DE/EN-Produktionsläufe sind `PASS`. G5 bleibt `HOLD`, bis die echte Fremdinstallation samt UAC und Neustart gegen exakt diesen Hash auf Clean Windows 11 abgeschlossen ist. |

### 3.4 Defaultwerte

| Feld | Default |
| --- | --- |
| App root | `%APPDATA%\PLwC\app` |
| Gateway runtime | `%APPDATA%\PLwC\app\gateway` |
| Chat Bridge | `%APPDATA%\PLwC\app\bridge` |
| Workspace | `%APPDATA%\PLwC\workspace` |
| Profiles | `%APPDATA%\PLwC\profiles` |
| Global config | `%APPDATA%\PLwC\config` |
| Global state | `%APPDATA%\PLwC\state` |
| Global logs | `%APPDATA%\PLwC\logs` |
| Profile backups | `%APPDATA%\PLwC\profile_backups` |
| Active profile | `default` |
| Security config | leer |
| Memory / Persona / Temperament threshold | `2` / `3` / `2` |
| Qdrant | `false` |
| Persona layer | Claude: aktiviert; lokale STDIO-Ziele: konservativ deaktiviert; Bridge: importierter Claude-Wert oder gemeinsamer Installerwert |

Die konkreten Environment-/MCPB-Schluessel entsprechen
`docs/WINDOWS_INSTALLER_PLAN.md`. Jede spaetere Defaultaenderung ist eine
Anforderungsveraenderung und oeffnet G0, G1 sowie die betroffenen rechten Gates
erneut.

## 4. Evidenzstandard

Alle Gate-Nachweise liegen unter `installer/windows/evidence/G0` bis `G6`.
Diese Verzeichnisse sind Verifikationsartefakte im Repository, gehoeren aber
nicht automatisch in den oeffentlichen Installerpayload.

Jeder Testnachweis MUSS enthalten: Commit-ID, Installer-Version, EXE-SHA256,
Datum in UTC, Windows-Version, Ausfuehrender/Agent, Vorbedingungen,
Testschritte oder Befehl, Soll, Ist, Ergebnis `PASS|FAIL|BLOCKED` und Verweise
auf Logs/Screenshots. Maschinen- und Benutzernamen sowie lokale absolute Pfade
werden vor dem Commit redigiert.

Vorgesehene Evidenzdateien:

| Gate | Pflichtdateien |
| --- | --- |
| G0 | `G0/requirements-review.md`, `G0/traceability.csv`, `G0/open-decisions.md` |
| G1 | `G1/architecture-review.md`, `G1/payload-boundary.md`, `G1/threat-review.md` |
| G2 | `G2/test-plan.md`, `G2/component-matrix.csv`, `G2/rollback-plan.md` |
| G3 | `G3/build-report.md`, `G3/artifact-manifest.json`, `G3/SHA256SUMS`, `G3/licenses-report.md` |
| G4 | `G4/static-and-unit-results.md`, `G4/selection-matrix-results.csv`, `G4/prerequisite-matrix-results.csv`, `G4/ui-layout-and-localization-results.md`, `G4/payload-scan.md` |
| G5 | `G5/windows-system-results.md`, `G5/client-smoke-results.md`, `G5/ui-acceptance.md`, `G5/reboot-reconnect.md`, `G5/uninstall-upgrade.md` |
| G6 | `G6/release-review.md`, `G6/known-limitations.md`, `G6/release-notes.md`, `G6/go-no-go.md` |

Fuer PLwC Personal sind zusaetzlich verpflichtend:

| Gate | Personal-Pflichtdateien |
| --- | --- |
| G0 | `G0/personal-release-baseline.md`, `G0/personal-distribution-decision.md` |
| G1 | `G1/personal-license-boundary.md`, `G1/personal-distribution-design.md` |
| G2 | `G2/personal-delta-test-plan.md`, `G2/personal-impact-matrix.csv`, `G2/personal-test-cases.csv`, `G2/personal-test-environments.md`, `G2/personal-rollback-test-plan.md`, `G2/personal-g2-exit-review.md` |
| G3 | `G3/personal-artifact-manifest.json`, `G3/THIRD_PARTY_NOTICES.txt`, `G3/personal-runtime-images.json` |
| G4 | `G4/personal-metadata-results.md`, `G4/personal-supply-chain-results.md` |
| G5 | `G5/personal-delta-acceptance.md` |
| G6 | `G6/publication-plan.md`, `G6/publication-verification.md` |

## 5. V-Modell-Gates

### G0 - Anforderungsbaseline

**Entry-Kriterien**

- Nutzerziele und alle normativen Quelldokumente sind verfuegbar.
- Bekannte Bestandsartefakte und offene Installerideen sind inventarisiert.

**Verifikation**

- A-REQ prueft UR-001 bis UR-016 sowie PR-001 bis PR-009 auf Eindeutigkeit, Testbarkeit und
  Widerspruchsfreiheit.
- A-SEC prueft SR-001 bis SR-011 gegen Installations-, Beta-, Bridge- und
  Container-Supply-Chain-Grenzen.
- Jede Anforderung besitzt mindestens eine Verifikationsmethode und ein
  spaeteres Gate in der Traceability-Matrix.

**Exit-Kriterien**

- Anforderungen, Defaults, Nicht-Ziele und offene Entscheidungen sind reviewed.
- Fuer Personal sind Produktidentitaet, Lizenzgrenze, Versionsvertrag,
  Distributionskanaele und Signaturstatus ausdruecklich entschieden.
- Es gibt keine offene Entscheidung, die EXE-Technik, Payloadgrenze,
  Komponentenverhalten oder Security-Modell grundlegend veraendert.
- `requirements-review.md` und `traceability.csv` sind `PASS`.

**Stop/Go**

- **STOP**, wenn eine Nutzeranforderung fehlt, zwei Quellen unaufgeloest
  kollidieren oder ein Abnahmekriterium nicht beobachtbar ist.
- **GO zu G1** nur mit vollstaendiger UR-/SR-Baseline.

### G1 - Architektur- und Sicherheitsdesign

**Entry-Kriterien**

- G0 ist `GO`.
- Zielplattform und EXE-Builder sind festgelegt; fuer den ersten Windows-Build
  ist Inno Setup die Referenz, sofern eine begruendete Designentscheidung es
  nicht ersetzt.

**Verifikation**

- Review des manifestgetriebenen Komponentendesigns und der Abhaengigkeit
  `alle optionalen Ziele -> ein erforderlicher Gateway-Kern`.
- Review eines komponentenabhaengigen Prerequisite-Resolvers mit eindeutigen
  Detection-Probes, Statusmodell und Block-/Warnreaktion gemaess UR-008.
- Review des digest-fixierten GHCR-Akquisitions-, Manifest-, Probe-,
  Diagnose- und Safe-Mode-Designs gemaess UR-015, UR-016 und SR-011.
- Fuer Personal Review der Lizenzgrenze je Artefakt, der privaten Staging-
  und oeffentlichen Distributionskanaele, des credentialfreien anonymen Pulls,
  des Personal-Updatevertrags und der kanalweisen Ruecknahme gemaess PR-001 bis
  PR-007.
- Review der Custom-Page-Aufteilung fuer `1366x768`, semantischer Controls und
  zentraler deutscher/englischer String-Ressourcen gemaess UR-009/UR-010.
- Review von Installations-, Update-, Repair-, Rollback- und Uninstall-Fluss.
- Threat Review fuer Registry, Hostkonfiguration, Extension-ID, Native
  Messaging, Loopback-Port, Payloadfilter und Logredaktion.
- Review, dass die EXE der einzige nutzerseitige Installer-Einstieg ist.
  Interne Skripte sind nur zulaessig, wenn sie durch die EXE gekapselt,
  gehasht und niemals als manueller Installationsschritt verlangt werden.

**Exit-Kriterien**

- Komponentenmanifest, Verzeichnisvalidierung, Config-Mapping und Besitz jeder
  geschriebenen Datei/jedes Registry-Werts sind spezifiziert.
- Python-/`mcp`-, Claude-, Node-/Browser-, Codex-/Odysseus- und Docker-Probes
  sowie deren UI-, Preview- und Summary-Ausgaben sind spezifiziert.
- Opt-in, Hersteller-/Registry-URLs, Versionen, SHA-256/Digests,
  Abbruch-/Fehlerverhalten und erneute Prüfung für Python, Node.js, Docker und
  die drei PLwC-Runtime-Images sind spezifiziert.
- Jede Installer-Seite, jeder Boolean-Control und jeder sichtbare String besitzt
  ein Layout-/Lokalisierungsdesign fuer Deutsch und Englisch.
- Codex-/Odysseus-Schreibstrategie folgt SR-004.
- Chat-Bridge-Design erfuellt SR-003 und UR-006.
- Payload-Allowlist und Privacy-Denylist sind freigegeben.
- Personal-Lizenzinventar, Drittanbietergrenze, Releasekanal- und
  Update-Trust-Design sind freigegeben.

**Stop/Go**

- **STOP** bei mehr als einem Gateway, remote gebundener Bridge, unbekannter
  Hostkonfigurationsmutation, fehlendem Rollback, manueller PS1-Pflicht oder
  fehlender/uneindeutiger Block-/Warnlogik fuer UR-008/UR-015, unvollstaendiger
  Fehlerdiagnose nach UR-016, nicht aufgeteiltem ueberhohem Formular oder
  unvollstaendigem Sprachressourcenmodell.
- **GO zu G2** nach A-ARCH- und A-SEC-Freigabe.

### G2 - Implementierungs- und Verifikationsfreigabe

**Entry-Kriterien**

- G1 ist `GO`.
- Alle Designobjekte besitzen verantwortliche Module und Tests.

**Verifikation**

- A-TEST leitet fuer jede Traceability-Zeile konkrete Testfaelle ab.
- `component-matrix.csv` enthaelt alle 16 Auswahlmasken fuer Claude, Codex,
  Odysseus und Bridge, inklusive `0000` (nur Gateway) und `1111` (alles).
- Negative Tests decken Pfadueberlappung, Python fehlt/zu alt, fehlende
  Laufzeitimporte (`mcp`, `fastembed`, `qdrant_client`)
  schlaegt fehl, Claude fehlt, Node.js fehlt/zu alt, Browser fehlt, Codex fehlt,
  Odysseus fehlt, Docker CLI/Daemon/Image fehlt, manipulierte Hashes, unbekannte
  Hostschemas, ungueltige Extension-ID, belegten Port, Installationsabbruch und
  Rollback ab.
- Akquisitionstests decken Standard-aus, explizites Opt-in, offizielle HTTPS-
  Quellen, manipulierte Hashes, DNS-/Proxyfehler, Installations- und UAC-Abbruch,
  erneute Prüfung, die explizite Node.js-Installation sowie das Verbot
  automatischer Claude-/Browser-Installation ab.
- Image-Akquisitionstests decken je Image fehlend/vorhanden/falscher Digest,
  anonymen GHCR-Pull, Tag-only-Verbot, Teilfehler, Timeout, Abbruch,
  idempotente Wiederholung, netzwerklose Probes und Safe-Mode-Fallback ab.
- Diagnosetests decken erwartete und unerwartete Child-/Python-Ausnahmen,
  vollständige Reportpersistenz und den Diagnoseexport ab.
- UI-Tests decken jede Standard-/Custom-Seite bei `1366x768` in Deutsch und
  Englisch ab, inklusive laengster dynamischer Prerequisite-/Fehlertexte,
  Checkbox-Zustaende, Vor/Zurueck-Navigation und Abschlussseite.
- Starttests decken die sichtbare Sprachauswahl, Windows-Sprachfallback,
  `/LANG` sowie den Neustart als Administrator mit bewahrter Auswahl ab.
- Groessentests decken Payloadmanifest, einzelne Downloads, Summen,
  `unknown`/`variable` und unzureichenden freien Speicher ab.
- Clean-VM-, Reboot-, Upgrade-, Repair- und Uninstall-Umgebungen sind definiert.
- Fuer Personal ordnet `personal-impact-matrix.csv` jede bestehende Evidenz
  genau `REUSE`, `TARGETED-RERUN` oder `FULL-RERUN` zu und begruendet die
  Entscheidung mit Quellmodulen, Buildinputs, Abhaengigkeiten, Konfigurationen
  und Claims.

**Exit-Kriterien**

- Jeder MUSS-Satz ist mindestens einem Testfall zugeordnet.
- Erwartete Evidenzdateien, Testdaten und Redaktionsregeln sind festgelegt.
- Jeder PR-MUSS-Satz ist mindestens einem automatisierten oder manuellen
  Nachweis und einem verantwortlichen Gate zugeordnet.
- Das Testdesign inventarisiert alle sichtbaren String-IDs und ordnet ihnen
  deutsche und englische Erwartungswerte zu.
- Keine kritische Funktion ist ausschliesslich durch manuelle Sichtpruefung
  abgedeckt, sofern sie automatisierbar ist.

**Stop/Go**

- **STOP**, wenn eine UR/SR ohne Test, eine Auswahlmaske ohne Erwartungswert
  oder ein destruktiver Test ohne disposable Umgebung verbleibt.
- **GO zur Implementierung/G3** nach A-TEST-Freigabe.

### G3 - Code Complete und reproduzierbarer Kandidat

**Entry-Kriterien**

- G2 ist `GO`.
- Implementierung, Tests und Builddefinition liegen im PLwC-Repository.

**Verifikation**

- Build aus sauberem Checkout ohne privaten zweiten Sourcepfad.
- Erzeugung einer versionierten Setup-EXE sowie Manifest, SHA256, Dateiliste
  und Lizenzbericht.
- Fuer Personal Erzeugung der Storepakete, Personal-Lizenzdateien,
  Drittanbieterhinweise, des Personal-Release-Manifests und dreier neu gebauter
  Runtime-Images aus demselben eingefrorenen Quellcommit.
- Zwei reproduzierbare Builds jedes Runtime-Images mit identischem Digest sowie
  SBOM, Lizenzinventar, Schwachstellenbericht und Provenienz.
- Zweiter Build in frischer Umgebung; Hashgleichheit oder vollstaendig
  erklaerte, kontrollierte Abweichung wird dokumentiert.
- Statische Suche nach privaten Pfaden, Secrets, `@latest`, Tag-only-
  Imagereferenzen, verbotenen Servern und nicht gepinnten Payloadquellen.

**Exit-Kriterien**

- Die EXE startet, zeigt Version und Komponenten korrekt und besitzt einen
  dokumentierten Signaturstatus.
- Die EXE zeigt die Voraussetzungen der aktuellen Auswahl vor jedem Schreiben
  und kann keinen durch UR-008 blockierten Installationsplan ausfuehren.
- Die EXE enthaelt vollstaendige deutsche und englische Ressourcen; ein
  automatisierter String-Check findet keine fehlende Uebersetzung.
- Alle Payloadteile stammen aus diesem Checkout oder aus gepinnten,
  hashgeprueften Abhaengigkeiten.
- Das buildgenerierte Runtime-Image-Manifest bindet logischen Namen, Plattform,
  Version, GHCR-Repository, Digest, Groesse, SBOM und Provenienz eindeutig.
- PLwC-eigene produktive Metadaten nennen weder Apache-2.0 noch eine alte
  r22-r27-Downloadquelle; historische und Drittanbieter-Hinweise bleiben
  davon unberuehrt und muessen erhalten sein.
- Build- und Packagingbefehle sind wiederholbar und liefern keine
  ungefilterten privaten Inhalte.

**Stop/Go**

- **STOP** bei fehlender EXE, Hashfehler, unerklaerter Buildabweichung,
  privatem Payloadinhalt, unlizenzierter Datei oder unpinnter Netzabhaengigkeit.
- **GO zu G4** fuer genau den in `artifact-manifest.json` fixierten Kandidaten.

### G4 - Komponentenverifikation

**Entry-Kriterien**

- G3 ist `GO`; EXE-SHA256 und Testkandidat sind eingefroren.
- Unit-/Integrationstestumgebung ist sauber und reproduzierbar.

**Verifikation**

- Static-, Unit-, Contract- und Installer-Logiktests sind `PASS`.
- Alle 16 Auswahlmasken werden mindestens automatisiert installiert,
  inventarisiert und deinstalliert; nicht gewaehlte Komponenten duerfen keine
  Hostregistrierung oder Laufzeitdateien hinterlassen.
- Default- und Override-Pfade, Preview ohne Seiteneffekt, Backup, Rollback,
  Repair, Upgrade und Uninstall werden geprueft.
- Auf einer Clean-Windows-11-Umgebung werden alle UR-008-Fehlzustaende einzeln
  und kombiniert geprueft. Blockierte Ziele schreiben nichts; fehlende
  Codex-/Odysseus-Clients erzeugen nur als `prepared` bezeichnete Snippets;
  fehlendes Docker erscheint in Preview und Summary mit
  `safe_mode_expected=true`.
- Die drei Image-Akquisitionspfade bestehen die UR-015-Matrix; ein Pull ohne
  anschliessenden digestgebundenen Realprobe ist kein Erfolg.
- Jeder UR-016-Fehlerpfad schreibt einen vorhandenen, exportierbaren Bericht
  mit redigiertem stdout/stderr und eindeutigem Exitcode.
- Alle Seiten werden fuer Deutsch und Englisch bei `1366x768` per Screenshot
  und Control-Bounds geprueft. Kein Control liegt ausserhalb des Clientbereichs
  oder hinter der Navigationsleiste; Boolean-Werte sind Checkboxen.
- Der erste interaktive Dialog zeigt die Sprachauswahl; die feste
  Navigationsschaltflaeche bleibt `Weiter`/`Next` und enthaelt keinen langen
  dynamischen Aktionsstatus.
- Rechte-, UAC-, MSI-Exitcode-, Log- und Free-Space-Fehlerpfade werden durch
  Fault Injection geprueft, bevor reale Zusatzprogramme gestartet werden.
- Gateway- und Bridge-Contracts pruefen Servername, exakt acht Tools,
  Loopbackbindung, erlaubte Extension-Origin, einen Child und Bestaetigungslogik.
- Payloadscan prueft SR-005 und SR-006.
- Personal-Contracts pruefen Produktname, Lizenzsatz, Drittanbieterhinweise,
  Komponenten- und Storeversionen, Setup-/Support-/Privacy-URLs,
  Update-Endpunkt und das Verbot eingebetteter Registry-Credentials.
- Die Personal-Images bestehen OCI-Label-, SBOM-, Lizenz-, Provenienz-,
  Schwachstellen-, Secret- und Digestpruefung. Private Staging-Pakete duerfen
  nicht anonym erreichbar sein.

**Exit-Kriterien**

- Alle automatisierbaren Tests sind `PASS`; kein flakey oder uebersprungener
  MUSS-Test bleibt offen.
- Die Prerequisite-Matrix ist fuer jede Komponentenauswahl und jeden
  Fehlzustand `PASS`; eine reine Payloadkopie gilt nicht als erfolgreicher
  Komponenten-Smoke.
- Layout-/Lokalisierungsmatrix ist fuer beide Sprachen und alle Seiten `PASS`;
  kein abgeschnittener Text, verdecktes Control, editierbares Boolean-Textfeld
  oder fehlender/gemischter Installertext bleibt offen.
- Auswahlmatrix und Dateisystem-/Registry-Differenzen entsprechen dem Manifest.
- Fehlerfaelle enden ohne falsch-positive Erfolgsmeldung und ohne unerklaerte
  Reste.

**Stop/Go**

- **STOP** bei jedem UR-/SR-Fehler, falsch-positiver Prerequisite-Erkennung,
  Installation eines blockierten Ziels, fehlender Prepared-/Safe-Mode-Warnung,
  Clipping bei `1366x768`, falschem Boolean-Control, fehlender Uebersetzung,
  Sprachmischung, unbekannter Registry-/Dateiaenderung, doppeltem Gateway,
  Toolcount ungleich acht oder Privacy-Fund.
- **GO zu G5** nach unabhaengiger A-TEST/A-SEC-Gegenpruefung.

### G5 - Systemvalidierung und Nutzerabnahme

**Entry-Kriterien**

- G4 ist `GO`.
- Clean Windows VM sowie die jeweils beanspruchten realen Clients/Browser sind
  mit dokumentierten Versionen verfuegbar.

**Verifikation**

- Nutzerfluss per Doppelklick: Defaults, Overrides, Prerequisite-Status,
  Abbruch vor Bestaetigung, Installation und Abschlussseite ohne manuelle
  PowerShell-Eingabe.
- Derselbe Nutzerfluss wird bei `1366x768` vollstaendig in Deutsch und Englisch
  durchlaufen, einschliesslich Warnung, Fehler, Prepared-/Safe-Mode-Text und
  Abschlussseite.
- Live-Smokes fuer Gateway-only, jede einzelne optionale Komponente und
  `alles`; weitere Kombinationen werden risikobasiert aus G4 wiederholt.
- Auf mindestens einem sauberen Windows-11-System ohne lokale PLwC-Images wird
  der anonyme GHCR-Pfad per Opt-in vollständig durchlaufen; danach bestehen
  Document Worker, Python Runner und Node Runner reale Operationen offline mit
  `--pull never`.
- Fuer Personal-Pakete, die gemaess PR-005 bis `GO-PUBLISH` privat bleiben,
  wird dieser G5-Lauf gegen dieselben finalen Repositorynamen und Digests mit
  einer ausschliesslich auf dem disposable Testhost vorhandenen GHCR-Anmeldung
  ausgefuehrt. Der Installer erhaelt keine Credentials. Der anonyme Clean-
  Install samt drei Runtime-Operationen wird zwingend nach `GO-PUBLISH` in G6
  wiederholt und blockiert bis dahin `GO-FINAL`.
- Ein direkter r26→r27-Lauf reproduziert die Ausgangslage
  `worker_missing`, beendet den Preflight ohne Diagnoseverlust und bewahrt
  Profile sowie Workspace bytegleich.
- Claude: ein `plwc-gateway`, acht Tools, verifizierter MCPB-Hash.
- Codex/Odysseus: je ein STDIO-Eintrag oder, bei unbekanntem Schema, korrekt
  vorbereiteter und als `prepared` gemeldeter Ausschnitt.
- Bridge: `127.0.0.1:3007`, acht Tools, sichtbarer Runtime-Status, bestaetigte
  Write/Read-Runde ohne Duplikat, Denial ohne Mutation und geschuetzter
  Governor-/Sandbox-Fluss.
- Reboot-Abnahme fuer UR-006: einmal installieren, Windows neu starten,
  Browser starten, `Status -> Reconnect`; kein erneuter Registry-Install und
  kein manuelles Startskript.
- Upgrade/Repair bewahren Nutzerdaten; Uninstall entfernt owned App- und
  Registry-Artefakte, aber keine Profile/Workspaces ohne separate explizite
  Zustimmung.
- Fuer Personal wird der G5-Umfang durch die in G2 freigegebene
  Auswirkungsmatrix bestimmt. Betroffene Pfade werden real erneut ausgefuehrt;
  uebernommene Evidenz nennt Test-ID, Ursprungscommit, unveraenderte Inputs und
  Begruendung. Mindestens Personal-Branding/Lizenztexte, Image-Erstdownload,
  alle drei Runtime-Operationen, Repair/Upgrade, Reboot/Reconnect, finaler
  Chrome-/Edge-Pfad und Update-/Offlinefehler werden erneut abgenommen.

**Exit-Kriterien**

- Alle beanspruchten Clientwege sind auf realer Zielsoftware `PASS` oder im
  Release klar als `prepared/not validated` begrenzt.
- UR-001 bis UR-016 und die fuer den Release geltenden PR-001 bis PR-009 sind
  aus Nutzersicht nachgewiesen oder durch eine freigegebene, tracebare
  Evidenzuebernahme abgedeckt.
- Keine Regression der PLwC Security-/Privacy-Grenzen ist offen.

**Stop/Go**

- **STOP** bei manuellem PS1-Zwang, fehlerhaftem Reconnect nach Neustart,
  Datenverlust, doppelter Ausfuehrung, falscher Supportbehauptung oder
  unvollstaendigem Rollback.
- **GO zu G6** nur fuer nachweislich validierte Claims.

### G6 - Release Acceptance

**Entry-Kriterien**

- G5 ist `GO`; der Kandidat wurde seit G3 nicht veraendert.
- Alle Evidenzen sind vollstaendig, redigiert und auf dieselbe EXE-SHA256
  bezogen.

**Verifikation**

- A-REL prueft Traceability, offene Fehler, Known Limitations und Claim-vs-Test.
- A-SEC wiederholt Hash-, Payload-, Privacy-, Lizenz- und Signaturstatuspruefung.
- A-REL gleicht EXE, Storepakete, Runtime-Image-Manifest und die tatsaechlich
  in privatem Staging beobachteten Digests ab. Fuer Personal wird die
  oeffentliche anonyme Pullbarkeit nach `GO-PUBLISH` als verpflichtende
  Post-Publication-Pruefung belegt.
- Release Notes nennen Dateiname, Version, SHA256, Groesse, Signaturstatus,
  Servername, Toolcount, Smoke-Nachweise, Limits, tatsaechliche Lizenzart und
  bei einem unsignierten Release den Hinweis auf den unbekannten
  Windows-Herausgeber.
- Oeffentlicher Installerpayload wird gegen die Allowlist geprueft; das eine
  Entwicklungsrepository wird nicht ungefiltert zum Releasepayload erklaert.
- Fuer Personal werden Root-Lizenz, Personal-Freigaben, Drittanbieterhinweise,
  OCI-Lizenzlabels, oeffentlicher Quellstand, Website, Update Center und
  Storetexte gegen denselben eingefrorenen Produktvertrag geprueft.

**Exit-Kriterien**

- `go-no-go.md` nennt Entscheidung, Entscheider, EXE-SHA256 und alle
  Runtime-Image-Digests sowie alle zugelassenen Produktclaims.
- `go-no-go.md` fuehrt fuer Personal getrennt `GO-PUBLISH` und `GO-FINAL`.
  `publication-verification.md` belegt nach `GO-PUBLISH` anonyme Source-,
  Installer-, Hash-, GHCR-, Website-, Update- und Storepruefungen.
- Keine offene Severity-1/2-Abweichung und keine offene Security-, Privacy-
  oder Integritaetsabweichung.
- Eine unsignierte Final-/Stable-Freigabe ist nur nach ausdruecklicher,
  dokumentierter Product-Owner-Entscheidung zulaessig und muss alle
  kompensierenden Nachweise aus SR-005 erfuellen. Sie bleibt technisch
  `NotSigned` und darf nicht als publisher-verifiziert oder
  production-certified bezeichnet werden.

**Stop/Go**

- **STOP/NO-GO** bei fehlender Evidenz, Kandidatenaenderung, Hashabweichung,
  nicht redigierten Daten, falschem Signaturclaim oder nicht reproduzierbarem
  Ergebnis. Ruecksprung zum fruehesten betroffenen Gate.
- **GO** nur fuer den exakt gehashten und dokumentierten Kandidaten. Ein
  Upload darf nicht still ersetzt und ein Beta-Tag nicht verschoben werden.
- Ein Personal-`GO-PUBLISH` autorisiert nur die darin einzeln benannten
  externen Aktionen. `GO-FINAL` folgt erst nach bestandener
  Post-Publication-Verifikation; bis dahin bleibt der Releasezustand
  `PUBLISHED/PENDING FINAL VERIFICATION`.

## 6. Traceability-Matrix

| Anforderung | Design-/Implementierungsobjekt | Verifikationsart | Gate | Primaere Evidenz |
| --- | --- | --- | --- | --- |
| UR-001 | Inno-Setup-EXE, GUI-Fluss, gekapselte Aktionen | Buildtest, Clean-VM-Doppelklick, UI-Abnahme | G3, G5 | `G3/build-report.md`, `G5/windows-system-results.md` |
| UR-002 | Komponentenmanifest und Abhaengigkeitsaufloeser | 16er Matrix, Dateisystem-/Registry-Diff, Live-Smokes | G4, G5 | `G4/selection-matrix-results.csv`, `G5/client-smoke-results.md` |
| UR-003 | Directory-Seite und kanonische Pfadvalidierung | Default-, Override- und Negativtests | G4, G5 | `G4/static-and-unit-results.md`, `G5/windows-system-results.md` |
| UR-004 | Config-Seite, Defaults und zielbezogenes Mapping | Snapshot/Schema-Test und installierter Istvergleich | G4, G5 | `G4/static-and-unit-results.md`, `G5/client-smoke-results.md` |
| UR-005 | Repo-lokale Builddefinition und Payloadmanifest | Clean-Checkout-Build, Source-/SBOM-Pruefung | G3, G6 | `G3/artifact-manifest.json`, `G6/release-review.md` |
| UR-006 | Native-Messaging-Registrierung und Reconnect-Launcher | Reboot- und Browser-Reconnect-E2E | G5 | `G5/reboot-reconnect.md` |
| UR-007 | Preview/Commit-Transaktion und Rollback | Before/after Diff bei Abbruch und Fehler | G4, G5 | `G4/selection-matrix-results.csv`, `G5/windows-system-results.md` |
| UR-008 | Komponentenabhaengiger Prerequisite-Resolver, Statusmodell und UI-/Summary-Ausgabe | Clean-Windows-11-Negativmatrix, Probe-/Versionstests, Dateisystem-/Registry-Diff | G1, G2, G3, G4, G5 | `G1/architecture-review.md`, `G2/test-plan.md`, `G4/prerequisite-matrix-results.csv`, `G5/windows-system-results.md` |
| UR-009 | Aufgeteilte Custom Pages, Control-Bounds und Boolean-Checkboxen | `1366x768` Screenshot-/Bounds-Matrix in Deutsch/Englisch und Control-Type-Test | G1, G2, G4, G5 | `G1/architecture-review.md`, `G4/ui-layout-and-localization-results.md`, `G5/ui-acceptance.md` |
| UR-010 | Deutsche/englische String-Ressourcen und Sprachwahl | String-Inventar, Missing-Key-Test, lokalisierte Negativ- und E2E-Abnahme | G1, G2, G3, G4, G5 | `G1/architecture-review.md`, `G4/ui-layout-and-localization-results.md`, `G5/ui-acceptance.md` |
| UR-011 | Opt-in-Seite, vollständiges Vorab-Gate, einmalig konsumierte Aktionen, lokalisierte Warteseite, offizielle Downloadlinks, verifizierte Python-/Docker-Akquisition und erneuter Probe | Statische Reihenfolgeverträge, simulierte Negativmatrix und Clean-VM-Abnahme einschließlich Fehler-/Neustartpfaden | G1, G2, G3, G4, G5 | `G1/architecture-review.md`, `G2/test-plan.md`, `G4/static-and-unit-results.md`, `G5/windows-system-results.md` |
| UR-012 | Inno-Sprachdialog, Windows-Sprachfallback und `/LANG` | Startdialog-, Kommandozeilen- und lokalisierter E2E-Test | G3, G4, G5 | `G4/ui-layout-and-localization-results.md`, `G5/ui-acceptance.md` |
| UR-013 | Rechtepruefung, kontrollierter erhoehter Neustart, MSI-Logging und urspruenglicher Benutzerkontext | UAC-/Exitcode-Fault-Injection und Standardbenutzer-Clean-VM | G3, G4, G5 | `G4/prerequisite-matrix-results.csv`, `G5/windows-system-results.md` |
| UR-014 | Build-generiertes Groessenmanifest, UI-Summen und Free-Space-Pruefung | Manifest-/Summen-Contract und Clean-VM-Speicher-Negativtest | G3, G4, G5 | `G3/artifact-manifest.json`, `G4/static-and-unit-results.md`, `G5/ui-acceptance.md` |
| UR-015 | GHCR-Image-Manifest, Opt-in-Seite, digestgebundene Akquisition und Realprobes | Source-/UI-Vertrag, Fake-Docker-Matrix, anonymer Clean-VM-Pull und echte Document-/Sandbox-Smokes | G1, G2, G3, G4, G5, G6 | `G1/container-image-design.md`, `G2/test-plan.md`, `G3/runtime-images.json`, `G4/image-acquisition-results.md`, `G5/windows-system-results.md` |
| UR-016 | gekapselte Prozessausfuehrung, atomare Fehlerberichte und Diagnoseexport | Exitcode-/Exception-Fault-Injection, Report-/Export-Inventar und realer r26→r27-Fehlerpfad | G1, G2, G4, G5 | `G1/diagnostic-design.md`, `G2/test-plan.md`, `G4/diagnostic-fault-results.md`, `G5/windows-system-results.md` |
| SR-001 | Ein Gateway-Core, Zieladapter, Tool-Allowlist | Contracttest und Host-Smoke | G4, G5 | `G4/static-and-unit-results.md`, `G5/client-smoke-results.md` |
| SR-002 | Pfadregeln | Property-/Negativtests und UI-Abnahme | G4, G5 | `G4/static-and-unit-results.md`, `G5/windows-system-results.md` |
| SR-003 | Bridge-Listener, Origincheck, Child-Lifecycle, Policy | Contract-, Security- und Browser-E2E | G4, G5 | `G4/static-and-unit-results.md`, `G5/client-smoke-results.md` |
| SR-004 | Host-Detector, Schema-Adapter, Backup, `prepared`-Fallback | Versionsmatrix und unbekanntes-Schema-Test | G4, G5 | `G4/selection-matrix-results.csv`, `G5/client-smoke-results.md` |
| SR-005 | Buildmanifest, Hash, SBOM, Signaturstatus | Zwei Builds, Hash-/Release-Review | G3, G6 | `G3/SHA256SUMS`, `G6/release-review.md` |
| SR-006 | Payloadfilter und Logredaktion | Secret-/Pfadscan, manuelle Gegenpruefung | G3, G4, G6 | `G4/payload-scan.md`, `G6/release-review.md` |
| SR-007 | Transaktion, Rollback, owned-artifact inventory | Fault Injection, Upgrade/Repair/Uninstall | G4, G5 | `G4/selection-matrix-results.csv`, `G5/uninstall-upgrade.md` |
| SR-008 | Docker-Prerequisite-Checker, Warnung und persistierte Safe-Mode-Erwartung | Missing-CLI/Daemon/Image-Negativtests und Preview-/Summary-Abnahme | G4, G5 | `G4/static-and-unit-results.md`, `G5/windows-system-results.md` |
| SR-009 | Gepinnte offizielle HTTPS-Downloads, SHA-256-Prüfung und Opt-in-Grenze | Source-Contract, Hash-Fehler und Silent-Negativtest | G3, G4, G5 | `G3/artifact-manifest.json`, `G4/static-and-unit-results.md`, `G5/windows-system-results.md` |
| SR-010 | Bewahrter urspruenglicher Benutzerkontext bei Erhoehung | Standardbenutzer-/Alternativkonto-Dateisystem- und Registry-Diff | G4, G5 | `G4/prerequisite-matrix-results.csv`, `G5/windows-system-results.md` |
| SR-011 | digest-gepinnte reproduzierbare GHCR-Images, OCI-Metadaten, SBOM, Scan und Provenienz | Zwei-Build-Digestvergleich, Manifest-/Policy-Test, anonymer Pull und Releaseabgleich | G1, G2, G3, G4, G5, G6 | `G1/threat-review.md`, `G3/runtime-images.json`, `G3/image-build-report.md`, `G4/image-security-results.md`, `G6/release-review.md` |
| PR-001 | Personal-Lizenzinventar je Artefakt und getrennte Drittanbieterhinweise | Metadaten-, Payload- und Lizenzscan | G0, G1, G3, G4, G6 | `G0/personal-release-baseline.md`, `G1/personal-license-boundary.md`, `G4/personal-metadata-results.md`, `G6/release-review.md` |
| PR-002 | Produkt-/Versionsvertrag und monotone Storeversionen | Schema-, Buildidentity-, UI- und Storepaket-Vertrag | G0, G3, G4, G5 | `G0/personal-release-baseline.md`, `G3/personal-artifact-manifest.json`, `G5/personal-delta-acceptance.md` |
| PR-003 | unveraenderliche offizielle Releaseeinheit | Hash-, Groessen-, Notice- und Release-Review | G3, G6 | `G3/personal-artifact-manifest.json`, `G3/SHA256SUMS`, `G6/go-no-go.md` |
| PR-004 | oeffentlicher Personal-Quellstand mit historischer Lizenzgrenze | Repository-, Archiv- und Lizenzreview | G1, G4, G6 | `G1/personal-license-boundary.md`, `G4/personal-metadata-results.md`, `G6/publication-verification.md` |
| PR-005 | credentialfreie, digestfixierte Personal-Runtime-Distribution | Secretscan, Image-Supply-Chain-Test, Clean-VM-Pull und Post-Publication-Probe | G1, G3, G4, G5, G6 | `G1/personal-distribution-design.md`, `G3/personal-runtime-images.json`, `G5/personal-delta-acceptance.md`, `G6/publication-verification.md` |
| PR-006 | Personal-konsistente Chrome-/Edge-Pakete | Storevertrag, Paketinspektion und Browser-E2E | G3, G4, G5, G6 | `G3/personal-artifact-manifest.json`, `G4/personal-metadata-results.md`, `G5/personal-delta-acceptance.md` |
| PR-007 | getrennte externe Kanal-Freigaben | Freigabematrix und kanalweise Ausfuehrungsprotokolle | G0, G6 | `G0/personal-distribution-decision.md`, `G6/publication-plan.md`, `G6/publication-verification.md` |
| PR-008 | begruendete Evidenzwiederverwendung | Impact-Matrix und gezielte Wiederholung | G2, G5, G6 | `G2/personal-impact-matrix.csv`, `G5/personal-delta-acceptance.md`, `G6/release-review.md` |
| PR-009 | getrenntes GO-PUBLISH und GO-FINAL | Vorabreview und anonyme Post-Publication-Pruefung | G6 | `G6/go-no-go.md`, `G6/publication-verification.md` |

## 7. Globale Stop-/Go-Regeln

1. Jede Code-, Payload- oder Defaultaenderung nach G3 invalidiert den
   eingefrorenen Kandidaten und mindestens G3 bis G6.
2. Eine Anforderungsaenderung springt zu G0 zurueck; eine Designaenderung
   mindestens zu G1; eine neue Teststrategie mindestens zu G2.
3. Security-, Privacy-, Integritaets-, Datenverlust- und Governance-Fehler sind
   nicht waiver-faehig.
4. Eine nicht sicher reproduzierbare Abweichung ist `FAIL`, nicht `BLOCKED`.
5. `BLOCKED` ist nur zulaessig, wenn eine externe Voraussetzung fehlt und kein
   Produktfehler beobachtet wurde. Ein blockierter MUSS-Test verhindert GO.
6. Nicht validierte Clientversionen oder Integrationswege werden nicht als
   unterstuetzt behauptet; sie duerfen klar als `prepared` dokumentiert werden.
7. Jede GO-Entscheidung nennt exakt Commit-ID und EXE-SHA256. Ein neuer Hash
   ist ein neuer Kandidat.
8. GHCR-Push, öffentliche Image-Sichtbarkeit, endgültiger Produktionsbuild und
   Veröffentlichung sind getrennte Freigaben und dürfen nicht aus einem
   vorherigen Gate-GO abgeleitet werden.
9. Fuer PLwC Personal ist ein bestehendes Apache-2.0-Image mit unveraendertem
   Digest nur Migrations-/QA-Evidenz. Es darf nicht durch Umbenennen oder
   Umtaggen zum Personal-Releaseartefakt erklaert werden.
10. `GO-PUBLISH` und `GO-FINAL` sind getrennt. Bis alle anonymen
    Post-Publication-Pruefungen bestanden sind, darf ein veroeffentlichter
    Kandidat nicht als final verifiziert bezeichnet werden.
