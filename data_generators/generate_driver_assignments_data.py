import csv
import uuid
import os
import random
import datetime

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    drivers_file = os.path.join(csv_dir, "srilankan_drivers_700k_no_header.csv")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_driver_assignments_no_header.csv")
    
    print("Reading drivers...")
    driver_ids = []
    if os.path.exists(drivers_file):
        with open(drivers_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    driver_ids.append(row[0])
    print(f"Loaded {len(driver_ids)} drivers.")
    
    print("Reading vehicles...")
    vehicle_ids = []
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    vehicle_ids.append(row[0])
    print(f"Loaded {len(vehicle_ids)} vehicles.")
    
    if not driver_ids or not vehicle_ids:
        print("Error: Missing parent data files.")
        return
        
    print("Generating driver assignments...")
    assignments = []
    created_at = datetime.datetime.now().isoformat()
    
    # 1. Generate active current assignments for vehicles
    # Since we have 50,000 vehicles, we pair them with the first 50,000 drivers
    num_assigned = min(len(driver_ids), len(vehicle_ids))
    for i in range(num_assigned):
        d_id = driver_ids[i]
        v_id = vehicle_ids[i]
        
        assign_id = str(uuid.uuid4())
        assigned_from = "2025-01-01"
        
        # columns: id, driver_id, vehicle_id, assigned_from, assigned_to, is_current, assigned_by, created_at
        assignments.append([
            assign_id, d_id, v_id, assigned_from, "", "TRUE", "roster_system", created_at
        ])
        
    # 2. Generate some historical assignments for the remaining 50,000 drivers
    # This represents drivers who were previously assigned to those same vehicles
    # Let's say 25,000 of them have historical assignments
    for i in range(num_assigned, min(len(driver_ids), num_assigned + 25000)):
        d_id = driver_ids[i]
        # Pick a random vehicle they were previously assigned to
        v_id = random.choice(vehicle_ids)
        
        assign_id = str(uuid.uuid4())
        assigned_from = "2024-01-01"
        assigned_to = "2024-12-31"
        
        assignments.append([
            assign_id, d_id, v_id, assigned_from, assigned_to, "FALSE", "roster_system", created_at
        ])
        
    print(f"Writing {len(assignments)} driver assignments to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(assignments)
        
    print("Success! Driver assignments file generated.")

if __name__ == "__main__":
    main()
