# KjG-Aufbauspiel Manager

## Änderungen in dieser Version

- Team 1 bekommt standardmäßig das erste Wappen im Dropdown, Team 2 das zweite usw.
- Der Teamname wird dadurch standardmäßig auf den Māori-Ausdruck des jeweiligen Wappens gesetzt.
- Im Team-Ranking wird statt der Platznummer links das jeweilige Wappen angezeigt.
- Alle Wappenbilder werden ca. 25 % größer dargestellt.
- Die Clan-/Wappen-Funktion aus der vorherigen Version bleibt erhalten.

## Lokal testen

```bash
python -m pip install -r requirements.txt
python app.py
```

Dann öffnen:

```text
http://localhost:5000
```

## Auf Render aktualisieren

1. ZIP entpacken.
2. In deinem GitHub-Repository alle alten Dateien durch die neuen Dateien ersetzen.
3. Änderungen committen.
4. In Render öffnen.
5. `Manual Deploy` auswählen.
6. `Clear build cache & deploy` starten.

## Render-Einstellungen

Start Command:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

Environment:

```text
PYTHON_VERSION=3.12.7
```
