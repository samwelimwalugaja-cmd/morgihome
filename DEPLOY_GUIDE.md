# MorgiHome - GitHub + PythonAnywhere Deploy Guide

## 0) Kwenye PythonAnywhere console (safisha zamani)
```bash
rm -rf ~/.virtualenvs/old-project-env
rm -f ~/old-project/db.sqlite3
rm -rf ~/old-project
ls ~/
```

## 1) GitHub (backend + flutter) - run C:\morgihome
```bash
cd C:\morgihome
git init
git branch -M main
git remote add origin https://github.com/samwelimwalugaja-cmd/morgihome.git
git add .
git commit -m "MorgiHome full project (backend + flutter)"
git push -u origin main
```
> .gitignore tayari ina: venv/, __pycache__/, db.sqlite3, .env, staticfiles/, media/,
> frontend/morgihome_mobile/build/, .dart_tool/, .pub-cache/, *.pyc, *.log

## 2) PythonAnywhere console (backend TU - flutter haiendi huko)
```bash
git clone https://github.com/samwelimwalugaja-cmd/morgihome.git
cd morgihome
mkvirtualenv --python=/usr/bin/python3.10 morgihome-env
workon morgihome-env
pip install -r requirements.txt
cp .env.example .env
# hariri .env: SECRET_KEY mpya, DEBUG=False, ALLOWED_HOSTS=samweli20.pythonanywhere.com
python manage.py migrate
python manage.py collectstatic --noinput
```

## 3) .env (PA) - /home/samweli20/morgihome/.env
```
SECRET_KEY=<n-defu-random>
DEBUG=False
ALLOWED_HOSTS=samweli20.pythonanywhere.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://samweli20.pythonanywhere.com
CORS_ALLOWED_ORIGINS=https://samweli20.pythonanywhere.com
ADMIN_URL=admin-secure/
```
> settings.py tayari: bila DB_PASSWORD -> SQLite (`/home/samweli20/morgihome/db.sqlite3`).
> STATIC_ROOT = BASE_DIR/staticfiles, MEDIA_ROOT = BASE_DIR/media.

## 4) WSGI - /var/www/samweli20_pythonanywhere_com_wsgi.py
Copy kutoka `wsgi_pythonanywhere.py`:
```python
import os, sys
path = '/home/samweli20/morgihome'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'morgihome_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 5) Web tab Static files
| URL | Directory |
|-----|-----------|
| /static/ | /home/samweli20/morgihome/staticfiles |
| /media/ | /home/samweli20/morgihome/media |

## 6) Reload (Web tab -> Reload kijani)

## 7) Test
- https://samweli20.pythonanywhere.com
- static, login/register, properties, /api/ (flutter: `--dart-define=API_BASE_URL=https://samweli20.pythonanywhere.com/api/`)

| Kipengele | GitHub | PythonAnywhere |
| Backend (Django) | ✅ | ✅ |
| Flutter (Mobile) | ✅ | ❌ |
