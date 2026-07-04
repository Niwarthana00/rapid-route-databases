# PowerShell script to automate the entire schema recreation and data import into Docker PostgreSQL database

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Automated Database Import & Seeding Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$ContainerName = "bus_enterprise_db"
$DbName = "bus_enterprise"
$DbUser = "postgres"

# Check if docker container is running
$container_status = docker inspect -f '{{.State.Running}}' $ContainerName 2>$null
if ($container_status -ne "true") {
    Write-Error "Error: Docker container '$ContainerName' is not running. Please start it using 'docker-compose up -d' first."
    exit 1
}

# 1. Clear Existing Data (Truncate Tables)
Write-Host "1. Clearing existing table data (TRUNCATE)..." -ForegroundColor Yellow
$truncate_query = "TRUNCATE core.drivers, core.driver_documents, core.vehicles, core.vehicle_documents, core.seat_map, core.driver_assignments, core.vehicle_maintenance, core.routes, core.route_halts, fin.fare_rules, biz.schedules, core.passengers, core.passenger_loyalty, biz.trips, biz.trip_halt_log, biz.bookings, fin.payments, fin.fact_trip_revenue, system.notifications CASCADE;"
docker exec -i $ContainerName psql -U $DbUser -d $DbName -c "$truncate_query" > $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to truncate tables."
    exit 1
}
Write-Host "   Tables truncated successfully." -ForegroundColor Green

# 2. Seed Static Data (Districts, Halts, Permits)
Write-Host "2. Seeding static data from 02_final_seed_data.sql..." -ForegroundColor Yellow
docker cp 02_final_seed_data.sql "${ContainerName}:/tmp/02_final_seed_data.sql"
docker exec -i $ContainerName psql -U $DbUser -d $DbName -f /tmp/02_final_seed_data.sql > $null
docker exec -i $ContainerName rm /tmp/02_final_seed_data.sql
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to execute 02_final_seed_data.sql"
    exit 1
}
Write-Host "   Static data seeded successfully." -ForegroundColor Green

# 3. Bulk Import CSV Files
Write-Host "3. Importing CSV files..." -ForegroundColor Yellow

$csv_files = @(
    @("srilankan_drivers_700k_no_header.csv", "core.drivers"),
    @("srilankan_driver_documents_no_header.csv", "core.driver_documents"),
    @("srilankan_vehicles_30k_no_header.csv", "core.vehicles"),
    @("srilankan_vehicle_documents_no_header.csv", "core.vehicle_documents"),
    @("srilankan_seat_maps_no_header.csv", "core.seat_map"),
    @("srilankan_driver_assignments_no_header.csv", "core.driver_assignments"),
    @("srilankan_vehicle_maintenance_no_header.csv", "core.vehicle_maintenance"),
    @("srilankan_routes_3k_no_header.csv", "core.routes"),
    @("srilankan_route_halts_no_header.csv", "core.route_halts"),
    @("srilankan_fare_rules_no_header.csv", "fin.fare_rules"),
    @("srilankan_schedules_15k_no_header.csv", "biz.schedules"),
    @("srilankan_passengers_1m_no_header.csv", "core.passengers"),
    @("srilankan_loyalty_no_header.csv", "core.passenger_loyalty"),
    @("srilankan_trips_50k_no_header.csv", "biz.trips"),
    @("srilankan_trip_halt_log_no_header.csv", "biz.trip_halt_log"),
    @("srilankan_bookings_300k_no_header.csv", "biz.bookings"),
    @("srilankan_payments_300k_no_header.csv", "fin.payments"),
    @("srilankan_fact_trip_revenue_no_header.csv", "fin.fact_trip_revenue"),
    @("srilankan_notifications_no_header.csv", "system.notifications")
)

foreach ($item in $csv_files) {
    $file = $item[0]
    $table = $item[1]
    
    if (-Not (Test-Path $file)) {
        Write-Warning "File $file not found. Skipping table $table."
        continue
    }
    
    Write-Host "   Importing $file into $table..." -ForegroundColor Gray
    
    # Copy file to container
    docker cp "csv_data/$file" "${ContainerName}:/tmp/$file"
    
    # Run the bulk COPY command
    docker exec -i $ContainerName psql -U $DbUser -d $DbName -c "\copy $table FROM '/tmp/$file' WITH CSV" > $null
    
    # Clean up file in container to save disk space
    docker exec -i $ContainerName rm "/tmp/$file"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to import $file into $table"
        exit 1
    }
}

Write-Host "=============================================" -ForegroundColor Green
Write-Host " Seeding & CSV Import Completed Successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
