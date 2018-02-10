# Sportsfreund - Facebook Messenger Bot

## Über Sportsfreund
Ich bin Sportsfreund, der Wintersport-Dienst der Sportschau. Ich bin für die Olympischen Winterspiele in PyeonChang entwickelt worden. Du kannst mich im Facebook-Messenger nutzen.
[sportsfreund.sportschau](m.me/sportsfreund.sportschau)

### Nachrichten erhalten
Ich schicke tägliche Highlights, Ergebnisse zu einer Sportart, Neuigkeiten zu Sportlern oder Medaillen und melde mich, wenn ein Livestream deiner Lieblingssportart startet. Du kannst dir die Sportsfreund-Nachrichten nach deinen Wünschen zusammenstellen und dich jederzeit anmelden und abmelden. Schreibe mir  'Anmelden für ...' und eine Sportart, einen Sportlernamen oder ein Land.

### Etwas fragen
Rufe meine Informationen selbst ab, indem du mir eine Nachricht schickst. Ich kenne über 2000 aktive Sportler. Oder frage zum Beispiel ‘Wann ist der nächste Ski-Wettkampf’, ‘Ergebnisse Biathlon’, ‘Ski Alpin Video’.

## Team
Redaktion: Willem de Haan, Nadine Mosch (MDR), Sebastian Göllner, David Vorholt (WDR) 
Umsetzung: Lisa Achenbach, Patricia Ennenbach, Jannes Höke, Christian Jörres, Marcus Weiner (WDR)
Grafik: Lisa Strieder (ARD.de)
Daten-Feeds: Heimspiel

[**Impressum**](http://www.sportschau.de/impressum/index.html)

## Nutzung

### Vorraussetzungen

- [Facebook Developer](https://developer.facebook.com/) App mit Messenger Integration: [Anleitung](https://developers.facebook.com/docs/messenger-platform/getting-started/app-setup)
- [Dialogflow](https://dialogflow.com/) App (früher api.ai)

Zunächst sollte der Source-Code lokal vorhanden sein. Dieses Git Kommando legt einen neuen Ordner mit dem Source an.

```
git clone https://github.com/wdr-data/sportsfreund.git
```


### Konfiguration

Diese Applikation wird über ein Shell Environment konfiguriert.
Zum Produktionsbetrieb ist dafür der Mechanismus der jeweiligen Platform zu nutzen.

Für die lokale Entwicklung kann die Konfiguration über die Datei `.env` im Source-Ordner erfolgen:

```bash
DEBUG=False           # Debug-Attribut der Services (z.B. Django) (optional)
LOG_LEVEL=info        # Loglevel des Application Servers Gunicorn (optional)
SECRET_KEY=12345      # Secret Key für Django
TUNNEL_NAME=          # ${TUNNEL_NAME}.localtunnel.me für den FB-Webhook
FB_PAGE_TOKEN=        # Access-Token für die Facebook API
FB_HUB_VERIFY_TOKEN=  # Verify Token für den Facebook Webhook
DIALOGFLOW_TOKEN=     # API Token für Dialogflow
FEED_URL=             # URL der Datenquellen (proprietär)
VIDEO_FEED_URL=       # URL für den Mediathek-Feed zum Wintersport (WDR intern)
VIDEO_PLAYLISTS_BASE= # URL zur Bestimmung der SMIL-Playlist eines Videos (WDR intern) - no trailing slash
VIDEO_URL_BASE=       # URL-Basis zum Abruf des MP4-Videos (WDR intern) - no trailing slash
LIVESTREAM_FEED_BASE=  # URL zum ECMS-Feed Olympia
LIVESTREAM_CENTER=    # URL zur Mediathek-Seite mit allen Livestreams
SENTRY_URL=           # DSN für die Sentry Error Logging Plattform (optional)
```

### Lokal ausführen

Zum lokalen Ausführen wird ein Docker-Daemon ([Installation](https://www.docker.com/get-docker)) und `docker-compose` benötigt.

Die Umgebung kann mit folgendem Befehl gestartet werden:

```bash
./start.sh
```

Nachdem die Einrichtung abgeschlossen ist, sollte die Funktionalität der Anwendung überprüft werden,
indem https://${TUNNEL_NAME}.localtunnel.me/admin/ aufgerufen werden. Dort sollte der Login zum Django-Backend erscheinen.


#### Einrichtung des Facebook-Webhooks

Wenn das funktioniert, kann die Einrichtung der Facebook-Integration abgeschlossen werden.
Dazu ist in der Facebook Developer App ein Webhook mit dieser URL einzurichten:

https://${TUNNEL_NAME}.localtunnel.me/fb/${FB_PAGE_TOKEN}/

Anschließend sollten die Events `messages`, `messaging_postbacks` und `messaging_referrals` für die gewünschte Seite abboniert werden.

Das Page Token wird in der URL verwendet, damit niemand außer Facebook Webhooks an Sportsfreund senden kann.

Sportsfreund sollte nun antworten.

### In Production

Für den Produktionsbetrieb werden zudem folgende Komponenten benötigt:
- PostgreSQL (Uri in `DATABASE_URL` hinterlegen)
- MongoDB (Uri in `MONGODB_URI` hinterlegen)
- Redis (Uri in `REDIS_URL` hinterlegen)
- S3 Bucket mit dieser Konfiguration:
  ```
  S3_ACCESS_KEY    # S3 Access Key
  S3_ACCESS_SECRET # S3 Access Secret
  S3_BUCKET        # S3 Bucket Name
  S3_ENDPOINT      # S3 Endpunkt (optional - für alternative Storages)
  S3_DOMAIN        # S3 Public Domain für URLs (optional - für alternative Storages)
  ```

Diese Applikation basiert auf Docker-Containern.
Zum Produktions-Betrieb kann man sich an der Datei [`docker-compose.yml`](/docker-compose.yml) orientieren,
diese muss allerdings an Produktionsbedingungen angepasst werden.

#### Heroku

Die Applikation kann auch auf Heroku ausgeführt werden.
Dazu muss lediglich dieses Repository deployed und die Environment Variablen gesetzt werden.

### Abhängigkeiten für die IDE

Dieses Python-Projekt nutzt Pipenv zur Verwaltung der Abhängigkeiten und des `virtualenv`.

Zum Ausführen der Anwendung müssen die Abhängigkeiten nicht installiert sein. Es bietet sich
allerdings an, ein lokales virtualenv zu erstellen, damit die IDE die Abhängigkeiten erkennen kann.

```bash
pipenv install
```


## Datenschutz
Es gelten die Facebook-Datenschutz-Regeln. Falls Nutzer sich für Push-Nachrichten anmelden, speichert Sportsfreund eine PSID (page specific id). Diese ID identifiziert den User nur im Chat mit Sportsfreund und hat sonst keine Bedeutung für Facebook.
Um entscheiden zu können, welche Antwort Sportsfreund  dem Nutzer sendet, schickt Sportsfreund den Text der Nachricht und die psid zu api.ai (Google Assistant).
Alleine kann Sportsfreund nichts lernen. Deshalb schauen sich Menschen die Fragen an, die Sportsfreund gestellt werden und machen Sportsfreund schlauer.
Darüber hinaus werden keine Daten gezogen oder weiterverwendet.
Zu den Datenschutzbestimmungen des "Westdeutschen Rundfunks": http://www1.wdr.de/hilfe/datenschutz102.html

## Daten-Quellen / Credits
- Sportsfreund arbeitet in Kooperation mit Novi, dem Nachrichten-Bot von Funk: https://www.funk.net/
- Sportsfreund nutzt api.ai (Google Assistant) um die Absichten der Nutzer (intents) zu klassifizieren. Übergeben wird die PSID (Page Specific ID) und der Nachrichtentext.

## Rechtliches und Lizenzen

#### Lizenz

Python (Source-Code oder aufbereitet) ist bei Beibehaltung des Lizenztextes unter der MIT License frei nutzbar und weiterverbreitbar.

[Lizenztext](LICENSE)

Für Grafiken wird kein Nutzungsrecht eingeräumt.

Das Urheberrecht der verwendeten Wahlprogramme liegt bei den Parteien. Für die Wahlprogramme wird kein Nutzungsrecht eingeräumt.

#### Urheberrecht

Copyright Westdeutscher Rundfunk Köln


#### Gewähleistungsausschluss
Es besteht keinerlei Gewährleistung für das Programm, soweit dies gesetzlich zulässig ist. Sofern nicht anderweitig schriftlich bestätigt, stellen die Urheberrechtsinhaber und/oder Dritte das Programm so zur Verfügung, „wie es ist“, ohne irgendeine Gewährleistung. Das volle Risiko bezüglich Qualität und Leistungsfähigkeit des Programms liegt bei Ihnen.
