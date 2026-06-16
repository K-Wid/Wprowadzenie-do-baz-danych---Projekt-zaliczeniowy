import customtkinter as ctk
from tkinter import ttk, messagebox
from sqlalchemy.engine import URL
import requests
import threading
from import_module import database as db
from import_module import config
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

DB_URL = URL.create(
    drivername="postgresql",
    username="postgres",      
    password="haslo",         
    host="localhost",
    database="pogoda"   
)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WeatherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Baza Danych - Stacja Pogodowa")
        self.geometry("950x650")

        db_url = config.read_config()
        if not isinstance(db_url, URL):
            db_url = URL.create(
                drivername="postgresql",
                username="postgres",      
                password="haslo",         
                host="localhost",
                port=5432,
                database="pogoda",        
            )
            config.save_config(db_url, True)
            db_url = config.read_config()

        try:
            db.setup_engine(db_url)
        except Exception as e:
            messagebox.showwarning("Błąd Bazy", f"Nie udało się połączyć z bazą.\nSprawdź plik konfiguracyjny.\n\nSzczegóły:\n{e}")

        self.miasta = self.pobierz_miasta_z_bazy()
        
        self.setup_ui()
    
    def aktualizuj_baze(self):
        def pobierz_w_tle():
            try:
                lokalizacje = db.get_locations()
                data_od = "2026-05-15"
                data_do = "2026-06-16"
                
                db.insert_api_response_current_time(lokalizacje)
                db.insert_api_response_hourly(lokalizacje, data_od, data_do)
                messagebox.showinfo("Sukces", "Baza danych została zaktualizowana o nowe pomiary z API.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Wystąpił błąd podczas aktualizacji:\n{e}")

        messagebox.showinfo("Informacja", "Rozpoczęto aktualizację z API. To może potrwać kilkanaście sekund...")
        threading.Thread(target=pobierz_w_tle, daemon=True).start()

    def pobierz_miasta_z_bazy(self):
        try:
            df = db.get_dataframe_from_sql("SELECT DISTINCT name FROM location_table ORDER BY name;")
            return df['name'].tolist() if not df.empty else ["Bydgoszcz", "Warszawa"]
        except:
            return ["Bydgoszcz", "Warszawa"]

    def setup_ui(self):
        frame_top = ctk.CTkFrame(self)
        frame_top.pack(pady=(20, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_top, text="Miasto:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        
        self.combo_miasto = ctk.CTkComboBox(frame_top, values=self.miasta, width=200)
        self.combo_miasto.pack(side="left", padx=5)

        ctk.CTkLabel(frame_top, text=" | ").pack(side="left", padx=5)

        self.entry_nowe_miasto = ctk.CTkEntry(frame_top, placeholder_text="Nowe miasto do listy...", width=200)
        self.entry_nowe_miasto.pack(side="left", padx=5)

        btn_dodaj = ctk.CTkButton(frame_top, text="Dodaj miasto", command=self.dodaj_miasto, width=100)
        btn_dodaj.pack(side="left", padx=5)
        btn_aktualizuj = ctk.CTkButton(frame_top, text="Aktualizuj z API", command=self.aktualizuj_baze, width=120)
        btn_aktualizuj.pack(side="left", padx=5)

        frame_mid = ctk.CTkFrame(self)
        frame_mid.pack(pady=10, padx=20, fill="x")

        frame_left = ctk.CTkFrame(frame_mid)
        frame_left.pack(side="left", fill="both", expand=True)
 
        frame_right = ctk.CTkFrame(frame_mid)
        frame_right.pack(side="right", fill="y", padx=10)

        self.wykres_param = ctk.StringVar(value="Temperatura")
        ctk.CTkLabel(frame_right, text="Parametr wykresu:").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 2)
        )

        self.combo_wykres = ctk.CTkComboBox(
            frame_right,
            values=["Temperatura", "Wilgotność", "Ciśnienie", "Opady"],
            variable=self.wykres_param
        )
        self.combo_wykres.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 10))

        self.tabs_parametry = ctk.CTkTabview(frame_left, height=160)
        self.tabs_parametry.pack(fill="x", padx=5, pady=5)

        self.vars = {
            "Opady": {
                "Relatywna wilgotność": ctk.BooleanVar(),
                "Deszcz": ctk.BooleanVar(),
                "Opady śniegu": ctk.BooleanVar()
            },
            "Wiatr": {
                "Prędkość": ctk.BooleanVar(),
                "Kierunek": ctk.BooleanVar(),
                "Prędkość w porywach": ctk.BooleanVar()
            },
            "Temperatura": {
                "Temperatura": ctk.BooleanVar(value=True),
                "Temp. odczuwalna": ctk.BooleanVar()
            },
            "Pogoda": {
                "Ciśnienie n.p.m.": ctk.BooleanVar(),
                "Zachmurzenie": ctk.BooleanVar(),
                "Opis pogody": ctk.BooleanVar()
            },
            "Pomiary": {
                "Czas pomiaru": ctk.BooleanVar(value=True) 
            },
            "Lokalizacja": {
                "Szerokość geogr.": ctk.BooleanVar(),
                "Długość geogr.": ctk.BooleanVar(),
                "Wysokość n.p.m.": ctk.BooleanVar()
            },
            "Strefa czasowa": {
                "Pełna nazwa": ctk.BooleanVar(),
                "Skrócona nazwa": ctk.BooleanVar(),
                "Offset": ctk.BooleanVar()
            }
        }


        for kategoria, opcje in self.vars.items():
            self.tabs_parametry.add(kategoria)
            tab = self.tabs_parametry.tab(kategoria)
            
            col, row = 0, 0
            for nazwa, var in opcje.items():
                ctk.CTkCheckBox(tab, text=nazwa, variable=var).grid(row=row, column=col, padx=15, pady=5, sticky="w")
                col += 1
                if col > 2:  
                    col = 0
                    row += 1

        ctk.CTkLabel(frame_right, text="Od (YYYY-MM-DD):").grid(
            row=2, column=0, padx=5, pady=2, sticky="e"
        )
        self.entry_od = ctk.CTkEntry(frame_right, width=140)
        self.entry_od.grid(row=2, column=1, padx=5, pady=2)

        ctk.CTkLabel(frame_right, text="Do (YYYY-MM-DD):").grid(
            row=3, column=0, padx=5, pady=2, sticky="e"
        )
        self.entry_do = ctk.CTkEntry(frame_right, width=140)
        self.entry_do.grid(row=3, column=1, padx=5, pady=2)

        btn_szukaj = ctk.CTkButton(
            frame_right,
            text="Pobierz dane",
            font=ctk.CTkFont(weight="bold"),
            command=self.pobierz_dane
        )

        btn_wykres = ctk.CTkButton(
            frame_right,
            text="Pokaż wykres",
            command=self.pokaz_wykres
        )

        btn_szukaj.grid(row=4, column=0, columnspan=2, sticky="we", pady=(10, 5))
        btn_wykres.grid(row=5, column=0, columnspan=2, sticky="we", pady=5)

        frame_tree = ctk.CTkFrame(frame_left)
        frame_tree.pack(fill="both", expand=True, pady=10)

        self.tree = ttk.Treeview(frame_tree, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

        self.frame_chart = ctk.CTkFrame(self)
        self.frame_chart.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = None

    

    def dodaj_miasto(self):
        nowe_miasto = self.entry_nowe_miasto.get().strip()
        
        if not nowe_miasto:
            return
            
        if nowe_miasto in self.miasta:
            messagebox.showinfo("Informacja", "To miasto jest już na liście.")
            return

        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={nowe_miasto}&count=1&language=pl&format=json"
            response = requests.get(url, timeout=5)
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                nazwa_oficjalna = result["name"]
                lat = result["latitude"]
                lon = result["longitude"]
                elev = result.get("elevation", 0.0)
                nowa_lokalizacja = db.Location(nazwa_oficjalna, lat, lon, elev)
                
                if db.add_location(nowa_lokalizacja):
                    if nazwa_oficjalna not in self.miasta:
                        self.miasta.append(nazwa_oficjalna)
                        self.combo_miasto.configure(values=self.miasta)
                    
                    self.combo_miasto.set(nazwa_oficjalna)
                    self.entry_nowe_miasto.delete(0, 'end')
                    self.aktualizuj_baze()
                    messagebox.showinfo("Sukces", f"Zapisano {nazwa_oficjalna} w bazie danych.")                
                else:
                    messagebox.showerror("Błąd", "Nie udało się zapisać miasta w bazie (prawdopodobnie już tam istnieje).")
            else:
                messagebox.showwarning("Brak wyników", f"API nie znalazło współrzędnych dla: {nowe_miasto}")
                
        except requests.RequestException:
            messagebox.showerror("Błąd Sieci", "Problem z połączeniem z API Open-Meteo.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił problem:\n{e}")

    def pobierz_dane(self):
        miasto = self.combo_miasto.get()
        data_od = self.entry_od.get().strip()
        data_do = self.entry_do.get().strip()

        selects = ["l.name AS miasto", "d.date_value AS data"]
        joins = [
            "measurement m",
            "JOIN location_table l ON m.location_id = l.location_id",
            "JOIN date_table d ON m.date_id = d.date_id"
        ]
        group_by = ["l.name", "d.date_value"]

        if self.vars["Pomiary"]["Czas pomiaru"].get():
            selects.append("t_time.time_value AS czas")
            joins.append("LEFT JOIN time_table t_time ON m.time_id = t_time.time_id")
            group_by.append("t_time.time_value")

        v_temp = self.vars["Temperatura"]
        if any(v.get() for v in v_temp.values()):
            joins.append("LEFT JOIN temperature t ON m.measurement_id = t.measurement_id")
            if v_temp["Temperatura"].get(): selects.append("ROUND(AVG(t.temperature)::numeric, 2) AS temperatura")
            if v_temp["Temp. odczuwalna"].get(): selects.append("ROUND(AVG(t.apparent_temperature)::numeric, 2) AS temp_odczuwalna")

        v_opady = self.vars["Opady"]
        if any(v.get() for v in v_opady.values()):
            joins.append("LEFT JOIN precipitation p ON m.measurement_id = p.measurement_id")
            if v_opady["Relatywna wilgotność"].get(): selects.append("ROUND(AVG(p.relative_humidity)::numeric, 2) AS wilgotnosc")
            if v_opady["Deszcz"].get(): selects.append("ROUND(SUM(p.rain)::numeric, 2) AS deszcz")
            if v_opady["Opady śniegu"].get(): selects.append("ROUND(SUM(p.snowfall)::numeric, 2) AS snieg")

        v_wiatr = self.vars["Wiatr"]
        if any(v.get() for v in v_wiatr.values()):
            joins.append("LEFT JOIN wind wnd ON m.measurement_id = wnd.measurement_id")
            if v_wiatr["Prędkość"].get(): selects.append("ROUND(AVG(wnd.wind_speed)::numeric, 2) AS wiatr_predkosc")
            if v_wiatr["Kierunek"].get(): selects.append("ROUND(AVG(wnd.wind_direction)::numeric, 2) AS wiatr_kierunek")
            if v_wiatr["Prędkość w porywach"].get(): selects.append("ROUND(MAX(wnd.wind_gusts)::numeric, 2) AS wiatr_porywy")

        v_pogoda = self.vars["Pogoda"]
        if any(v.get() for v in v_pogoda.values()):
            joins.append("LEFT JOIN weather w ON m.measurement_id = w.measurement_id")
            if v_pogoda["Ciśnienie n.p.m."].get(): selects.append("ROUND(AVG(w.surface_pressure)::numeric, 2) AS cisnienie")
            if v_pogoda["Zachmurzenie"].get(): selects.append("ROUND(AVG(w.cloud_cover)::numeric, 2) AS zachmurzenie")
            if v_pogoda["Opis pogody"].get():
                joins.append("LEFT JOIN weather_code wc ON w.weather_code_id = wc.weather_code_id")
                selects.append("MAX(wc.description) AS opis_pogody")

        v_lok = self.vars["Lokalizacja"]
        if v_lok["Szerokość geogr."].get(): selects.append("MAX(l.latitude) AS szerokosc")
        if v_lok["Długość geogr."].get(): selects.append("MAX(l.longitude) AS dlugosc")
        if v_lok["Wysokość n.p.m."].get(): selects.append("MAX(l.elevation) AS wysokosc_npm")

        v_strefa = self.vars["Strefa czasowa"]
        if any(v.get() for v in v_strefa.values()):
            joins.append("LEFT JOIN timezone tz ON l.timezone_id = tz.timezone_id")
            if v_strefa["Pełna nazwa"].get(): selects.append("MAX(tz.full_name) AS strefa_pelna")
            if v_strefa["Skrócona nazwa"].get(): selects.append("MAX(tz.short_name) AS strefa_skrot")
            if v_strefa["Offset"].get(): selects.append("MAX(tz.time_offset::text) AS strefa_offset") # Rzutowanie unikające błędu typu interval

        if len(selects) == 2:
            messagebox.showwarning("Błąd", "Wybierz przynajmniej jeden parametr.")
            return

        query = f"SELECT {', '.join(selects)} \nFROM {' '.join(joins)} \nWHERE l.name = '{miasto}'"
        
        if data_od: query += f" AND d.date_value >= '{data_od}'"
        if data_do: query += f" AND d.date_value <= '{data_do}'"

        query += f"\nGROUP BY {', '.join(group_by)} \nORDER BY d.date_value DESC"
        if self.vars["Pomiary"]["Czas pomiaru"].get():
            query += ", t_time.time_value DESC"
            
        query += ";"

        try:
            df = db.get_dataframe_from_sql(query)

            self.tree.delete(*self.tree.get_children())

            if df.empty:
                messagebox.showinfo("Wynik", "Brak wyników w bazie dla podanych kryteriów.")
                return

            self.tree["columns"] = list(df.columns)
            for col in df.columns:
                self.tree.heading(col, text=str(col).replace("_", " ").title())
                self.tree.column(col, anchor="center", width=110)

            for _, row in df.iterrows():
                self.tree.insert("", "end", values=list(row))

        except Exception as e:
            messagebox.showerror("Błąd Bazy", f"Wystąpił problem przy zapytaniu:\n{e}")

    def pokaz_wykres(self):

        param = self.combo_wykres.get()
        miasto = self.combo_miasto.get()
        data_od = self.entry_od.get().strip()
        data_do = self.entry_do.get().strip()

        joins = [
            "JOIN location_table l ON m.location_id = l.location_id",
            "JOIN date_table d ON m.date_id = d.date_id",
            "JOIN time_table t_time ON m.time_id = t_time.time_id"
        ]

        if param == "Temperatura":
            select_col = "temp.temperature"
            joins.append("JOIN temperature temp ON m.measurement_id = temp.measurement_id")
            ylabel = "°C"

        elif param == "Wilgotność":
            select_col = "p.relative_humidity"
            joins.append("JOIN precipitation p ON m.measurement_id = p.measurement_id")
            ylabel = "%"

        elif param == "Ciśnienie":
            select_col = "w.surface_pressure"
            joins.append("JOIN weather w ON m.measurement_id = w.measurement_id")
            ylabel = "hPa"

        elif param == "Opady":
            select_col = "p.rain"
            joins.append("JOIN precipitation p ON m.measurement_id = p.measurement_id")
            ylabel = "mm"

        query = f"""
        SELECT
            d.date_value,
            t_time.time_value,
            {select_col} AS value
        FROM measurement m
        {' '.join(joins)}
        WHERE l.name = '{miasto}'
        """

        if data_od:
            query += f" AND d.date_value >= '{data_od}'"

        if data_do:
            query += f" AND d.date_value <= '{data_do}'"

        query += """
        ORDER BY d.date_value, t_time.time_value
        """

        try:
            df = db.get_dataframe_from_sql(query)

            if df.empty:
                messagebox.showinfo(
                    "Brak danych",
                    "Brak danych do narysowania wykresu."
                )
                return

            df["datetime"] = pd.to_datetime(
                df["date_value"].astype(str)
                + " "
                + df["time_value"].astype(str)
            )

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            fig, ax = plt.subplots(figsize=(8, 4))

            ax.plot(df["datetime"], df["value"])

            ax.set_title(f"{param} - {miasto}")
            ax.set_xlabel("Czas")
            ax.set_ylabel(ylabel)
            ax.grid(True)

            fig.autofmt_xdate()

            self.canvas = FigureCanvasTkAgg(
                fig,
                master=self.frame_chart
            )

            self.canvas.draw()
            self.canvas.get_tk_widget().pack(
                fill="both",
                expand=True
            )

        except Exception as e:
            messagebox.showerror(
                "Błąd",
                str(e)
            )




if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()