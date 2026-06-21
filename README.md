# KjG-Aufbauspiel Manager

## Änderungen in dieser Version

- Stationsname steht oben neben dem Lobby-Button; Unterzeile „Station X“ entfällt.
- Teamname steht oben neben dem Lobby-Button.
- Leerzeile zwischen Lobby-Button-Zeile und Timer in Team-/Stationsansicht.
- Abstand zwischen Team-Punktestand und Dörfer/Städte/Großstädte reduziert.
- Lobby zeigt Teams mit kleinen Symbolen.
- Teamnamen können in der Orga-View wie Stationsnamen bearbeitet werden.
- Aktive Runde kann in der Orga-View manuell überschrieben werden.
- Rundentimer kann in der Orga-View auf Startwert zurückgesetzt werden, ohne Runde oder Punkte zu ändern.
- Hilfesystem bleibt erhalten.

## Lokal starten

```bash
python -m pip install -r requirements.txt
python app.py
```

## Render

Start Command:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

Environment:

```text
PYTHON_VERSION=3.12.7
```
