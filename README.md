# Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy
Projekt zaliczeniowy przedmiotu Wprowadzenie do baz danych.

#### Schemat ERD bazy danych

[Plik żródłowy (obraz)](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/e9e816449d68a4523dd83f51b0d8111316f8f114/Database_info/ERD.png)

[Plik żródłowy (PlantUML)](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/9b9b53b0c8d8d74b6775556c487997c0416bab44/Database_info/ERD.puml)

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
Uruchomienie projektu wymaga stworzenia pustej bazy danych w zewnętrznym programie oraz uruchomienia [kodu SQL tworzącego podstawowe tabele](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/890301137d357166779b3831c43d062e80ab8543/SQL_scripts/creating_tables). W przypadku konieczności przywrócenia bazy danych do stanu początkowego trzeba uruchomić [kod SQL usuwający tabele](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/890301137d357166779b3831c43d062e80ab8543/SQL_scripts/creating_tables) i ponownie stworzyć tabele.

Istnieje plik [test.py](https://github.com/K-Wid/Wprowadzenie-do-baz-danych---Projekt-zaliczeniowy/blob/890301137d357166779b3831c43d062e80ab8543/Python_code/test.py), który testuje podstawową funkcjonalność programu.
