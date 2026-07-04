import csv
import uuid
import random
import datetime
import os

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    passengers_file = os.path.join(csv_dir, "srilankan_passengers_1m_no_header.csv")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    routes_file = os.path.join(csv_dir, "srilankan_routes_3k_no_header.csv")
    schedules_file = os.path.join(csv_dir, "srilankan_schedules_15k_no_header.csv")
    trips_file = os.path.join(csv_dir, "srilankan_trips_50k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_bookings_300k_no_header.csv")
    
    print("Reading passenger IDs...")
    passenger_ids = []
    if os.path.exists(passengers_file):
        with open(passengers_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    passenger_ids.append(row[0])
    print(f"Loaded {len(passenger_ids)} passenger IDs.")
    
    print("Reading vehicles...")
    vehicles = {}
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 10:
                    vehicles[row[0]] = {
                        "total_seats": int(row[7]) if row[7].isdigit() else 45,
                        "has_ac": row[9] == "TRUE"
                    }
    print(f"Loaded {len(vehicles)} vehicles.")
    
    print("Reading routes...")
    routes = {}
    if os.path.exists(routes_file):
        with open(routes_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    routes[row[0]] = {
                        "origin_halt_id": row[3],
                        "destination_halt_id": row[4],
                        "distance_km": float(row[5])
                    }
    print(f"Loaded {len(routes)} routes.")
    
    print("Reading schedules...")
    schedules = {}
    if os.path.exists(schedules_file):
        with open(schedules_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    schedules[row[0]] = {
                        "route_id": row[1],
                        "vehicle_id": row[2]
                    }
    print(f"Loaded {len(schedules)} schedules.")
    
    print("Reading trips...")
    trips = []
    if os.path.exists(trips_file):
        with open(trips_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    # id, schedule_id, vehicle_id, driver_id, trip_date, status, departed_at, arrived_at, delay_reason
                    trips.append({
                        "id": row[0],
                        "schedule_id": row[1],
                        "vehicle_id": row[2],
                        "trip_date": row[4],
                        "status": row[5]
                    })
    print(f"Loaded {len(trips)} trips.")
    
    if not passenger_ids or not vehicles or not routes or not schedules or not trips:
        print("Error: Missing required parent CSV files.")
        return
        
    target_count = 300000
    print(f"Generating {target_count} bookings...")
    
    bookings = []
    occupied_seats = {} # trip_id -> set of seat numbers
    
    count = 0
    # To speed up and ensure we don't get stuck on fully booked trips, we keep track of retries
    retries = 0
    
    while count < target_count and retries < 100000:
        trip = random.choice(trips)
        trip_id = trip["id"]
        
        # Get parent info
        sched = schedules.get(trip["schedule_id"])
        if not sched:
            continue
            
        route = routes.get(sched["route_id"])
        # Fallback to the trip's actual vehicle_id in case it was substituted
        veh = vehicles.get(trip["vehicle_id"]) or vehicles.get(sched["vehicle_id"])
        
        if not route or not veh:
            continue
            
        total_seats = veh["total_seats"]
        has_ac = veh["has_ac"]
        
        # Initialize seat set for trip
        if trip_id not in occupied_seats:
            occupied_seats[trip_id] = set()
            
        # Check capacity
        if len(occupied_seats[trip_id]) >= total_seats:
            retries += 1
            continue
            
        # Pick unique seat number
        seat_num = random.randint(1, total_seats)
        while seat_num in occupied_seats[trip_id]:
            seat_num = random.randint(1, total_seats)
            
        occupied_seats[trip_id].add(seat_num)
        
        # Keep seat_number as an integer
        seat_number = seat_num
        
        # Pick random passenger
        passenger_id = random.choice(passenger_ids)
        
        # Booking date (random datetime 1 to 7 days before trip_date)
        trip_date_obj = datetime.datetime.strptime(trip["trip_date"], "%Y-%m-%d")
        booking_days_before = random.randint(1, 7)
        booking_hours_offset = random.randint(0, 23)
        booking_mins_offset = random.randint(0, 59)
        
        booking_dt = trip_date_obj - datetime.timedelta(
            days=booking_days_before, 
            hours=booking_hours_offset, 
            minutes=booking_mins_offset
        )
        booked_at_str = booking_dt.strftime("%Y-%m-%d %H:%M:%S+00")
        
        # Determine booking status based on trip status
        trip_status = trip["status"]
        if trip_status == "CANCELLED":
            booking_status = "CANCELLED"
        elif trip_status == "COMPLETED":
            booking_status = "COMPLETED" if random.random() < 0.98 else "NO_SHOW"
        else:
            booking_status = "CONFIRMED" if random.random() < 0.95 else "PENDING"
            
        # Cancel details
        cancelled_at_str = ""
        cancel_reason = ""
        if booking_status == "CANCELLED":
            # Cancelled between 1 hour and 2 days after booked_at
            cancel_dt = booking_dt + datetime.timedelta(
                hours=random.randint(1, 48),
                minutes=random.randint(0, 59)
            )
            cancelled_at_str = cancel_dt.strftime("%Y-%m-%d %H:%M:%S+00")
            cancel_reason = random.choice([
                "Travel plans changed",
                "Trip rescheduled",
                "Accidental booking",
                "Bus schedule conflict"
            ])
            
        # Calculate realistic fare based on distance and AC presence
        distance = route["distance_km"]
        if has_ac:
            rate = 13.00
            base = 200.00
        else:
            rate = 6.50
            base = 80.00
            
        fare_amount = round(distance * rate + base, 2)
        
        booking_id = str(uuid.uuid4())
        boarding_halt_id = route["origin_halt_id"]
        alighting_halt_id = route["destination_halt_id"]
        
        # Generate a unique booking reference
        booking_ref = f"BK-{count + 1:07d}-{random.randint(10, 99)}"
        
        # columns: id, passenger_id, trip_id, boarding_halt_id, alighting_halt_id, seat_number, fare_amount, booking_status, booking_ref, booked_at, cancelled_at, cancel_reason
        bookings.append([
            booking_id, passenger_id, trip_id, boarding_halt_id, alighting_halt_id,
            seat_number, fare_amount, booking_status, booking_ref, booked_at_str,
            cancelled_at_str, cancel_reason
        ])
        count += 1
        retries = 0 # reset retries on success
        
        if count % 100000 == 0:
            print(f"Generated {count} records...")
            
    print(f"Generated {len(bookings)} bookings.")
    print(f"Writing bookings to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(bookings)
        
    print("Success! Bookings file generated.")

if __name__ == "__main__":
    main()
