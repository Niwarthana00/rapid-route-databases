import csv
import uuid
import os

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_seat_maps_no_header.csv")
    
    print("Reading vehicles...")
    vehicles = []
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    vehicles.append({
                        "id": row[0],
                        "total_seats": int(row[7]) if row[7].isdigit() else 45
                    })
    print(f"Loaded {len(vehicles)} vehicles.")
    
    if not vehicles:
        print("Error: No vehicles found.")
        return
        
    print("Generating seat maps...")
    count = 0
    
    # Setup CSV writing
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        for v in vehicles:
            v_id = v["id"]
            total_seats = v["total_seats"]
            
            for seat_num in range(1, total_seats + 1):
                # Determine seat type
                if seat_num in [1, 2]:
                    seat_type = "FRONT_ROW"
                elif seat_num in [3, 4]:
                    seat_type = "DISABLED"
                elif seat_num in range(5, 11):
                    seat_type = "PREMIUM"
                else:
                    seat_type = "STANDARD"
                    
                seat_id = str(uuid.uuid4())
                writer.writerow([seat_id, v_id, seat_num, seat_type, "TRUE"])
                count += 1
                
            if count % 200000 == 0:
                print(f"Generated {count} seats...")
                
    print(f"Success! Generated {count} seat map records and saved to srilankan_seat_maps_no_header.csv")

if __name__ == "__main__":
    main()
