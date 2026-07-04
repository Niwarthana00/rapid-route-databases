import csv
import uuid
import random
import datetime
import os

def parse_pg_array(arr_str):
    # Parses "{1,2,3,4,5}" into [1, 2, 3, 4, 5]
    arr_str = arr_str.replace("{", "").replace("}", "")
    if not arr_str:
        return []
    return [int(x) for x in arr_str.split(",")]

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    drivers_file = os.path.join(csv_dir, "srilankan_drivers_700k_no_header.csv")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    schedules_file = os.path.join(csv_dir, "srilankan_schedules_15k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_trips_50k_no_header.csv")
    
    print("Reading drivers list for substitutions...")
    driver_ids = []
    if os.path.exists(drivers_file):
        with open(drivers_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    driver_ids.append(row[0])
                    
    print("Reading vehicles list for substitutions...")
    vehicle_ids = []
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    vehicle_ids.append(row[0])
                    
    print("Reading schedules...")
    schedules = []
    if os.path.exists(schedules_file):
        with open(schedules_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 7:
                    # columns: id, route_id, vehicle_id, driver_id, departure_time, arrival_time, days_of_week
                    schedules.append({
                        "id": row[0],
                        "route_id": row[1],
                        "vehicle_id": row[2],
                        "driver_id": row[3],
                        "departure_time": row[4],
                        "arrival_time": row[5],
                        "days_of_week": parse_pg_array(row[6])
                    })
                    
    print(f"Loaded {len(schedules)} schedules.")
    if not schedules or not driver_ids or not vehicle_ids:
        print("Error: Missing required parent files.")
        return
        
    # Define Date Range for seeding: Last 25 days up to today (July 4, 2026)
    end_date = datetime.date(2026, 7, 4)
    start_date = end_date - datetime.timedelta(days=25)
    
    # Generate dates list
    date_list = []
    curr = start_date
    while curr <= end_date:
        date_list.append(curr)
        curr += datetime.timedelta(days=1)
        
    print(f"Expanding schedules over {len(date_list)} days (from {start_date} to {end_date})...")
    
    # To get around 50,000 trips, we process a random subset of schedules
    # 15,000 schedules * 26 days * (5.5 / 7) = ~300,000 total potential trips.
    # To get ~50,000 trips, we need about 16.6% of the schedules.
    # Let's shuffle and select 2,550 schedules.
    random.shuffle(schedules)
    selected_schedules = schedules[:2550]
    
    trips = []
    count = 0
    
    for sched in selected_schedules:
        for dt in date_list:
            # Check if schedule runs on this day of week (Monday=1, Sunday=7)
            dow = dt.isoweekday()
            if dow not in sched["days_of_week"]:
                continue
                
            # Perform substitutions (simulating real fleet operations)
            # 5% chance of vehicle change
            v_id = random.choice(vehicle_ids) if random.random() < 0.05 else sched["vehicle_id"]
            # 8% chance of driver shift change
            d_id = random.choice(driver_ids) if random.random() < 0.08 else sched["driver_id"]
            
            # Determine trip status
            # Today's date is 2026-07-04
            is_today = (dt == end_date)
            
            # Status choices: 'SCHEDULED', 'BOARDING', 'DEPARTED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'DELAYED'
            status = "COMPLETED"
            if is_today:
                # Split today's trips: past times completed, future times scheduled
                dep_hour = int(sched["departure_time"].split(":")[0])
                # Let's assume current hour is 10 AM (based on current local time 10:05 AM)
                if dep_hour < 9:
                    status = "COMPLETED"
                elif dep_hour == 9 or dep_hour == 10:
                    status = random.choice(["IN_PROGRESS", "DELAYED"])
                elif dep_hour == 11:
                    status = "BOARDING"
                else:
                    status = "SCHEDULED"
            else:
                # 2% chance of cancellation for past trips
                if random.random() < 0.02:
                    status = "CANCELLED"
            
            # Calculate actual departure and arrival times for COMPLETED/IN_PROGRESS trips
            actual_dep_str = ""
            actual_arr_str = ""
            
            if status in ["COMPLETED", "IN_PROGRESS", "DELAYED"]:
                # Parse departure time
                dep_h, dep_m, dep_s = map(int, sched["departure_time"].split(":"))
                dep_dt = datetime.datetime.combine(dt, datetime.time(dep_h, dep_m, dep_s))
                
                # Add delay offset (-2 to +15 minutes)
                dep_delay = random.randint(-2, 15)
                act_dep_dt = dep_dt + datetime.timedelta(minutes=dep_delay)
                actual_dep_str = act_dep_dt.strftime("%Y-%m-%d %H:%M:%S+00")
                
                if status == "COMPLETED":
                    # Parse arrival time
                    arr_h, arr_m, arr_s = map(int, sched["arrival_time"].split(":"))
                    arr_dt = datetime.datetime.combine(dt, datetime.time(arr_h, arr_m, arr_s))
                    # Add delay offset (-5 to +25 minutes)
                    arr_delay = random.randint(-5, 25)
                    act_arr_dt = arr_dt + datetime.timedelta(minutes=arr_delay)
                    actual_arr_str = act_arr_dt.strftime("%Y-%m-%d %H:%M:%S+00")
            
            delay_reason = ""
            if status == "DELAYED":
                delay_reason = "Heavy traffic congestion on route"
                
            trip_id = str(uuid.uuid4())
            dep_date_str = dt.isoformat()
            
            # Timestamps
            created_at = datetime.datetime.combine(dt - datetime.timedelta(days=2), datetime.time(12, 0)).isoformat()
            updated_at = created_at
            
            # Columns in database order:
            # id, schedule_id, vehicle_id, driver_id, trip_date, status, departed_at, arrived_at, delay_reason, created_at, updated_at
            trips.append([
                trip_id, sched["id"], v_id, d_id, dep_date_str,
                status, actual_dep_str, actual_arr_str, delay_reason, created_at, updated_at
            ])
            count += 1
            
    print(f"Generated {len(trips)} actual trips.")
    
    print(f"Writing trips to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(trips)
        
    print("Success! Trips file generated.")

if __name__ == "__main__":
    main()
