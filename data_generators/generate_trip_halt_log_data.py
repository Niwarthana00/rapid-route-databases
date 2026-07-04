import csv
import uuid
import random
import datetime
import os

def parse_iso_datetime(dt_str):
    if not dt_str:
        return None
    dt_str = dt_str.replace("T", " ")
    if "+" in dt_str:
        dt_str = dt_str.split("+")[0]
    try:
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.datetime.strptime(dt_str, "%Y-%m-%d")
        except ValueError:
            return None

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    vehicles_file = os.path.join(csv_dir, "srilankan_vehicles_30k_no_header.csv")
    route_halts_file = os.path.join(csv_dir, "srilankan_route_halts_no_header.csv")
    schedules_file = os.path.join(csv_dir, "srilankan_schedules_15k_no_header.csv")
    trips_file = os.path.join(csv_dir, "srilankan_trips_50k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_trip_halt_log_no_header.csv")
    
    print("Reading vehicle capacities...")
    vehicle_capacities = {}
    if os.path.exists(vehicles_file):
        with open(vehicles_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 8:
                    vehicle_capacities[row[0]] = int(row[7]) if row[7].isdigit() else 45
    print(f"Loaded {len(vehicle_capacities)} vehicle capacities.")
    
    print("Reading route halts sequences...")
    route_sequences = {}
    if os.path.exists(route_halts_file):
        with open(route_halts_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6:
                    r_id = row[1]
                    if r_id not in route_sequences:
                        route_sequences[r_id] = []
                    route_sequences[r_id].append({
                        "halt_id": row[2],
                        "sequence_order": int(row[3]),
                        "travel_time": int(row[5])
                    })
                    
    for r_id in route_sequences:
        route_sequences[r_id].sort(key=lambda x: x["sequence_order"])
    print(f"Loaded stop sequences for {len(route_sequences)} routes.")
    
    print("Reading schedules...")
    schedules = {}
    if os.path.exists(schedules_file):
        with open(schedules_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 5:
                    schedules[row[0]] = {
                        "route_id": row[1],
                        "departure_time": row[4],
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
                    trips.append({
                        "id": row[0],
                        "schedule_id": row[1],
                        "vehicle_id": row[2],
                        "trip_date": row[4],
                        "status": row[5],
                        "actual_departure": row[6],
                        "actual_arrival": row[7]
                    })
    print(f"Loaded {len(trips)} trips.")
    
    if not route_sequences or not schedules or not trips:
        print("Error: Missing required parent files.")
        return
        
    print("Generating trip halt logs...")
    logs = []
    count = 0
    
    for t in trips:
        t_id = t["id"]
        sched = schedules.get(t["schedule_id"])
        if not sched:
            continue
            
        r_id = sched["route_id"]
        seq = route_sequences.get(r_id)
        if not seq:
            continue
            
        # Cancelled trips have no logs
        if t["status"] == "CANCELLED":
            continue
            
        # Base datetime for scheduled departure
        trip_date_obj = datetime.datetime.strptime(t["trip_date"], "%Y-%m-%d")
        dep_h, dep_m, dep_s = map(int, sched["departure_time"].split(":"))
        sched_start_dt = datetime.datetime.combine(trip_date_obj, datetime.time(dep_h, dep_m, dep_s))
        
        act_dep_dt = parse_iso_datetime(t["actual_departure"])
        
        # Determine delay from origin
        origin_delay_mins = 0
        if act_dep_dt:
            origin_delay_mins = int((act_dep_dt - sched_start_dt).total_seconds() / 60)
            
        curr_delay_mins = origin_delay_mins
        n_stops = len(seq)
        
        # Get vehicle capacity
        v_id = t["vehicle_id"] or sched["vehicle_id"]
        capacity = vehicle_capacities.get(v_id, 45)
        
        # Track simulated occupancy along stops
        occupancy = 0
        
        for idx, halt in enumerate(seq):
            seq_order = halt["sequence_order"]
            h_id = halt["halt_id"]
            travel_time = halt["travel_time"]
            
            # Determine if this stop should have actual arrival/departure populated
            is_populated = False
            if t["status"] == "COMPLETED":
                is_populated = True
            elif t["status"] in ["IN_PROGRESS", "DELAYED", "DEPARTED"]:
                if idx < max(1, n_stops // 2):
                    is_populated = True
            elif t["status"] == "BOARDING":
                if idx == 0:
                    is_populated = True
                    
            # 1. Scheduled times calculation for delay interpolation
            if idx > 0:
                sched_arr_dt = sched_start_dt + datetime.timedelta(minutes=travel_time)
                
            # 2. Actual arrived_at and departed_at
            arrived_at_str = ""
            departed_at_str = ""
            
            # 3. Passenger flow simulation
            boarded = 0
            alighted = 0
            
            if is_populated:
                if idx == 0:
                    # Origin halt
                    departed_at_str = t["actual_departure"]
                    
                    # Boarding at origin
                    boarded = random.randint(10, max(12, capacity - 8))
                    occupancy = boarded
                elif idx == n_stops - 1:
                    # Destination halt
                    arrived_at_str = t["actual_arrival"]
                    
                    # Alighting at destination (everyone leaves)
                    alighted = occupancy
                    occupancy = 0
                else:
                    # Intermediate halt: accumulate delay randomly
                    if random.random() < 0.75:
                        curr_delay_mins += random.randint(0, 5)
                    else:
                        curr_delay_mins = max(-2, curr_delay_mins - random.randint(0, 3))
                        
                    act_arr_dt_stop = sched_arr_dt + datetime.timedelta(minutes=curr_delay_mins)
                    arrived_at_str = act_arr_dt_stop.strftime("%Y-%m-%d %H:%M:%S+00")
                    
                    layover_actual = random.randint(2, 6)
                    act_dep_dt_stop = act_arr_dt_stop + datetime.timedelta(minutes=layover_actual)
                    departed_at_str = act_dep_dt_stop.strftime("%Y-%m-%d %H:%M:%S+00")
                    
                    # Passenger flow at intermediate halt
                    # Alight some passengers
                    if occupancy > 0:
                        alighted = random.randint(1, max(1, occupancy // 3))
                        occupancy -= alighted
                    # Board some passengers up to capacity
                    max_boardable = capacity - occupancy
                    if max_boardable > 0:
                        boarded = random.randint(1, max(1, max_boardable // 2))
                        occupancy += boarded
            else:
                # For future stops, actual times and flow are empty/0
                pass
                
            log_id = str(uuid.uuid4())
            
            # columns: id, trip_id, halt_id, sequence_order, arrived_at, departed_at, passengers_boarded, passengers_alighted, current_occupancy
            logs.append([
                log_id, t_id, h_id, seq_order, arrived_at_str, departed_at_str,
                boarded, alighted, occupancy
            ])
            
        count += 1
        if count % 10000 == 0:
            print(f"Processed logs for {count} trips...")
            
    print(f"Generated {len(logs)} halt log records.")
    
    print(f"Writing trip halt logs to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(logs)
        
    print("Success! Trip halt log file generated.")

if __name__ == "__main__":
    main()
