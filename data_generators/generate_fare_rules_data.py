import csv
import uuid
import os
import random

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    routes_file = os.path.join(csv_dir, "srilankan_routes_3k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_fare_rules_no_header.csv")
    
    print("Reading routes...")
    routes = []
    if os.path.exists(routes_file):
        with open(routes_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 5:
                    routes.append({
                        "id": row[0],
                        "origin_halt_id": row[3],
                        "destination_halt_id": row[4]
                    })
    print(f"Loaded {len(routes)} routes.")
    
    if not routes:
        print("Error: No routes found.")
        return
        
    print("Generating fare rules...")
    fare_rules = []
    count = 0
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        for r in routes:
            route_id = r["id"]
            orig = r["origin_halt_id"]
            dest = r["destination_halt_id"]
            
            # Create bidirectional rules
            pairs = [(orig, dest), (dest, orig)]
            
            for from_halt, to_halt in pairs:
                # Calculate realistic base fares and per km rates
                # Normal buses: base = 80 LKR, rate = 6.50 LKR/km
                # AC buses: base = 200 LKR, rate = 13.00 LKR/km
                # We will define a general rule for each route. Some will be AC surcharged.
                has_ac_surcharge = "TRUE" if random.random() < 0.40 else "FALSE"
                ac_surcharge_amount = round(random.uniform(50.00, 150.00), 2) if has_ac_surcharge == "TRUE" else 0.00
                
                base_fare = round(random.uniform(70.00, 100.00), 2)
                per_km_rate = round(random.uniform(5.50, 7.50), 4)
                
                rule_id = str(uuid.uuid4())
                effective_from = "2025-01-01"
                effective_to = "" # NULL in Postgres
                
                # columns: id, route_id, from_halt_id, to_halt_id, base_fare, per_km_rate, has_ac_surcharge, ac_surcharge_amount, effective_from, effective_to
                writer.writerow([
                    rule_id, route_id, from_halt, to_halt, base_fare, 
                    per_km_rate, has_ac_surcharge, ac_surcharge_amount, 
                    effective_from, effective_to
                ])
                count += 1
                
    print(f"Success! Generated {count} fare rules and saved to srilankan_fare_rules_no_header.csv")

if __name__ == "__main__":
    main()
