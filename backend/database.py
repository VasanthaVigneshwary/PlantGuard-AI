import psycopg2

DATABASE_URL = "postgresql://postgres:Varshak2418@localhost:5432/plant_guard_ai"


def get_connection():
    connection = psycopg2.connect(DATABASE_URL)
    return connection