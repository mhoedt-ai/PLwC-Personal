# PLwC Personal – Produkt- und Metadatenvertrag

Stand: 3. Oktober 2026. Status: **G0-Produktvertrag bestätigt; lokale
G3-Implementierung geprüft**;
Releasefreigabe ausstehend.

| Feld | Verbindlicher Wert |
| --- | --- |
| Sichtbarer Produktname und erste offizielle Releasebezeichnung | `PLwC Personal` |
| Technische Produktversion | `1.0.0` |
| Technischer Git-Releasetag | `v1.0.0` |
| Sichtbarer Windows-Setupname / technische Produktversion / Authenticode | `PLwC installer` / `1.0.0` / `NotSigned` |
| Interne Installer-Quellrevision | `installer-r27`; keine sichtbare Produktversion |
| Bridge-Protokoll / nächste Chrome- und Edge-Paketversion | `1.0.0` / `2.0.0` |
| Personal-Quellrepository | `https://github.com/mhoedt-ai/PLwC-Personal` |
| Personal-Releaseübersicht | `https://github.com/mhoedt-ai/PLwC-Personal/releases` |
| Personal-Update-Manifest | `https://github.com/mhoedt-ai/PLwC-Personal/releases/latest/download/plwc-personal-release-manifest.json` |
| PLwC-eigene Lizenz in technischen Metadaten | `LicenseRef-PLwC-Personal-1.0` |
| Browser-Store-Anzeigename | `PLwC Personal Chat Bridge` |

`LicenseRef-PLwC-Personal-1.0` bezeichnet ausschließlich PLwC-eigene
Bestandteile dieser Linie. Der maßgebliche Text besteht aus `LICENSE`,
`PERSONAL_USE_PERMISSION.md` und `OFFICIAL_REDISTRIBUTION_PERMISSION.md`.
Fremdkomponenten behalten ihre eigenen Lizenzen. Die historische Apache-2.0-
Linie behält ihre bereits eingeräumten Rechte; ihre Evidenz und Archive werden
nicht umetikettiert.

Alle PLwC-eigenen Komponenten beginnen in der Personal-Linie technisch bei
`1.0.0`; die Browser-Store-Pakete sind wegen der bestehenden Store-IDs und
früherer Einreichungen die Ausnahme und erhalten `2.0.0`. Drittanbieter-
Versionen werden dadurch nicht umbenannt. Gateway, Bridge und Native Launcher
tragen `1.0.0`; die Runtime-Buildquellen und ihre aktuellen Verträge sind
ebenfalls auf `1.0.0` umgestellt. Die Extension-Quelle und ihre Paketverträge
tragen `2.0.0`. Bestehende Images und Store-ZIPs mit `0.1.0` beziehungsweise
`1.0.4` sind historische Kandidaten. Reproduzierte Personal-Artefakte aus einem
sauberen Publikationscommit wurden noch nicht erzeugt. Der Wert
`components.browserExtension=1.0.0` in der Bridge-Buildidentität bezeichnet
die kompatible Bridge-Protokollversion. Die Store-Paketversion wird separat
aus Extension-Paket und Manifest gebunden; der Installer-Build prüft beide
Verträge. Die endgültige Paketversion und ihre Artefakt-Hashes werden mit dem
G3-Kandidaten eingefroren.
Die Store-Dashboards zeigten am 27.09.2026 jeweils `1.0.1` als aktuellen
Entwurf. Das Einreichungsprotokoll hält fest, dass die lokalen Zwischenstände
`1.0.2` und `1.0.3` nicht eingereicht wurden. Der Product Owner legte am
30.09.2026 `2.0.0` als nächste gemeinsame Chrome-/Edge-Paketversion für die
bestehenden IDs fest. Nach erneuter Anmeldung wurden am 03.10.2026 beide
privaten Dashboards gelesen: Chrome zeigt `1.0.1` mit dem Status
„Bereit zur Veröffentlichung vor dem 07.10.2026“, Edge zeigt `1.0.1` als
`In draft` / `Hidden`. Die geplante `2.0.0` liegt in beiden Fällen höher.
Nachweis: `installer/windows/evidence/G3/personal-store-version-check-20261003.md`.
Vor der tatsächlichen Einreichung wird der Stand erneut geprüft.
Dies ist noch keine Storeeinreichung oder
Freigabe des Personal-Releasekandidaten. Store-IDs und Native-Messaging-Origins
bleiben stabil.

Der Installer behält für Upgrade/Repair seine technische `AppId`, sein
Installationsverzeichnis und vorhandene Datenpfade. Der sichtbare Setupname
wird `PLwC installer`; der Produkt- und Uninstall-Eintrag wird `PLwC Personal`.
Der finale Assetname wird erst mit
dem gebundenen G3-Kandidaten festgelegt. Bis dahin dürfen Store- und Registry-
Metadaten keinen alten r22–r27-Installer als aktuellen Personal-Download
ausweisen.

Der Personal-Updatekanal verwendet einen eigenen signierten Endpunkt und einen
neuen, lokal gepinnten öffentlichen RSA-Trustanker. Der vorhandene RSA-Prüfer
ist wiederverwendbar; der bisherige r27-Schlüssel ist **nicht** der Personal-
Trustanker. Die Datei kann als GitHub-Release-Asset ohne zusätzlichen
Hostingdienst bereitgestellt werden. Entstehen dadurch doch zusätzliche
Kosten, gilt die Product-Owner-Zustimmung zu diesem Kanal nicht.

Der echte Personal-Schlüssel wurde am 03.10.2026 vom Releaseverantwortlichen
lokal erzeugt; verschlüsselte Sicherung und Wiederherstellung sind geprüft.
`config/release-trust.json` enthält ausschließlich seine öffentlichen Parameter.
Der unabhängig geprüfte SPKI-SHA-256-Fingerprint lautet
`43b5314e2d46e3ca668fe409a9670582ab8af26c7dc6d4bcca44f3522c7079b8`.
Der Pin ist Bestandteil der Quellbaseline; die bestehende Nutzerinstallation
wurde nicht geändert. Der signierte Personal-Kandidat und seine reale
Update-Abnahme bleiben ausstehend.

Keine Angabe dieses Vertrags gibt Push, Build, GHCR-Public, Storeeinreichung,
Websiteänderung oder Veröffentlichung frei.
