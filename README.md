# Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy
Projekt zaliczeniowy przedmiotu Wprowadzenie do baz danych.

#### Schemat ERD bazy danych

[Plik żródłowy (obraz)](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/Database_info/ERD.png)

[Plik żródłowy (PlantUML)](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/Database_info/ERD.puml)

![ERD_image](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/Database_info/ERD.png)

#### Wykorzystywane biblioteki Python
- sqlalchemy
- openmeteo-requests
- requests-cache
- retry-requests
- numpy
- pandas
- Wszystkie inne bazowe dla powyższych

```
pip install SQLAlchemy
pip install openmeteo-requests
pip install requests-cache
pip install retry-requests
pip install numpy
pip install pandas
```

#### Obecny stan projektu
Tabela *timezone* nie jest wykorzystywana.

Połączenie tabel *log_import* i *error_table* może ulec zmianie.

Uruchomienie projektu wymaga stworzenia pustej bazy danych w zewnętrznym programie oraz uruchomienia funkcji `database.create_all_tables()`. W celu przywrócenia bazy danych do stanu początkowego możliwe jest wywołanie `database.destroy_all_tables()`, a następnie `database.create_all_tables()`.

Działające funkcjonalności:
- Tworzenie i usuwanie tabel z bazy danych
- Dodawanie lokalizacji do bazy danych
- Uzyskiwanie tabel z bazy danych poprzez zapytania SQL
- Komunikacja z [OpenMeteo API](https://open-meteo.com/en/docs)
- Dodanie rzeczywistych danych pogodowych wybranych lokalizacji do bazy danych
- Dodanie godzinowych (w określonym przedziale dat) danych pogodowych wybranych lokalizacji do bazy danych

Istnieje plik [test.py](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/Python_code/test.py), który testuje podstawową funkcjonalność programu. **Kod nie generuje ani nie obsługuje wyjątków.**
