# Render Deployment

## Render settings

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

The Procfile already contains this start command.
