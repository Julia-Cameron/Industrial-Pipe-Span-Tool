import sqlite3
import math

def seed_data(db_name="pipe_span_app.db"):
    """Seeds the database cleanly with unique constraints to avoid duplicate records."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create tables with UNIQUE constraints
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nps TEXT UNIQUE NOT NULL,
            outer_diameter_mm REAL NOT NULL,
            wall_thickness_mm REAL NOT NULL,
            weight_kg_m REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fluids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fluid_name TEXT UNIQUE NOT NULL,
            density_kg_m3 REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS canadian_zoning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT UNIQUE NOT NULL,
            wind_pressure_kpa REAL NOT NULL,
            snow_load_kpa REAL NOT NULL,
            seismic_zone_factor REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            size_nps TEXT NOT NULL,
            weight_kg REAL NOT NULL
        )
    ''')

    # Expanded Pipes Data (ASME B36.10)
    pipes_data = [
        ("1\"", 33.4, 2.77, 1.95),
        ("1.5\"", 48.3, 3.68, 3.81),
        ("2\"", 60.3, 3.91, 5.44),
        ("3\"", 88.9, 5.49, 11.29),
        ("4\"", 114.3, 6.02, 16.07),
        ("6\"", 168.3, 7.11, 28.26),
        ("8\"", 219.1, 8.18, 42.55),
        ("10\"", 273.1, 9.27, 60.29),
        ("12\"", 323.8, 9.53, 73.77),
        ("16\"", 406.4, 9.53, 93.27),
        ("24\"", 610.0, 9.53, 141.00)
    ]
    cursor.executemany("INSERT OR IGNORE INTO pipes (nps, outer_diameter_mm, wall_thickness_mm, weight_kg_m) VALUES (?, ?, ?, ?)", pipes_data)

    # Expanded Fluids Data
    fluids_data = [
        ("Water (Fresh)", 1000.0),
        ("Produced Water", 1050.0),
        ("Crude Oil (Light)", 830.0),
        ("Crude Oil (Heavy)", 920.0),
        ("Diesel / Fuel Oil", 850.0),
        ("Jet A-1 Fuel", 804.0),
        ("Natural Gas (High Pressure)", 75.0),
        ("Sour Gas (H2S rich)", 95.0),
        ("Propane (Liquid)", 500.0),
        ("Steam (Saturated)", 10.0)
    ]
    cursor.executemany("INSERT OR IGNORE INTO fluids (fluid_name, density_kg_m3) VALUES (?, ?)", fluids_data)

    # Expanded Canadian Zoning Data (NBC)
    zoning_data = [
        ("Calgary, AB", 0.50, 1.20, 0.15),
        ("Edmonton, AB", 0.40, 1.40, 0.12),
        ("Toronto, ON", 0.55, 0.75, 0.20),
        ("Vancouver, BC", 0.60, 1.90, 0.45),
        ("Montreal, QC", 0.65, 2.10, 0.24),
        ("Ottawa, ON", 0.50, 1.50, 0.20),
        ("Regina, SK", 0.45, 1.30, 0.05),
        ("Winnipeg, MB", 0.45, 1.70, 0.05),
        ("Halifax, NS", 0.85, 2.00, 0.08),
        ("St. John's, NL", 0.95, 2.50, 0.07)
    ]
    cursor.executemany("INSERT OR IGNORE INTO canadian_zoning (region, wind_pressure_kpa, snow_load_kpa, seismic_zone_factor) VALUES (?, ?, ?, ?)", zoning_data)

    # Expanded Accessories Data
    accessories_data = [
        ("Gate Valve", "1\"", 6.2),
        ("Gate Valve", "2\"", 15.5),
        ("Gate Valve", "4\"", 45.0),
        ("Gate Valve", "8\"", 120.0),
        ("Ball Valve", "2\"", 12.0),
        ("Ball Valve", "4\"", 38.0),
        ("Check Valve", "3\"", 22.0),
        ("Check Valve", "6\"", 75.0),
        ("Control Valve", "4\"", 65.0),
        ("Control Valve", "8\"", 180.0)
    ]
    cursor.executemany("INSERT OR IGNORE INTO accessories (item_name, size_nps, weight_kg) VALUES (?, ?, ?)", accessories_data)

    conn.commit()
    conn.close()
    print("Database successfully re-seeded cleanly without duplicates!")

def calculate_max_span(pipe_weight, fluid_weight_distributed, outer_dia, wall_thickness, allowable_stress=20_000_000):
    """Calculates maximum span based on bending stress & deflection limits."""
    od = outer_dia / 1000.0
    id_pipe = (outer_dia - (2 * wall_thickness)) / 1000.0
    
    z_modulus = (math.pi * (od**4 - id_pipe**4)) / (32 * od)
    moment_of_inertia = (math.pi * (od**4 - id_pipe**4)) / 64
    E_modulus = 200e9 
    
    total_load_n_m = (pipe_weight + fluid_weight_distributed) * 9.81
    if total_load_n_m <= 0:
        return 0.0

    span_stress = math.sqrt((8 * allowable_stress * z_modulus) / total_load_n_m)
    max_allowable_sag = 0.0025 
    span_deflection = ((384 * E_modulus * moment_of_inertia * max_allowable_sag) / (5 * total_load_n_m)) ** 0.25
    
    return round(min(span_stress, span_deflection), 2)

if __name__ == "__main__":
    seed_data()