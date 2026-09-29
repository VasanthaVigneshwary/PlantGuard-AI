import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to the project .env file.")


def get_connection():
    connection = psycopg2.connect(DATABASE_URL)
    return connection