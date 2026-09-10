import sqlite3

def initialize_database(db_name="pipe_span_app.db"):
    """Connects to SQLite database and creates the required schema for the app."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 1. Pipes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nps TEXT NOT NULL,
            outer_diameter_mm REAL NOT NULL,
            wall_thickness_mm REAL NOT NULL,
            weight_kg_m REAL NOT NULL
        )
    ''')

    # 2. Fluids Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fluids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fluid_name TEXT NOT NULL,
            density_kg_m3 REAL NOT NULL
        )
    ''')

    # 3. Canadian Environmental Zoning Table (per National Building Code)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS canadian_zoning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            wind_pressure_kpa REAL NOT NULL,
            snow_load_kpa REAL NOT NULL,
            seismic_zone_factor REAL NOT NULL
        )
    ''')

    # 4. Accessories Table (Valves, Flanges)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            size_nps TEXT NOT NULL,
            weight_kg REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database schema initialized successfully!")

if __name__ == "__main__":
    initialize_database()