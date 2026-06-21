# KjG-Aufbauspiel Manager

Render-fertige Flask-/Socket.IO-Webapp für das KjG-Aufbauspiel.

## Änderungen in dieser Version

- Leerzeile zwischen Lobby-Button und Timer in Stations-, Team- und Helferansicht.
- Neuer Helferraum in der Lobby.
- Teams und Stationen können über einen roten Button „Hilfe“ rufen.
- Hilferuf färbt den Hintergrund der jeweiligen Team-/Stationsansicht rot.
- Helfer sehen Hilferufe in Reihenfolge des Eingangs.
- Erster Klick im Helferraum: Hilferuf wird gelb, Hintergrund der rufenden Ansicht wird gelb.
- Zweiter Klick im Helferraum: Hilferuf verschwindet, Hintergrund wird wieder normal.
- Mehrere Helfer können gleichzeitig in den Helferraum.
- Pro Station kann weiterhin nur eine Person beitreten.

## Lokal starten

```bash
python -m pip install -r requirements.txt
python app.py
```

## Render Start Command

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

## Render Environment

```text
PYTHON_VERSION=3.12.7
```
