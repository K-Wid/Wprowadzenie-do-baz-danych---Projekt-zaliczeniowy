from sqlalchemy import URL
from import_module import database

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="postgres",
    host="localhost",
    port=5432,
    database="pogoda"
)

database.setup_engine(db_url)

# Zakres Dat

START_DATE = "2026-06-13"
END_DATE = "2026-06-15"

# Import danych historycznych

try:
    locations = database.get_locations()

    print(f"Znaleziono {len(locations)} lokalizacji.")
    print(f"Pobieranie danych od {START_DATE} do {END_DATE}...\n")

    result = database.insert_api_response_hourly(
        locations,
        START_DATE,
        END_DATE
    )

    print("\nImport zakończony.")

except Exception as e:
    print("Błąd:", e)
