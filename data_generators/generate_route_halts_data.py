import csv
import uuid
import random
import datetime
import math
import os

# Helper to parse SQL VALUES clause character-by-character (state machine)
def parse_sql_values(val_part):
    values = []
    current = []
    in_quotes = False
    escape = False
    i = 0
    while i < len(val_part):
        char = val_part[i]
        if in_quotes:
            if escape:
                current.append(char)
                escape = False
            elif char == "'" and i + 1 < len(val_part) and val_part[i+1] == "'":
                current.append("'")
                i += 1
            elif char == "'":
                in_quotes = False
            elif char == "\\":
                escape = True
            else:
                current.append(char)
        else:
            if char == "'":
                in_quotes = True
            elif char == ",":
                values.append("".join(current).strip())
                current = []
            else:
                current.append(char)
        i += 1
    values.append("".join(current).strip())
    return values

# Calculate distance on Earth's surface
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    seed_file = os.path.join(workspace, "02_final_seed_data.sql")
    routes_file = os.path.join(csv_dir, "srilankan_routes_3k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_route_halts_no_header.csv")
    
    print("Reading halts coordinates...")
    halts = {}
    
    if os.path.exists(seed_file):
        with open(seed_file, "r", encoding="utf-8") as f:
            for line in f:
                if "INSERT INTO core.halts" in line:
                    start = line.find("VALUES (")
                    if start != -1:
                        end = line.rstrip().rfind(")")
                        val_part = line[start + 8 : end]
                        tokens = parse_sql_values(val_part)
                        if len(tokens) >= 7:
                            try:
                                h_id = tokens[0]
                                halts[h_id] = {
                                    "lat": float(tokens[5]),
                                    "lon": float(tokens[6]),
                                    "name": tokens[2]
                                }
                            except ValueError:
                                pass
                                
    print(f"Loaded {len(halts)} halts.")
    
    print("Reading routes...")
    routes = []
    if os.path.exists(routes_file):
        with open(routes_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 7:
                    # id, route_number, name, origin_halt_id, destination_halt_id, distance_km, duration_mins
                    routes.append({
                        "id": row[0],
                        "origin_halt_id": row[3],
                        "destination_halt_id": row[4],
                        "distance_km": float(row[5]),
                        "duration_mins": int(row[6])
                    })
                    
    print(f"Loaded {len(routes)} routes.")
    if not halts or not routes:
        print("Error: Missing parent halts or routes data.")
        return
        
    print("Generating route halts stop sequences...")
    route_halts = []
    
    # Pre-index halts by grid or simple structure to optimize searching (or do bounding box search)
    halts_list = list(halts.items()) # list of (h_id, dict)
    
    route_count = 0
    for r in routes:
        r_id = r["id"]
        orig_id = r["origin_halt_id"]
        dest_id = r["destination_halt_id"]
        total_dist = r["distance_km"]
        total_dur = r["duration_mins"]
        
        orig_halt = halts.get(orig_id)
        dest_halt = halts.get(dest_id)
        
        if not orig_halt or not dest_halt:
            # Fallback if halt not found: write only origin and destination
            # Origin
            route_halts.append([str(uuid.uuid4()), r_id, orig_id, 0, 0.00, 0])
            # Destination
            route_halts.append([str(uuid.uuid4()), r_id, dest_id, 1, total_dist, total_dur])
            continue
            
        orig_lat, orig_lon = orig_halt["lat"], orig_halt["lon"]
        dest_lat, dest_lon = dest_halt["lat"], dest_halt["lon"]
        
        # Bounding box of route path
        min_lat, max_lat = min(orig_lat, dest_lat), max(orig_lat, dest_lat)
        min_lon, max_lon = min(orig_lon, dest_lon), max(orig_lon, dest_lon)
        
        # Add padding to bounding box
        padding = 0.05
        min_lat -= padding
        max_lat += padding
        min_lon -= padding
        max_lon += padding
        
        # Find candidates within bounding box
        candidates = []
        straight_len = haversine(orig_lat, orig_lon, dest_lat, dest_lon)
        
        for h_id, h in halts_list:
            if h_id == orig_id or h_id == dest_id:
                continue
            if min_lat <= h["lat"] <= max_lat and min_lon <= h["lon"] <= max_lon:
                # Check how close it is to the straight line connecting origin and destination
                # Simple distance: sum of distances to origin and destination should be close to straight line length
                d1 = haversine(orig_lat, orig_lon, h["lat"], h["lon"])
                d2 = haversine(h["lat"], h["lon"], dest_lat, dest_lon)
                # If it's along the way, d1 + d2 shouldn't exceed straight_len * 1.35
                if d1 + d2 <= max(straight_len * 1.35, straight_len + 5.0):
                    candidates.append((h_id, d1, d1 / max(0.1, d1 + d2)))
                    
        # Select 2 to 5 random intermediate halts
        num_stops = random.randint(2, 5)
        if len(candidates) > num_stops:
            selected = random.sample(candidates, num_stops)
        else:
            selected = candidates
            
        # Sort selected halts by distance to origin to ensure correct sequence ordering
        selected.sort(key=lambda x: x[1])
        
        # Sequence of halts: Origin, Selected halts, Destination
        seq = []
        # Origin
        seq.append((orig_id, 0.0, 0))
        
        # Intermediate halts (interpolate distance and duration)
        # We enforce strict monotonicity
        last_d = 0.0
        last_t = 0
        
        for idx, (h_id, dist_to_orig, ratio) in enumerate(selected):
            # Interpolated distance
            d_from_orig = round(total_dist * ratio, 2)
            # Interpolated travel time
            t_from_orig = int(total_dur * ratio)
            
            # Guarantee strictly increasing values
            if d_from_orig <= last_d:
                d_from_orig = round(last_d + random.uniform(0.5, 1.5), 2)
            if t_from_orig <= last_t:
                t_from_orig = last_t + random.randint(1, 4)
                
            # If distance exceeds total distance, cap it
            if d_from_orig >= total_dist:
                d_from_orig = round(total_dist - 0.5, 2)
            if t_from_orig >= total_dur:
                t_from_orig = total_dur - 2
                
            if d_from_orig > last_d and t_from_orig > last_t:
                seq.append((h_id, d_from_orig, t_from_orig))
                last_d = d_from_orig
                last_t = t_from_orig
                
        # Destination
        # Guarantee it is greater than last intermediate stop
        dest_seq_num = len(seq)
        seq.append((dest_id, total_dist, total_dur))
        
        # Write sequence to route_halts rows
        for seq_idx, (h_id, d_from_orig, t_from_orig) in enumerate(seq):
            rh_id = str(uuid.uuid4())
            route_halts.append([
                rh_id, r_id, h_id, seq_idx, d_from_orig, t_from_orig
            ])
            
        route_count += 1
        if route_count % 1000 == 0:
            print(f"Processed sequences for {route_count} routes...")
            
    print(f"Generated {len(route_halts)} total stop sequence records.")
    
    print(f"Writing route halts to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(route_halts)
        
    print("Success! Route halts file generated.")

if __name__ == "__main__":
    main()
