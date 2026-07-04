import csv
import uuid
import random
import datetime
import os

def minutes_to_time_str(mins):
    h = (mins // 60) % 24
    m = mins % 60
    return f"{h:02d}:{m:02d}:00"

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    drivers_file = os.path.join(csv_dir, "srilankan_drivers_700k_no_header.csv")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    routes_file = os.path.join(csv_dir, "srilankan_routes_3k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_schedules_15k_no_header.csv")
    
    print("Reading driver IDs...")
    driver_ids = []
    if os.path.exists(drivers_file):
        with open(drivers_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    driver_ids.append(row[0])
    print(f"Loaded {len(driver_ids)} driver IDs.")
    
    print("Reading vehicle IDs...")
    vehicle_ids = []
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    vehicle_ids.append(row[0])
    print(f"Loaded {len(vehicle_ids)} vehicle IDs.")
    
    print("Reading routes...")
    routes = []
    if os.path.exists(routes_file):
        with open(routes_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 7:
                    routes.append({
                        "id": row[0],
                        "duration_mins": int(row[6])
                    })
    print(f"Loaded {len(routes)} routes.")
    
    if not driver_ids or not vehicle_ids or not routes:
        print("Error: Missing required parent data (drivers, vehicles, or routes).")
        return
        
    target_count = 15000
    print(f"Generating {target_count} schedules matching database schema constraints...")
    
    schedules = []
    used_keys = set() # To ensure unique assignments
    
    count = 0
    while count < target_count:
        route = random.choice(routes)
        route_id = route["id"]
        duration = route["duration_mins"]
        
        # Select random driver and vehicle
        driver_id = random.choice(driver_ids)
        vehicle_id = random.choice(vehicle_ids)
        
        # Choose a set of days of the week (1=Mon, 7=Sun)
        day_combo = random.choice([
            [1, 2, 3, 4, 5],      # Weekdays
            [6, 7],               # Weekends
            [1, 2, 3, 4, 5, 6, 7],# Daily
            [1, 3, 5],            # Mon/Wed/Fri
            [2, 4, 6]             # Tue/Thu/Sat
        ])
        # Format as PostgreSQL array string, e.g. "{1,2,3,4,5}"
        days_of_week = "{" + ",".join(map(str, day_combo)) + "}"
        
        # Enforce check constraint: arrival_time > departure_time
        # Max minutes in a day = 1440. Duration is added.
        # We must choose departure minutes so that departure_minutes + duration < 1440 (stays on same day)
        if duration >= 1440:
            duration = 1439 # Cap duration just in case
            
        max_dep_minutes = 1439 - duration
        if max_dep_minutes <= 0:
            dep_minutes = 0
        else:
            dep_minutes = random.randint(0, max_dep_minutes)
            
        arr_minutes = dep_minutes + duration
        
        dep_time_str = minutes_to_time_str(dep_minutes)
        arr_time_str = minutes_to_time_str(arr_minutes)
        
        # Avoid duplicate schedule slots
        key = (route_id, vehicle_id, dep_time_str)
        if key in used_keys:
            continue
            
        used_keys.add(key)
        
        schedule_id = str(uuid.uuid4())
        valid_from = "2025-01-01"
        valid_to = "" # NULL
        is_active = "TRUE" if random.random() < 0.95 else "FALSE"
        
        # Timestamps
        created_days_ago = random.randint(10, 300)
        created_at = (datetime.datetime.now() - datetime.timedelta(days=created_days_ago)).isoformat()
        updated_at = created_at
        
        # Columns: id, route_id, vehicle_id, driver_id, departure_time, arrival_time, days_of_week, valid_from, valid_to, is_active, created_at, updated_at
        schedules.append([
            schedule_id, route_id, vehicle_id, driver_id, dep_time_str, arr_time_str,
            days_of_week, valid_from, valid_to, is_active, created_at, updated_at
        ])
        count += 1
        
        if count % 3000 == 0:
            print(f"Generated {count} records...")
            
    print(f"Writing {len(schedules)} schedules to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(schedules)
        
    print("Success! Schedules file generated.")

if __name__ == "__main__":
    main()
