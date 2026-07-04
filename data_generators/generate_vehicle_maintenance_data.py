import csv
import uuid
import os
import random
import datetime

MAINTENANCE_TASKS = [
    ("ROUTINE", "Engine oil change and filter replacement", 8000, 15000.00),
    ("ROUTINE", "AC cabin filter cleaning and general inspection", 5000, 8500.00),
    ("INSPECTION", "Brake pads check and suspension safety inspection", 4000, 6000.00),
    ("REPAIR", "Brake pads replacement and brake fluid top-up", 12000, 25000.00),
    ("REPAIR", "Clutch plate adjustment and gear synchronization check", 15000, 45000.00),
    ("REPAIR", "Front tire replacement (pair) and wheel alignment", 20000, 95000.00),
    ("ROUTINE", "Full body wash, interior vacuuming and leaf spring lubrication", 6000, 12000.00)
]

WORKSHOPS = [
    "Dimo Service Center, Colombo",
    "Lanka Leyland Workshop, Yakkala",
    "Tata Motors Service Station, Kurunegala",
    "Toyota Lanka Center, Wattala",
    "Isuru Auto Engineering, Kandy",
    "Jayasinghe Motors, Galle",
    "Ruhunu Auto Services, Matara"
]

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_vehicle_maintenance_no_header.csv")
    
    print("Reading vehicles...")
    vehicles = []
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 12:
                    # id, registration_number, chassis_number, engine_number, make, model, year, total_seats, fuel_type, has_ac, is_active, odometer_km
                    vehicles.append({
                        "id": row[0],
                        "year": int(row[6]) if row[6].isdigit() else 2015,
                        "odometer": float(row[11]) if row[11].replace(".","",1).isdigit() else 150000.0
                    })
    print(f"Loaded {len(vehicles)} vehicles.")
    
    if not vehicles:
        print("Error: Missing vehicles file.")
        return
        
    print("Generating maintenance logs...")
    logs = []
    created_at = datetime.datetime.now().isoformat()
    
    for v in vehicles:
        v_id = v["id"]
        year = v["year"]
        odo_max = v["odometer"]
        
        # Decide how many service logs to generate (1 to 3 depending on vehicle age)
        num_logs = random.randint(1, 3)
        
        # Odometer steps backwards for older services
        curr_odo = odo_max
        curr_date = datetime.date(2026, 6, 1)
        
        for i in range(num_logs):
            # Pick a task
            task_type, desc, odo_interval, base_cost = random.choice(MAINTENANCE_TASKS)
            
            # Service odometer
            curr_odo -= random.randint(odo_interval - 2000, odo_interval + 2000)
            if curr_odo <= 0:
                curr_odo = random.randint(5000, 15000)
                
            # Service date
            curr_date -= datetime.timedelta(days=random.randint(60, 180))
            if curr_date.year < year:
                curr_date = datetime.date(year, random.randint(1, 12), random.randint(1, 28))
                
            service_date_str = curr_date.isoformat()
            next_service_date_str = (curr_date + datetime.timedelta(days=random.randint(90, 180))).isoformat()
            
            cost = round(base_cost * random.uniform(0.9, 1.25), 2)
            performed_by = random.choice(WORKSHOPS)
            m_id = str(uuid.uuid4())
            
            # columns: id, vehicle_id, maintenance_type, description, odometer_at_service, cost, service_date, next_service_date, performed_by, created_at
            logs.append([
                m_id, v_id, task_type, desc, round(curr_odo, 2), cost,
                service_date_str, next_service_date_str, performed_by, created_at
            ])
            
            # Stop if service date goes before manufacturing year
            if curr_date.year <= year:
                break
                
    print(f"Writing {len(logs)} maintenance logs to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(logs)
        
    print("Success! Vehicle maintenance log file generated.")

if __name__ == "__main__":
    main()
