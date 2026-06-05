import customtkinter as ctk
from tkinter import ttk, messagebox
import requests
import pandas as pd
from sqlalchemy.engine import URL

import import_from_openmeteo as om
import database as db

# --- KONFIGURACJA BAZY DANYCH ---
DB_URL = URL.create(
    drivername="postgresql",
    username="postgres",      
    password="haslo",         
    host="localhost",
    database="pogoda"        
)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def get_weather_icon(wmo_code):
    """Mapuje kod pogody WMO na ikonę Unicode."""
    if wmo_code in [0, 1]: return "☀️"         # Czyste niebo
    elif wmo_code in [2]: return "⛅"          # Częściowe zachmurzenie
    elif wmo_code in [3]: return "☁️"          # Pochmurno
    elif wmo_code in [45, 48]: return "🌫️"     # Mgła
    elif 51 <= wmo_code <= 67: return "🌧️"     # Deszcz
    elif 71 <= wmo_code <= 77: return "❄️"     # Śnieg
    elif 80 <= wmo_code <= 82: return "🌦️"     # Przelotny deszcz
    elif 95 <= wmo_code <= 99: return "⛈️"     # Burza
    else: return "🌡️"                         # Domyślna

class WeatherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stacja Pogodowa")
        self.geometry("950x650")

        # Inicjalizacja i TEST połączenia z bazą danych
        try:
            db.setup_engine(DB_URL)
            with db.engine.connect() as conn:
                pass
        except Exception as e:
            messagebox.showwarning("Błąd Bazy Danych", f"Nie udało się połączyć z bazą. Historia będzie niedostępna.\n\nSzczegóły:\n{e}")

        self.current_city = "Bydgoszcz"
        self.lat = 53.1235
        self.lon = 18.0084

        self.setup_ui()
        self.get_initial_location()

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_weather = self.tabview.add("Prognoza Pogody")
        self.tab_history = self.tabview.add("Historia Pomiarów")

        self.setup_weather_tab()
        self.setup_history_tab()

    def setup_weather_tab(self):
        # Pasek wyszukiwania
        search_frame = ctk.CTkFrame(self.tab_weather, fg_color="transparent")
        search_frame.pack(pady=(10, 20), fill="x", padx=20)

        self.city_entry = ctk.CTkEntry(search_frame, placeholder_text="Wpisz nazwę miasta...", height=40, font=ctk.CTkFont(size=14))
        self.city_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        search_btn = ctk.CTkButton(search_frame, text="Szukaj", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.search_city)
        search_btn.pack(side="right")

        # Karta obecnej pogody
        self.current_weather_frame = ctk.CTkFrame(self.tab_weather, corner_radius=15)
        self.current_weather_frame.pack(pady=10, fill="x", padx=20)

        self.city_label = ctk.CTkLabel(self.current_weather_frame, text="Miasto: --", font=ctk.CTkFont(size=28, weight="bold"))
        self.city_label.pack(pady=(20, 5))

        self.icon_label = ctk.CTkLabel(self.current_weather_frame, text="--", font=ctk.CTkFont(size=70))
        self.icon_label.pack()

        self.temp_label = ctk.CTkLabel(self.current_weather_frame, text="-- °C", font=ctk.CTkFont(size=36, weight="bold"), text_color="#3B8ED0")
        self.temp_label.pack(pady=(0, 20))

        # Prognoza
        forecast_label = ctk.CTkLabel(self.tab_weather, text="Prognoza na najbliższe 7 dni:", font=ctk.CTkFont(size=18, weight="bold"))
        forecast_label.pack(pady=(20, 10), padx=20, anchor="w")

        self.forecast_frame = ctk.CTkScrollableFrame(self.tab_weather, orientation="horizontal", height=160, fg_color="transparent")
        self.forecast_frame.pack(fill="x", padx=20)

    def setup_history_tab(self):
        filter_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        filter_frame.pack(pady=10, fill="x", padx=20)

        refresh_btn = ctk.CTkButton(filter_frame, text="Odśwież dane z bazy", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.load_history)
        refresh_btn.pack(side="left")

        # Stylowanie tabeli
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))
        style.configure("Treeview", font=('Arial', 11), rowheight=25)

        columns = ("id", "miasto", "data", "temperatura")
        self.tree = ttk.Treeview(self.tab_history, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID Pomiaru")
        self.tree.heading("miasto", text="Miasto")
        self.tree.heading("data", text="Data")
        self.tree.heading("temperatura", text="Temperatura (°C)")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def get_initial_location(self):
        try:
            response = requests.get("http://ip-api.com/json/", timeout=3)
            data = response.json()
            if data.get("status") == "success":
                self.current_city = data["city"]
                self.lat = data["lat"]
                self.lon = data["lon"]
        except requests.RequestException:
            pass 
        
        self.update_weather_display()

    def search_city(self):
        city_name = self.city_entry.get().strip()
        if not city_name:
            return

        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=pl&format=json"
            response = requests.get(url, timeout=5)
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                self.lat = result["latitude"]
                self.lon = result["longitude"]
                self.current_city = result["name"]
                
                self.update_weather_display()
            else:
                messagebox.showinfo("Brak wyników", f"Nie znaleziono miasta: {city_name}")
                
        except requests.RequestException:
            messagebox.showerror("Błąd", "Wystąpił problem z połączeniem podczas wyszukiwania miasta.")

    def update_weather_display(self):
        self.city_label.configure(text=self.current_city)
        
        try:
            params = {
                "latitude": [self.lat],
                "longitude": [self.lon],
                "elevation": [0],
                "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "weather_code", "cloud_cover", "pressure_msl", "precipitation", "rain", "snowfall", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"],
                "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
                "timezone": ["auto"]
            }
            
            responses = om.get_responses(params)
            response = responses[0]

            # Bieżąca pogoda
            current_weather = om.MeteoResponse(response.Current())
            
            self.temp_label.configure(text=f"{current_weather.temperature_2m:.1f} °C")
            
            # Ustawienie ikony na podstawie weather_code
            icon = get_weather_icon(current_weather.weather_code)
            self.icon_label.configure(text=icon)

            # Czyszczenie starych kafelków prognozy
            for widget in self.forecast_frame.winfo_children():
                widget.destroy()

            # Prognoza dzienna
            daily = response.Daily()
            daily_t_max = daily.Variables(0).ValuesAsNumpy()
            daily_t_min = daily.Variables(1).ValuesAsNumpy()
            daily_codes = daily.Variables(2).ValuesAsNumpy()
            
            dates = pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )

            for i in range(len(dates)):
                day_frame = ctk.CTkFrame(self.forecast_frame, width=130, height=140, corner_radius=10)
                day_frame.pack(side="left", padx=10, pady=5)
                
                date_str = dates[i].strftime("%d.%m")
                t_max = daily_t_max[i]
                t_min = daily_t_min[i]
                day_icon = get_weather_icon(daily_codes[i])
                
                ctk.CTkLabel(day_frame, text=date_str, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 0))
                ctk.CTkLabel(day_frame, text=day_icon, font=ctk.CTkFont(size=30)).pack(pady=5)
                ctk.CTkLabel(day_frame, text=f"Max: {t_max:.1f}°", text_color="#E07A5F", font=ctk.CTkFont(weight="bold")).pack()
                ctk.CTkLabel(day_frame, text=f"Min: {t_min:.1f}°", text_color="#81B29A").pack(pady=(0, 10))

        except Exception as e:
            self.temp_label.configure(text="Błąd")
            messagebox.showerror("Błąd API", f"Wystąpił problem:\n{e}")

    def load_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        sql_command = """
            SELECT m.measurement_id, l.name, d.date_value, t.temperature
            FROM measurement m
            JOIN location_table l ON m.location_id = l.location_id
            JOIN date_table d ON m.date_id = d.date_id
            JOIN temperature t ON m.measurement_id = t.measurement_id
            ORDER BY d.date_value DESC, m.measurement_id DESC
            LIMIT 100;
        """
        
        try:
            df = db.get_dataframe_from_sql(sql_command)
            
            for _, row in df.iterrows():
                temp_formatted = f"{row['temperature']:.1f}"
                
                self.tree.insert("", "end", values=(
                    row['measurement_id'], 
                    row['name'], 
                    row['date_value'], 
                    temp_formatted
                ))
                
        except Exception as e:
            messagebox.showerror("Błąd Bazy", f"Brak tabel lub błąd zapytania:\n{e}")

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()