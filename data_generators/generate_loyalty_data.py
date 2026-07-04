import csv
import datetime
import os

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    bookings_file = os.path.join(csv_dir, "srilankan_bookings_300k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_loyalty_no_header.csv")
    
    print("Reading bookings and aggregating loyalty stats...")
    passenger_stats = {}
    
    if os.path.exists(bookings_file):
        with open(bookings_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    passenger_id = row[1]
                    fare_amount = float(row[6])
                    booking_status = row[7]
                    
                    if booking_status == "COMPLETED":
                        if passenger_id not in passenger_stats:
                            passenger_stats[passenger_id] = {
                                "total_trips": 0,
                                "total_spent": 0.0
                            }
                        passenger_stats[passenger_id]["total_trips"] += 1
                        passenger_stats[passenger_id]["total_spent"] += fare_amount
                        
    print(f"Aggregated statistics for {len(passenger_stats)} unique passengers with completed trips.")
    
    loyalty_rows = []
    updated_at_str = datetime.datetime.now().isoformat()
    
    for p_id, stats in passenger_stats.items():
        trips = stats["total_trips"]
        spent = round(stats["total_spent"], 2)
        points = int(spent // 100)
        
        # Determine tier
        if trips <= 5:
            tier = "BRONZE"
        elif trips <= 15:
            tier = "SILVER"
        elif trips <= 30:
            tier = "GOLD"
        else:
            tier = "PLATINUM"
            
        # columns: passenger_id, tier, total_trips, total_spent, points_balance, updated_at
        loyalty_rows.append([
            p_id, tier, trips, spent, points, updated_at_str
        ])
        
    print(f"Writing {len(loyalty_rows)} loyalty records to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(loyalty_rows)
        
    print("Success! Passenger loyalty file generated.")

if __name__ == "__main__":
    main()
