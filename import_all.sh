#!/bin/bash
set -e

CONTAINER_NAME="bus_enterprise_db"
DB_NAME="bus_enterprise"
DB_USER="postgres"

echo "============================================="
echo "   Automated Database Import & Seeding Script"
echo "============================================="

# Check if docker container is running
if [ "$(docker inspect -f '{{.State.Running}}' $CONTAINER_NAME 2>/dev/null)" != "true" ]; then
    echo "Error: Docker container '$CONTAINER_NAME' is not running. Please start it using 'docker-compose up -d' first."
    exit 1
fi

# 1. Clear Existing Data (Truncate Tables)
echo "1. Clearing existing table data (TRUNCATE)..."
truncate_query="TRUNCATE core.drivers, core.driver_documents, core.vehicles, core.vehicle_documents, core.seat_map, core.driver_assignments, core.vehicle_maintenance, core.routes, core.route_halts, fin.fare_rules, biz.schedules, core.passengers, core.passenger_loyalty, biz.trips, biz.trip_halt_log, biz.bookings, fin.payments, fin.fact_trip_revenue, system.notifications CASCADE;"
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "$truncate_query" > /dev/null
echo "   Tables truncated successfully."

# 2. Seed Static Data
echo "2. Seeding static data from 02_final_seed_data.sql..."
docker cp 02_final_seed_data.sql "$CONTAINER_NAME:/tmp/02_final_seed_data.sql"
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /tmp/02_final_seed_data.sql > /dev/null
docker exec -i $CONTAINER_NAME rm /tmp/02_final_seed_data.sql
echo "   Static data seeded successfully."

# 3. Bulk Import CSV Files
echo "3. Importing CSV files..."

declare -a csv_files=(
    "srilankan_drivers_700k_no_header.csv:core.drivers"
    "srilankan_driver_documents_no_header.csv:core.driver_documents"
    "srilankan_vehicles_30k_no_header.csv:core.vehicles"
    "srilankan_vehicle_documents_no_header.csv:core.vehicle_documents"
    "srilankan_seat_maps_no_header.csv:core.seat_map"
    "srilankan_driver_assignments_no_header.csv:core.driver_assignments"
    "srilankan_vehicle_maintenance_no_header.csv:core.vehicle_maintenance"
    "srilankan_routes_3k_no_header.csv:core.routes"
    "srilankan_route_halts_no_header.csv:core.route_halts"
    "srilankan_fare_rules_no_header.csv:fin.fare_rules"
    "srilankan_schedules_15k_no_header.csv:biz.schedules"
    "srilankan_passengers_1m_no_header.csv:core.passengers"
    "srilankan_loyalty_no_header.csv:core.passenger_loyalty"
    "srilankan_trips_50k_no_header.csv:biz.trips"
    "srilankan_trip_halt_log_no_header.csv:biz.trip_halt_log"
    "srilankan_bookings_300k_no_header.csv:biz.bookings"
    "srilankan_payments_300k_no_header.csv:fin.payments"
    "srilankan_fact_trip_revenue_no_header.csv:fin.fact_trip_revenue"
    "srilankan_notifications_no_header.csv:system.notifications"
)

for entry in "${csv_files[@]}"; do
    IFS=":" read -r file table <<< "$entry"
    if [ ! -f "csv_data/$file" ]; then
        echo "Warning: File $file not found. Skipping table $table."
        continue
    fi
    echo "   Importing $file into $table..."
    docker cp "csv_data/$file" "$CONTAINER_NAME:/tmp/$file"
    docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\\copy $table FROM '/tmp/$file' WITH CSV" > /dev/null
    docker exec -i $CONTAINER_NAME rm "/tmp/$file"
done

echo "============================================="
echo " Seeding & CSV Import Completed Successfully!"
echo "============================================="
