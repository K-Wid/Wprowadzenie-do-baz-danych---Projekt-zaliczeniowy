import time
import requests
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

# Lista Miast (76 największych pod względem liczby ludności)

CITIES = [
    "Warszawa",
    "Kraków",
    "Wrocław",
    "Łódź",
    "Poznań",
    "Gdańsk",
    "Szczecin",
    "Lublin",
    "Bydgoszcz",
    "Białystok",
    "Katowice",
    "Gdynia",
    "Częstochowa",
    "Rzeszów",
    "Radom",
    "Toruń",
    "Sosnowiec",
    "Kielce",
    "Gliwice",
    "Olsztyn",
    "Bielsko-Biała",
    "Zabrze",
    "Bytom",
    "Zielona Góra",
    "Rybnik",
    "Ruda Śląska",
    "Tychy",
    "Opole",
    "Gorzów Wielkopolski",
    "Dąbrowa Górnicza",
    "Elbląg",
    "Płock",
    "Koszalin",
    "Tarnów",
    "Włocławek",
    "Chorzów",
    "Wałbrzych",
    "Kalisz",
    "Legnica",
    "Grudziądz",
    "Jaworzno",
    "Słupsk",
    "Jastrzębie-Zdrój",
    "Nowy Sącz",
    "Jelenia Góra",
    "Siedlce",
    "Mysłowice",
    "Piła",
    "Ostrów Wielkopolski",
    "Suwałki",
    "Lubin",
    "Inowrocław",
    "Konin",
    "Stargard",
    "Piotrków Trybunalski",
    "Pruszków",
    "Siemianowice Śląskie"
    "Gniezno",
    "Żory",
    "Głogów",
    "Ostrowiec Świętokrzyski",
    "Tarnowskie Góry",
    "Pabianice",
    "Leszno",
    "Łomża",
    "Ełk",
    "Zamość",
    "Tomaszów Mazowiecki",
    "Chełm",
    "Mielec",
    "Tczew",
    "Przemyśl",
    "Stalowa Wola",
    "Biała Podlaska",
    "Kędzierzyn-Koźle"
]

# Dodawanie miast do tabeli 

for city in CITIES:
    url = (
    f"https://geocoding-api.open-meteo.com/v1/search"
    f"?name={city}&count=1&language=pl&format=json"
)

    data = requests.get(url, timeout=10).json()

    if "results" not in data:
        print(f"Nie znaleziono: {city}")
        continue

    result = data["results"][0]

    location = database.Location(
        name=city,
        latitude=result["latitude"],
        longitude=result["longitude"],
        elevation=result.get("elevation", 0)
    )

    success = database.add_location(location)

    print(
        city,
        "dodano" if success else "już istnieje"
    )

# Import danych co 60 min

while True:

    try:
        locations = database.get_locations()

        result = database.insert_api_response_current_time(locations)

        print("Import zakończony.")

    except Exception as e:
        print("Błąd importu:", e)

    print("Oczekiwanie 60 minut...\n")

    time.sleep(3600)