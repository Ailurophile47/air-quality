from loader import get_connection

def get_or_create_location(city, country, lat, lon):
    with get_connection() as conn:
        with conn.cursor() as cur:

            # 1️⃣ Check if location exists
            cur.execute(
                """
                SELECT id 
                FROM locations 
                WHERE city_name = %s
                """,
                (city,),
            )

            result = cur.fetchone()

            if result:
                return result[0]

            # 2️⃣ Insert if not exists
            cur.execute(
                """
                INSERT INTO locations (city_name, country, latitude, longitude)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (city, country, lat, lon),
            )

            return cur.fetchone()[0]