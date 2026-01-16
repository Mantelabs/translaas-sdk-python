# FastAPI Example

FastAPI application with async support, dependency injection, and automatic language resolution.

## Setup

```bash
cd examples/fastapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Translaas API key and configuration
```

## Running

```bash
uvicorn app:app --reload
```

## Features Demonstrated

- FastAPI async support
- Dependency injection
- Automatic language resolution
- API endpoints with translations
