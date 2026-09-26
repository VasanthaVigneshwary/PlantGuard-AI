from datetime import datetime

from database import get_connection


def _normalize_prediction_part(value):
    normalized = value.replace("_", " ").replace("-", " ")
    return " ".join(normalized.lower().split())


def get_disease_details_by_prediction(prediction):
    prediction_parts = prediction.split("___", 1)

    if len(prediction_parts) != 2:
        return None

    crop_name = _normalize_prediction_part(prediction_parts[0])
    predicted_disease = _normalize_prediction_part(prediction_parts[1])

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT d.id, d.name, c.name AS crop_name
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            ORDER BY d.id;
        """)

        matching_disease_id = None

        for disease_id, disease_name, database_crop_name in cursor.fetchall():
            normalized_crop_name = _normalize_prediction_part(database_crop_name)
            normalized_disease_name = _normalize_prediction_part(disease_name)

            if normalized_crop_name != crop_name:
                continue

            candidates = {
                normalized_disease_name,
            }

            crop_prefix = f"{crop_name} "
            if normalized_disease_name.startswith(crop_prefix):
                candidates.add(normalized_disease_name[len(crop_prefix):])

            if predicted_disease in candidates:
                matching_disease_id = disease_id
                break

        if matching_disease_id is None:
            return None

    finally:
        cursor.close()
        connection.close()

    return get_disease_details(matching_disease_id)


def get_all_crops():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, scientific_name, description
            FROM crops
            ORDER BY id;
        """)

        crops = cursor.fetchall()

        return crops

    finally:
        cursor.close()
        connection.close()


def get_all_diseases():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.name,
                c.name AS crop_name,
                d.description
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            ORDER BY d.id;
        """)

        diseases = cursor.fetchall()

        return diseases

    finally:
        cursor.close()
        connection.close()


def ensure_default_user():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1;")
        existing_user = cursor.fetchone()

        if existing_user is not None:
            return existing_user[0]

        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            ("Plant Guard User", "plantguard@local.test")
        )
        user_id = cursor.fetchone()[0]
        connection.commit()
        return user_id

    finally:
        cursor.close()
        connection.close()


def seed_default_notifications():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications;")
        if cursor.fetchone()[0] > 0:
            return

        user_id = ensure_default_user()
        default_notifications = [
            (
                "Plant health monitoring reminder",
                "Review the current crop health and upload a fresh leaf image if symptoms have changed.",
                "monitoring"
            ),
            (
                "Regular crop inspection reminder",
                "Inspect leaves, stems, and soil routinely to catch early signs of stress or disease.",
                "inspection"
            ),
            (
                "Disease prevention reminder",
                "Keep growing areas clean, improve airflow, and remove infected plant material promptly.",
                "prevention"
            ),
            (
                "Treatment and application reminder",
                "Follow the recommended treatment instructions and product label before applying any control measures.",
                "treatment"
            ),
            (
                "General plant-care reminder",
                "Maintain balanced watering, soil health, and crop spacing to support strong plant growth.",
                "care"
            ),
        ]

        cursor.executemany(
            """
                INSERT INTO notifications (user_id, title, message, notification_type, created_at, is_read)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                (user_id, title, message, notification_type, datetime.utcnow(), False)
                for title, message, notification_type in default_notifications
            ]
        )
        connection.commit()

    finally:
        cursor.close()
        connection.close()


def get_notifications():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications;")
        if cursor.fetchone()[0] == 0:
            cursor.close()
            connection.close()
            seed_default_notifications()
            connection = get_connection()
            cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                prediction_id,
                title,
                message,
                notification_type,
                scheduled_at,
                is_read,
                created_at
            FROM notifications
            ORDER BY created_at DESC, id DESC;
        """)

        rows = cursor.fetchall()
        notifications = []

        for row in rows:
            notifications.append({
                "id": row[0],
                "user_id": row[1],
                "prediction_id": row[2],
                "title": row[3],
                "message": row[4],
                "notification_type": row[5],
                "scheduled_at": row[6].isoformat() if row[6] is not None else None,
                "is_read": bool(row[7]) if row[7] is not None else False,
                "created_at": row[8].isoformat() if row[8] is not None else None,
            })

        return notifications

    finally:
        cursor.close()
        connection.close()


def normalize_name(value):
    if value is None:
        return ""

    return " ".join(
        value.replace("_", " ").replace("-", " ").lower().split()
    )


def get_disease_by_name(disease_name, crop_name=None):
    disease_name = (disease_name or "").strip()

    if not disease_name:
        return None

    normalized_target_disease = normalize_name(disease_name)
    normalized_crop_name = normalize_name(crop_name)

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                d.id,
                d.name,
                c.name AS crop_name,
                d.description
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            ORDER BY d.id;
        """)

        for disease_id, db_disease_name, db_crop_name, description in cursor.fetchall():
            normalized_db_disease = normalize_name(db_disease_name)
            normalized_db_crop = normalize_name(db_crop_name)

            if normalized_crop_name and normalized_db_crop != normalized_crop_name:
                continue

            candidates = {
                normalized_db_disease,
            }

            if normalized_db_disease.startswith(f"{normalized_crop_name} "):
                candidates.add(normalized_db_disease[len(normalized_crop_name) + 1:])

            if normalized_target_disease in candidates:
                return get_disease_details(disease_id)

            if normalized_target_disease in normalized_db_disease:
                return get_disease_details(disease_id)

        return None

    finally:
        cursor.close()
        connection.close()


def get_disease_details(disease_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Disease and crop
        cursor.execute("""
            SELECT
                d.id,
                d.name,
                c.name AS crop_name,
                d.description
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            WHERE d.id = %s;
        """, (disease_id,))

        disease = cursor.fetchone()

        if not disease:
            return None

        # Symptoms
        cursor.execute("""
            SELECT
                s.id,
                s.name,
                s.description
            FROM symptoms s
            JOIN disease_symptoms ds
                ON s.id = ds.symptom_id
            WHERE ds.disease_id = %s
            ORDER BY s.id;
        """, (disease_id,))

        symptoms = cursor.fetchall()

        # Causes
        cursor.execute("""
            SELECT
                c.id,
                c.name,
                c.description
            FROM causes c
            JOIN disease_causes dc
                ON c.id = dc.cause_id
            WHERE dc.disease_id = %s
            ORDER BY c.id;
        """, (disease_id,))

        causes = cursor.fetchall()

        # Prevention
        cursor.execute("""
            SELECT
                p.id,
                p.title,
                p.description
            FROM prevention p
            JOIN disease_prevention dp
                ON p.id = dp.prevention_id
            WHERE dp.disease_id = %s
            ORDER BY p.id;
        """, (disease_id,))

        prevention = cursor.fetchall()

        # Treatments and application rates
        cursor.execute("""
            SELECT
                t.id,
                t.name,
                t.type,
                t.description,
                t.instructions,
                t.precautions,
                ar.id,
                ar.application_method,
                ar.measurement_unit,
                ar.rate,
                ar.basis,
                ar.notes
            FROM treatments t
            LEFT JOIN application_rates ar
                ON t.id = ar.treatment_id
            WHERE t.disease_id = %s
            ORDER BY t.id, ar.id;
        """, (disease_id,))

        treatment_rows = cursor.fetchall()

        return {
            "disease": disease,
            "symptoms": symptoms,
            "causes": causes,
            "prevention": prevention,
            "treatments": treatment_rows
        }

    finally:
        cursor.close()
        connection.close()
