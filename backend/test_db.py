from database import get_connection

try:
    connection = get_connection()

    print("✅ PostgreSQL connection successful!")

    cursor = connection.cursor()
    cursor.execute("SELECT current_database();")

    database_name = cursor.fetchone()[0]
    print(f"📌 Connected database: {database_name}")

    cursor.close()
    connection.close()

except Exception as e:
    print("❌ Database connection failed!")
    print("Error:", e)