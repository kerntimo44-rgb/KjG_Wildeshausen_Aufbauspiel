# KjG-Aufbauspiel Manager

Render-fertige Flask-/Socket.IO-Webapp für das KjG-Aufbauspiel.

## Änderungen in dieser Version

- Rundentimer aktualisiert sich jetzt direkt im Browser, ohne manuelles Neuladen.
- Lobby-Titel: `KjG-Aufbauspiel`.
- Default-Stationsnamen: Holz 1, Holz 2, Fisch 1, Fisch 2, Stein 1, Stein 2, Kokosnuss 1, Kokosnuss 2, Schilf 1, Schilf 2.
- Mehrere Personen können gleichzeitig in die Orga-View.
- Pro Station kann weiterhin nur eine Person beitreten.
- Blinkeffekt in den letzten 5 Sekunden ist deutlicher, aber weich.
- Orga-View-Untertext entfernt.
- Lobby-Bereiche für Stationen und Teams sind optisch gleich aufgebaut.

## Lokal starten

```bash
python -m pip install -r requirements.txt
python app.py
```

## Render Start Command

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```
