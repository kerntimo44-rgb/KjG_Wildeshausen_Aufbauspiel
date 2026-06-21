# Render Deployment

## Build Command

```bash
pip install -r requirements.txt
```

## Start Command

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

## Environment Variable

```text
PYTHON_VERSION=3.12.7
```
