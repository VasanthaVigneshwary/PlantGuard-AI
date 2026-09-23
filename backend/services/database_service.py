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
