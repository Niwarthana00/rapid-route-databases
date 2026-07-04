import csv
import uuid
import os
import datetime

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    schedules_file = os.path.join(csv_dir, "srilankan_schedules_15k_no_header.csv")
    trips_file = os.path.join(csv_dir, "srilankan_trips_50k_no_header.csv")
    bookings_file = os.path.join(csv_dir, "srilankan_bookings_300k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_fact_trip_revenue_no_header.csv")
    
    print("Reading vehicle capacities...")
    vehicle_capacities = {}
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    vehicle_capacities[row[0]] = int(row[7]) if row[7].isdigit() else 45
    print(f"Loaded {len(vehicle_capacities)} vehicle capacities.")
    
    print("Reading schedules to map routes...")
    schedule_routes = {}
    if os.path.exists(schedules_file):
        with open(schedules_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    schedule_routes[row[0]] = row[1]
    print(f"Loaded {len(schedule_routes)} schedule route mappings.")
    
    print("Aggregating bookings by trip...")
    trip_bookings = {}
    if os.path.exists(bookings_file):
        with open(bookings_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    # id, passenger_id, trip_id, boarding_halt_id, alighting_halt_id, seat_number, fare_amount, booking_status
                    t_id = row[2]
                    fare = float(row[6])
                    status = row[7]
                    
                    if t_id not in trip_bookings:
                        trip_bookings[t_id] = []
                    trip_bookings[t_id].append({
                        "fare": fare,
                        "status": status
                    })
    print(f"Aggregated bookings for {len(trip_bookings)} unique trips.")
    
    print("Reading trips and computing revenue metrics...")
    revenue_rows = []
    computed_at = datetime.datetime.now().isoformat()
    
    if os.path.exists(trips_file):
        with open(trips_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    # id, schedule_id, vehicle_id, driver_id, trip_date, status, departed_at, arrived_at, delay_reason
                    t_id = row[0]
                    sched_id = row[1]
                    v_id = row[2]
                    d_id = row[3]
                    trip_date = row[4]
                    
                    route_id = schedule_routes.get(sched_id)
                    if not route_id:
                        continue # Skip trips without valid routes
                        
                    # Aggregate stats
                    t_bk_list = trip_bookings.get(t_id, [])
                    
                    total_bookings = len([b for b in t_bk_list if b["status"] != "CANCELLED"])
                    cancellations = len([b for b in t_bk_list if b["status"] == "CANCELLED"])
                    no_shows = len([b for b in t_bk_list if b["status"] == "NO_SHOW"])
                    
                    # Revenue from successful bookings (completed, confirmed, no_show)
                    successful_bookings = [b for b in t_bk_list if b["status"] in ["COMPLETED", "CONFIRMED", "NO_SHOW"]]
                    total_revenue = round(sum(b["fare"] for b in successful_bookings), 2)
                    
                    # Avg fare
                    avg_fare = round(total_revenue / len(successful_bookings), 2) if len(successful_bookings) > 0 else ""
                    
                    # Occupancy rate
                    capacity = vehicle_capacities.get(v_id, 45)
                    occupancy_rate = round((total_bookings / capacity) * 100.0, 2)
                    
                    rev_id = str(uuid.uuid4())
                    
                    # columns: id, trip_id, route_id, vehicle_id, driver_id, trip_date, total_bookings, total_revenue, avg_fare, occupancy_rate, cancellations, no_shows, computed_at
                    revenue_rows.append([
                        rev_id, t_id, route_id, v_id, d_id, trip_date,
                        total_bookings, total_revenue, avg_fare, occupancy_rate,
                        cancellations, no_shows, computed_at
                    ])
                    
    print(f"Writing {len(revenue_rows)} fact trip revenue rows...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(revenue_rows)
        
    print("Success! Fact trip revenue file generated.")

if __name__ == "__main__":
    main()
