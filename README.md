# Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy
Projekt zaliczeniowy przedmiotu Wprowadzenie do baz danych.

#### Schemat ERD bazy danych

[Plik żródłowy (obraz)](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/e9e816449d68a4523dd83f51b0d8111316f8f114/Database_info/ERD.png)

[Plik żródłowy (PlantUML)](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/Database_info/ERD.puml)

![ERD_image](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/e9e816449d68a4523dd83f51b0d8111316f8f114/Database_info/ERD.png)

#### Wykorzystywane biblioteki Python
- sqlalchemy
- openmeteo-requests
- requests-cache
- retry-requests
- numpy
- pandas

```
pip install SQLAlchemy
pip install openmeteo-requests
pip install requests-cache
pip install retry-requests
pip install numpy
pip install pandas
```

#### Obecny stan projektu
Tabele *timezone* i *error_table* nie są wykorzystywane.

Uruchomienie projektu wymaga stworzenia pustej bazy danych w zewnętrznym programie oraz uruchomienia [kodu SQL tworzącego podstawowe tabele](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/SQL_scripts/creating_tables). W przypadku konieczności przywrócenia bazy danych do stanu początkowego trzeba uruchomić [kod SQL usuwający tabele](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/SQL_scripts/deleting_tables) i ponownie stworzyć tabele.

Istnieje plik [test.py](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/main/Python_code/test.py), który testuje podstawową funkcjonalność programu. **W obecnym stanie kod nie obsługuje wyjątków.**
