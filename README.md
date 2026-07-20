# KjG-Aufbauspiel Manager

## Änderungen

- Orga-View ist passwortgeschützt.
- Passwort: `start123`
- Anmeldung bleibt in der Browser-Sitzung aktiv.
- Orga-Schreibaktionen werden serverseitig geschützt.
- Weißer Außenbereich aller Wappen ist transparent.
- Weiße Bestandteile innerhalb der Schilde bleiben erhalten.

## Lokal starten

```bash
python -m pip install -r requirements.txt
python app.py
```

## Render aktualisieren

1. ZIP entpacken.
2. Dateien im GitHub-Repository ersetzen.
3. Commit erstellen.
4. In Render `Manual Deploy` öffnen.
5. `Clear build cache & deploy` auswählen.

Start Command:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

Environment:

```text
PYTHON_VERSION=3.12.7
```
