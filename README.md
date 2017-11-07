# Sportsfreund - Facebook Messenger Bot 

## Über Sportsfreund
TODO

## Team 
TODO

[**Impressum**](http://www1.wdr.de/impressum/index.html)

## Nutzung
Benötigt werden ein Facebook Developer Account und ein api.ai Account.

Zunächst muss das GitHub-Repo gecloned werden:

```
git clone https://github.com/wdr-data/sportsfreund.git
```

Die Nutzung eines `virtualenv` ist empfohlen. Nachdem dieses angelegt und aktiviert ist, müssen die requirements installiert werden:

```
pip install -r requirements.txt
```

### Konfiguration
Neue Nachrichten werden von Facebook auf einen Webhook gesendet. Wir benutzen CherryPy als Webserver, der eine Django-Instanz per WSGI hostet, um diesen bereitzustellen. 

Die Webserver-Konfiguration befindet sich in `sportsfreund/start.py`. Standardmäßig läuft dieser auf `128.0.0.1:8004`. Für den Testbetrieb kann `ngrok` verwendet werden, um den Webhook zu empfangen, in der Produktion wird ein reverse proxy wie `nginx` oder `haproxy` empfohlen.

Als nächstes sollte Django konfiguriert werden. Dafür editieren Sie in `sportsfreund/sportsfreund/settings.py` die folgenden Attribute:
- `SITE_URL` (ohne trailing slash)
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- Eventuell `DATABASES`, falls nicht SQLite verwendet werden soll.

Es müssen außerdem die Wortlisten für die "Wörter-der-Wahl"-Funktionalität generiert werden. Hierzu wechseln Sie in das Verzeichnis `sportsfreund/bot/` und führen folgende Befehle aus:

```
mkdir output
python wp-vb.py
```

Nun legt man einen Admin-User an, migriert die Datenbank und sammelt die statischen Dateien. Dafür wechselt man zurück in das Projektverzeichnis `sportsfreund` (in dem sich `manage.py` befindet), und führt die folgenden Befehle aus:

```
./manage.py createsuperuser
./manage.py migrate
./manage.py collectstatic
```

Nun sollte das Django-Backend bereits funktionieren. Testen Sie dies mit
```
python start.py
```
Besuchen Sie `SITE_URL/admin` (also zum Beispiel http://128.0.0.1:8004/admin für lokalen Zugriff mit Standard-Werten) und loggen Sie sich mit den Admin-Daten ein, die Sie festgelegt haben. 

Falls dies funktioniert, können nun die Facebook- und api.ai Apps erstellt werden.

Für die Facebook-App, folgen Sie bitte der folgenden Anleitung: https://developers.facebook.com/docs/messenger-platform/guides/quick-start/

Bei dem Schritt, an dem Sie den Webhook aktivieren, müssen Sie außerdem folgendes beachten:

- Sportsfreund sucht das Page Token in der Umgebungsvariable `sportsfreund_PAGE_TOKEN` und das Hub Verify Token in `sportsfreund_HUB_VERIFY_TOKEN`.
- Der Webhook muss folgendes Muster haben: `SITE_URL/fb/YOURPAGETOKENHERE/` (**mit** trailing slash). 
- Abonnieren Sie die Events `messages`, `messaging_postbacks` und `messaging_referrals`
 
Das Page Token wird in der URL verwendet, damit niemand außer Facebook Webhooks an Sportsfreund senden kann.

Erstellen Sie außerdem eine api.ai App und importieren Sie den von uns trainierten Agent aus dem GitHub-Repository. Sportsfreund erwartet das api.ai Client Token in der Umgebungsvariable `sportsfreund_API_AI_TOKEN`.

Sportsfreund sollte nun antworten.

## Datenschutz 
Es gelten die Facebook-Datenschutz-Regeln. Falls Nutzer sich für Push-Nachrichten anmelden, speichert Sportsfreund eine PSID (page specific id). Diese ID identifiziert den User nur im Chat mit Sportsfreund und hat sonst keine Bedeutung für Facebook.
Um entscheiden zu können, welche Antwort Sportsfreund  dem Nutzer sendet, schickt Sportsfreund den Text der Nachricht und die psid zu api.ai (Google Assistant). 
Alleine kann Sportsfreund nichts lernen. Deshalb schauen sich Menschen die Fragen an, die Sportsfreund gestellt werden und machen Sportsfreund schlauer. 
Darüber hinaus werden keine Daten gezogen oder weiterverwendet.
Zu den Datenschutzbestimmungen des "Westdeutschen Rundfunks": http://www1.wdr.de/hilfe/datenschutz102.html

## Daten-Quellen / Credits 
- WDR-Kandidatencheck http://kandidatencheck.wdr.de/kandidatencheck/
- abgeordnetenwatch.de https://www.abgeordnetenwatch.de/
- Wahlkompass Digitales http://wahlkompass-digitales.de/
- Bundeswahlleiter https://www.bundeswahlleiter.de/
- infratest dimap https://www.infratest-dimap.de/
- Homepages der Parteien
- Sportsfreund arbeitet in Kooperation mit Novi, dem Nachrichten-Bot von Funk: https://www.funk.net/
- Sportsfreund hat sich beim WDR-Projekt "Wörter der Wahl" bedient: https://github.com/wdr-data/woerter-der-wahl
- Sportsfreund nutzt api.ai (Google Assistant) um die Absichten der Nutzer (intents) zu klassifizieren. Übergeben wird die PSID (Page Specific ID) und der Nachrichtentext.

## Rechtliches und Lizenzen 

#### Lizenz

Python (Source-Code oder aufbereitet) ist bei Beibehaltung des Lizenztextes unter der MIT License frei nutzbar und weiterverbreitbar.

[Lizenztext](LICENSE)

Für Grafiken wird kein Nutzungsrecht eingeräumt.

Das Urheberrecht der verwendeten Wahlprogramme liegt bei den Parteien. Für die Wahlprogramme wird kein Nutzungsrecht eingeräumt. 

#### Urheberrecht

Copyright Westdeutscher Rundfunk Köln


## Gewähleistungsausschluss 
Es besteht keinerlei Gewährleistung für das Programm, soweit dies gesetzlich zulässig ist. Sofern nicht anderweitig schriftlich bestätigt, stellen die Urheberrechtsinhaber und/oder Dritte das Programm so zur Verfügung, „wie es ist“, ohne irgendeine Gewährleistung. Das volle Risiko bezüglich Qualität und Leistungsfähigkeit des Programms liegt bei Ihnen.

