import subprocess
import os
import sys

def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout

def main():
    container = "bus_enterprise_db"
    db_name = "bus_enterprise"
    db_user = "postgres"
    
    print("====================================================")
    print("   Python Automated Database Seeding & CSV Import   ")
    print("====================================================")
    
    # Check if container is running
    try:
        ps_out = run_command(["docker", "ps", "-q", "-f", f"name={container}"])
        if not ps_out.strip():
            print(f"Error: Docker container '{container}' is not running. Start it with 'docker-compose up -d' first.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: Could not verify Docker container status. Make sure Docker is running.", file=sys.stderr)
        sys.exit(1)

    # 1. Clear Existing Data (Truncate Tables)
    print("\n1. Clearing existing table data (TRUNCATE)...")
    truncate_query = (
        "TRUNCATE core.drivers, core.driver_documents, core.vehicles, core.vehicle_documents, "
        "core.seat_map, core.driver_assignments, core.vehicle_maintenance, core.routes, core.route_halts, "
        "fin.fare_rules, biz.schedules, core.passengers, core.passenger_loyalty, biz.trips, "
        "biz.trip_halt_log, biz.bookings, fin.payments, fin.fact_trip_revenue, system.notifications CASCADE;"
    )
    run_command(["docker", "exec", "-i", container, "psql", "-U", db_user, "-d", db_name, "-c", truncate_query])
    print("   Tables truncated successfully.")
    
    # 2. Seed Static Data (Districts, Halts, Permits)
    print("\n2. Seeding static data from 02_final_seed_data.sql...")
    run_command(["docker", "cp", "02_final_seed_data.sql", f"{container}:/tmp/02_final_seed_data.sql"])
    run_command(["docker", "exec", "-i", container, "psql", "-U", db_user, "-d", db_name, "-f", "/tmp/02_final_seed_data.sql"])
    run_command(["docker", "exec", "-i", container, "rm", "/tmp/02_final_seed_data.sql"])
    print("   Static data seeded successfully.")
    
    # 3. Bulk Import CSV Files
    print("\n3. Importing CSV files...")
    csv_files = [
        ("srilankan_drivers_700k_no_header.csv", "core.drivers"),
        ("srilankan_driver_documents_no_header.csv", "core.driver_documents"),
        ("srilankan_vehicles_30k_no_header.csv", "core.vehicles"),
        ("srilankan_vehicle_documents_no_header.csv", "core.vehicle_documents"),
        ("srilankan_seat_maps_no_header.csv", "core.seat_map"),
        ("srilankan_driver_assignments_no_header.csv", "core.driver_assignments"),
        ("srilankan_vehicle_maintenance_no_header.csv", "core.vehicle_maintenance"),
        ("srilankan_routes_3k_no_header.csv", "core.routes"),
        ("srilankan_route_halts_no_header.csv", "core.route_halts"),
        ("srilankan_fare_rules_no_header.csv", "fin.fare_rules"),
        ("srilankan_schedules_15k_no_header.csv", "biz.schedules"),
        ("srilankan_passengers_1m_no_header.csv", "core.passengers"),
        ("srilankan_loyalty_no_header.csv", "core.passenger_loyalty"),
        ("srilankan_trips_50k_no_header.csv", "biz.trips"),
        ("srilankan_trip_halt_log_no_header.csv", "biz.trip_halt_log"),
        ("srilankan_bookings_300k_no_header.csv", "biz.bookings"),
        ("srilankan_payments_300k_no_header.csv", "fin.payments"),
        ("srilankan_fact_trip_revenue_no_header.csv", "fin.fact_trip_revenue"),
        ("srilankan_notifications_no_header.csv", "system.notifications")
    ]
    
    for file, table in csv_files:
        file_path = os.path.join("csv_data", file)
        if not os.path.exists(file_path):
            print(f"   Warning: File '{file_path}' not found. Skipping table '{table}'.")
            continue
            
        print(f"   Importing {file} into {table}...")
        # Copy file to container
        run_command(["docker", "cp", file_path, f"{container}:/tmp/{file}"])
        # Run copy query
        copy_query = f"\\copy {table} FROM '/tmp/{file}' WITH CSV"
        run_command(["docker", "exec", "-i", container, "psql", "-U", db_user, "-d", db_name, "-c", copy_query])
        # Remove file from container
        run_command(["docker", "exec", "-i", container, "rm", f"/tmp/{file}"])
        
    print("\n====================================================")
    print(" Seeding & CSV Import Completed Successfully!       ")
    print("====================================================")

if __name__ == "__main__":
    main()
