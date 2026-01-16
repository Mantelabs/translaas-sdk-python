# Django Example

Django application with middleware integration, template tags, and automatic language resolution.

## Setup

```bash
cd examples/django
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Translaas API key and configuration
```

## Running

```bash
python manage.py runserver
```

## Features Demonstrated

- Django middleware integration
- Template tags for translations
- Automatic language resolution
- Settings configuration
