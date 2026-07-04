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
    driver_docs_output = os.path.join(csv_dir, "srilankan_driver_documents_no_header.csv")
    vehicle_docs_output = os.path.join(csv_dir, "srilankan_vehicle_documents_no_header.csv")
    
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
        
    created_at = datetime.datetime.now().isoformat()
    
    print("Generating driver documents...")
    d_count = 0
    with open(driver_docs_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for d_id in driver_ids:
            # 1. NIC document
            nic_id = str(uuid.uuid4())
            nic_file = f"/uploads/drivers/{d_id}/nic.pdf"
            nic_issued = (datetime.date(2020, 1, 1) + datetime.timedelta(days=random.randint(0, 1500))).isoformat()
            writer.writerow([
                nic_id, d_id, "NIC", nic_file, nic_issued, "", "TRUE", 
                "admin_system", created_at, created_at
            ])
            d_count += 1
            
            # 2. License document
            lic_id = str(uuid.uuid4())
            lic_file = f"/uploads/drivers/{d_id}/license.pdf"
            lic_issued = (datetime.date(2021, 1, 1) + datetime.timedelta(days=random.randint(0, 1000))).isoformat()
            lic_expires = (datetime.date(2027, 1, 1) + datetime.timedelta(days=random.randint(0, 1000))).isoformat()
            writer.writerow([
                lic_id, d_id, "LICENSE", lic_file, lic_issued, lic_expires, "TRUE", 
                "admin_system", created_at, created_at
            ])
            d_count += 1
            
    print(f"Generated {d_count} driver documents.")
    
    print("Generating vehicle documents...")
    v_count = 0
    with open(vehicle_docs_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for v_id in vehicle_ids:
            # 1. Revenue License
            rev_id = str(uuid.uuid4())
            rev_file = f"/uploads/vehicles/{v_id}/revenue_license.pdf"
            rev_issued = (datetime.date(2025, 1, 1) + datetime.timedelta(days=random.randint(0, 180))).isoformat()
            rev_expires = (datetime.date(2026, 1, 1) + datetime.timedelta(days=random.randint(0, 180))).isoformat()
            writer.writerow([
                rev_id, v_id, "REVENUE_LICENSE", rev_file, rev_issued, rev_expires, "TRUE",
                "admin_system", created_at, created_at
            ])
            v_count += 1
            
            # 2. Insurance
            ins_id = str(uuid.uuid4())
            ins_file = f"/uploads/vehicles/{v_id}/insurance.pdf"
            ins_issued = (datetime.date(2025, 1, 1) + datetime.timedelta(days=random.randint(0, 180))).isoformat()
            ins_expires = (datetime.date(2026, 1, 1) + datetime.timedelta(days=random.randint(0, 180))).isoformat()
            writer.writerow([
                ins_id, v_id, "INSURANCE", ins_file, ins_issued, ins_expires, "TRUE",
                "admin_system", created_at, created_at
            ])
            v_count += 1
            
            # 3. Route Permit
            perm_id = str(uuid.uuid4())
            perm_file = f"/uploads/vehicles/{v_id}/route_permit.pdf"
            perm_issued = (datetime.date(2024, 1, 1) + datetime.timedelta(days=random.randint(0, 365))).isoformat()
            perm_expires = (datetime.date(2026, 1, 1) + datetime.timedelta(days=random.randint(0, 365))).isoformat()
            writer.writerow([
                perm_id, v_id, "ROUTE_PERMIT", perm_file, perm_issued, perm_expires, "TRUE",
                "admin_system", created_at, created_at
            ])
            v_count += 1
            
    print(f"Generated {v_count} vehicle documents.")
    print("Success! Driver and vehicle document files generated.")

if __name__ == "__main__":
    main()
