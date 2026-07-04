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
                i += 1 # skip the second quote
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

# Calculate straight-line distance on Earth's surface
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Extract the city/town name from a halt's name
def get_town(name):
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        if parts[-1] == "Sri Lanka":
            parts.pop()
        return parts[-1]
    for kw in ["Central Bus Stand", "Bus Stand", "Bus Stop", "Depot", "Junction", "bus stop", "bus holt"]:
        if kw in name:
            return name.split(kw)[0].strip()
    return name.strip()

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    seed_file = os.path.join(workspace, "02_final_seed_data.sql")
    output_csv = os.path.join(csv_dir, "srilankan_routes_3k_no_header.csv")
    
    print("Reading halts data from 02_final_seed_data.sql...")
    halts = []
    
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
                                halts.append({
                                    "id": tokens[0],
                                    "name": tokens[2],
                                    "lat": float(tokens[5]),
                                    "lon": float(tokens[6])
                                })
                            except ValueError:
                                pass
                                
    total_halts = len(halts)
    print(f"Loaded {total_halts} halts from seed SQL file.")
    
    if total_halts < 2:
        print("Error: Not enough halts to generate routes.")
        return
        
    target_count = 3000
    print(f"Generating {target_count} unique realistic routes...")
    
    routes = []
    used_route_nums = set()
    used_halt_pairs = set()
    
    count = 0
    while count < target_count:
        # Pick random origin and destination halts
        orig = random.choice(halts)
        dest = random.choice(halts)
        
        # Ensure origin and destination are different and unique as a pair
        if orig["id"] == dest["id"]:
            continue
            
        pair_key = (orig["id"], dest["id"])
        reverse_pair_key = (dest["id"], orig["id"])
        if pair_key in used_halt_pairs or reverse_pair_key in used_halt_pairs:
            continue
            
        # Calculate realistic distance (Haversine * road winding factor 1.2 to 1.45)
        straight_dist = haversine(orig["lat"], orig["lon"], dest["lat"], dest["lon"])
        # If halts are extremely close, enforce a minimum distance
        distance_km = round(max(1.5, straight_dist * random.uniform(1.2, 1.45)), 2)
        
        # Estimate duration based on realistic Sri Lankan bus speeds (30 km/h for short routes, up to 55 km/h for highways)
        if distance_km > 100:
            speed = random.uniform(42.0, 55.0) # Highway/major road speed
        else:
            speed = random.uniform(30.0, 42.0) # Local/city speed
            
        duration_mins = int((distance_km / speed) * 60)
        duration_mins = max(10, duration_mins) # minimum 10 mins
        
        # Generate unique route number (e.g. 001, 120-A, 138/2, EX005)
        route_found = False
        for attempt in range(100):
            r_type = random.random()
            if r_type < 0.65:
                # Regular route (e.g. 120, 002)
                num = f"{random.randint(1, 999):03d}"
            elif r_type < 0.85:
                # Sub-route (e.g. 138/2, 122/A)
                num = f"{random.randint(1, 500):03d}/{random.choice(['1', '2', 'A', 'B'])}"
            else:
                # Highway Express (e.g. EX1-5, EX002)
                num = f"EX{random.randint(1, 99):02d}"
                
            if num not in used_route_nums:
                used_route_nums.add(num)
                route_num = num
                route_found = True
                break
                
        if not route_found:
            continue
            
        # Extract towns for route name
        orig_town = get_town(orig["name"])
        dest_town = get_town(dest["name"])
        route_name = f"{orig_town} - {dest_town}"
        
        # Unique check passed, add to list
        used_halt_pairs.add(pair_key)
        
        route_id = str(uuid.uuid4())
        is_active = "TRUE" if random.random() < 0.98 else "FALSE" # 98% active routes
        
        # Timestamps
        created_days_ago = random.randint(10, 1000)
        created_at = (datetime.datetime.now() - datetime.timedelta(days=created_days_ago, hours=random.randint(0, 23))).isoformat()
        updated_at = created_at
        
        routes.append([
            route_id, route_num, route_name, orig["id"], dest["id"],
            distance_km, duration_mins, is_active, created_at, updated_at
        ])
        count += 1
        
    print(f"Writing {len(routes)} routes to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(routes)
        
    print("Success! Realistic routes file generated.")

if __name__ == "__main__":
    main()
