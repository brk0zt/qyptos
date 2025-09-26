Cloud MVP — Complete package (Django + DRF)

Features included:
- JWT auth (login/refresh)
- User registration
- File uploads with optional one-time view + generated token
- Automatic watermarking for image uploads ("Confidential - <username>")
- Group (CloudGroup) creation, join via invite token
- Group file uploads and comments
- Simple frontend template with screenshot JS warning

Quickstart:
1. unzip cloud_mvp_complete.zip
2. python -m venv venv
3. source venv/bin/activate   (Windows: venv\Scripts\activate)
4. pip install -r requirements.txt
5. python manage.py makemigrations users files
6. python manage.py migrate
7. python manage.py createsuperuser
8. python manage.py runserver
