import os
import csv
import uuid
import random
import datetime

# Realistic Sri Lankan Bus/Coach Make & Model combinations
VEHICLE_MODELS = [
    # (Make, Model, Seats Range, has_ac probability, Fuel Type)
    ("Ashok Leyland", "Viking", [42, 49, 54], 0.10, "DIESEL"),
    ("Ashok Leyland", "Falcon", [49, 54], 0.15, "DIESEL"),
    ("Tata", "LPO 1613", [42, 54], 0.05, "DIESEL"),
    ("Tata", "LPO 1512", [42, 49], 0.05, "DIESEL"),
    ("Isuzu", "Journey", [29, 32, 35], 0.40, "DIESEL"),
    ("Mitsubishi Fuso", "Rosa", [26, 29], 0.50, "DIESEL"),
    ("Toyota", "Coaster", [26, 29], 0.80, "DIESEL"),
    ("Toyota", "HiAce", [14, 15], 0.95, "DIESEL"),
    ("Micro", "Optima", [29, 32], 0.60, "DIESEL"),
    ("Hino", "Liesse", [26, 29], 0.40, "DIESEL"),
    ("Yutong", "ZK6122H", [45, 49], 1.00, "DIESEL"), # Luxury highway coaches
    ("BYD", "K9", [31, 39], 1.00, "ELECTRIC") # Electric city buses
]

PROVINCES = [
    ("WP", 0.60), # Western (60%)
    ("CP", 0.10), # Central (10%)
    ("SP", 0.10), # Southern (10%)
    ("NW", 0.05), # North Western (5%)
    ("SG", 0.05), # Sabaragamuwa (5%)
    ("NC", 0.03), # North Central (3%)
    ("Uva", 0.03),# Uva (3%)
    ("NP", 0.02), # Northern (2%)
    ("EP", 0.02)  # Eastern (2%)
]

# Common bus category letters in Sri Lanka
CATEGORY_LETTERS = ["NA", "NB", "NC", "ND", "NE", "NF", "NG", "NH", "PA", "PB", "PC", "PD", "PE", "PF", "PG", "PH", "ZA", "ZB", "ZC"]

def main():
    target_count = 50000
    output_csv = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    
    print(f"Generating {target_count} realistic Sri Lankan vehicle records...")
    
    # We will generate unique registration numbers systematically
    # Since we need 1,000,000 unique registration numbers, we can use a set to track
    used_regs = set()
    
    count = 0
    
    # Setup CSV writing
    # Columns in core.vehicles: id, registration_number, chassis_number, engine_number, make, model, year, total_seats, fuel_type, has_ac, is_active, odometer_km, created_at, updated_at, deleted_at
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        while count < target_count:
            # 1. Generate unique registration number
            # WP NB-4589 or SP ND-1203
            reg_found = False
            for attempt in range(100):
                # Pick province
                prov_list = [p[0] for p in PROVINCES]
                weights = [p[1] for p in PROVINCES]
                prov = random.choices(prov_list, weights=weights, k=1)[0]
                
                # Pick letters
                let = random.choice(CATEGORY_LETTERS)
                
                # Pick digits
                num = random.randint(1000, 9999)
                
                reg = f"{prov} {let}-{num}"
                if reg not in used_regs:
                    used_regs.add(reg)
                    reg_number = reg
                    reg_found = True
                    break
                    
            if not reg_found:
                continue # Retry record generation on collision
                
            # 2. Vehicle details from models list
            model_info = random.choice(VEHICLE_MODELS)
            make = model_info[0]
            model = model_info[1]
            total_seats = random.choice(model_info[2])
            has_ac = "TRUE" if random.random() < model_info[3] else "FALSE"
            
            # Fuel type
            fuel_type = model_info[4]
            # Add small random variation for alternative fuels if diesel
            if fuel_type == "DIESEL" and random.random() < 0.05:
                fuel_type = random.choice(["CNG", "HYBRID", "PETROL"])
                
            # 3. Manufacture Year (2000 to 2026)
            year = random.randint(2000, 2026)
            
            # 4. Engine & Chassis Numbers (Guarantee uniqueness using sequential IDs)
            # Chassis starts with a common manufacturer code followed by unique sequence
            chassis_num = f"MHF1A15A1E1{count+1000000:07d}"
            engine_num = f"6D16T{count+1000000:07d}"
            
            # 5. Odometer (km driven) - vehicles from 2026 have low km, older have higher
            age_years = 2026 - year
            avg_annual_km = random.randint(30000, 80000)
            odometer_km = round(max(500.0, age_years * avg_annual_km + random.randint(-15000, 15000)), 2)
            
            # 6. Status and Metadata
            vehicle_id = str(uuid.uuid4())
            is_active = "TRUE" if random.random() < 0.95 else "FALSE" # 95% active fleet
            
            # Timestamps
            created_days_ago = random.randint(10, 1500)
            created_at = (datetime.datetime.now() - datetime.timedelta(days=created_days_ago, hours=random.randint(0, 23))).isoformat()
            updated_at = created_at
            deleted_at = "" # Empty for NULL
            
            # Write to CSV (no header!)
            # id, registration_number, chassis_number, engine_number, make, model, year, total_seats, fuel_type, has_ac, is_active, odometer_km, created_at, updated_at, deleted_at
            writer.writerow([
                vehicle_id, reg_number, chassis_num, engine_num, make, model, year,
                total_seats, fuel_type, has_ac, is_active, odometer_km, created_at, updated_at, deleted_at
            ])
            
            count += 1
            if count % 200000 == 0:
                print(f"Generated {count} records...")
                
    print(f"Success! Generated {count} vehicles and saved to {output_csv}")

if __name__ == "__main__":
    main()
