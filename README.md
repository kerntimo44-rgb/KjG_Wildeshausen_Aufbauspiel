# KjG-Aufbauspiel Manager

## Änderungen in dieser Version

- Die Helfer-Übersicht ist zusätzlich in der Orga-View direkt unter dem Timer sichtbar.
- Team-Einstellungen enthalten jetzt ein Dropdown für Wappen.
- Die hochgeladenen CLAN-Wappen sind in `static/clans/` eingebunden.
- Bei Auswahl eines Wappens wird der Teamname automatisch auf den zugeordneten Māori-Ausdruck gesetzt.
- Jedes Wappen kann nur einmal vergeben werden; vergebene Wappen sind in anderen Dropdowns deaktiviert.
- Teamnamen und Wappen erscheinen in Lobby und Teamansicht.

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
