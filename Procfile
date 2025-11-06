web: uvicorn slack_bot_simple:fastapi_app --host 0.0.0.0 --port $PORT --workers 4
release: python scripts/db_migrate.py up
# Heroku deployment - Using simplified bot (direct token, no OAuth)
