import csv
import uuid
import os
import random
import datetime

def main():
    # Dynamic relative path resolution for workspace structure
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace = os.path.dirname(script_dir)
csv_dir = os.path.join(workspace, "csv_data")
    bookings_file = os.path.join(csv_dir, "srilankan_bookings_300k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_notifications_no_header.csv")
    
    print("Reading bookings...")
    notifications = []
    
    if os.path.exists(bookings_file):
        with open(bookings_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            count = 0
            for row in reader:
                if len(row) >= 10:
                    # id, passenger_id, trip_id, boarding_halt_id, alighting_halt_id, seat_number, fare_amount, booking_status, booking_ref, booked_at
                    b_id = row[0]
                    p_id = row[1]
                    b_status = row[7]
                    b_ref = row[8]
                    booked_at = row[9]
                    
                    # Channel distribution
                    channel = random.choices(["SMS", "EMAIL", "PUSH", "WHATSAPP"], weights=[40, 30, 20, 10], k=1)[0]
                    
                    if b_status == "CANCELLED":
                        message_type = "BOOKING_CANCELLED"
                        body = f"Your booking {b_ref} has been cancelled successfully. Your refund is being processed."
                    else:
                        message_type = "BOOKING_CONFIRMED"
                        body = f"Thank you! Your booking {b_ref} is confirmed. Seat number: {row[5]}. Safe travels!"
                        
                    n_id = str(uuid.uuid4())
                    
                    # Notification sent 1 to 5 minutes after booked_at
                    try:
                        booked_dt = datetime.datetime.strptime(booked_at.split("+")[0], "%Y-%m-%d %H:%M:%S")
                        sent_dt = booked_dt + datetime.timedelta(minutes=random.randint(1, 5))
                        sent_at_str = sent_dt.strftime("%Y-%m-%d %H:%M:%S+00")
                    except ValueError:
                        sent_at_str = booked_at
                        
                    # columns: id, passenger_id, booking_id, channel, message_type, body, status, sent_at, error_msg, created_at
                    notifications.append([
                        n_id, p_id, b_id, channel, message_type, body, "DELIVERED", 
                        sent_at_str, "", booked_at
                    ])
                    count += 1
                    
                    if count % 100000 == 0:
                        print(f"Processed {count} bookings...")
                        
    print(f"Generated {len(notifications)} notifications.")
    print(f"Writing notifications to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(notifications)
        
    print("Success! System notifications file generated.")

if __name__ == "__main__":
    main()
