# Zeltlager Game Manager - Flask-Version v8 HTTP

Diese Version nutzt wieder HTTP, weil Browser selbstsignierte lokale HTTPS-Zertifikate häufig blockieren.

Alle bisherigen Design- und Funktionsänderungen bleiben erhalten:

- einfarbige plastische Buttons
- kompaktere Team-View
- bereinigte Lobby
- alle Timer blinken in den letzten 5 Sekunden weich
- Default-Spielzeit an Stationen: 01:00 Minute

## Installation

```bash
python -m pip install -r requirements.txt
```

## Start

```bash
python app.py
```

Laptop:

```text
http://localhost:5000
```

Handys im selben WLAN:

```text
http://DEINE-LAPTOP-IP:5000
```

Beispiel:

```text
http://192.168.178.23:5000
```
