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
    bookings_file = os.path.join(csv_dir, "srilankan_bookings_300k_no_header.csv")
    output_csv = os.path.join(csv_dir, "srilankan_payments_300k_no_header.csv")
    
    print("Reading bookings...")
    payments = []
    
    if os.path.exists(bookings_file):
        with open(bookings_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            count = 0
            for row in reader:
                if len(row) >= 10:
                    # id, passenger_id, trip_id, boarding_halt_id, alighting_halt_id, seat_number, fare_amount, booking_status, booking_ref, booked_at, cancelled_at, cancel_reason
                    b_id = row[0]
                    fare_amount = float(row[6])
                    b_status = row[7]
                    b_ref = row[8]
                    booked_at = row[9]
                    cancelled_at = row[10]
                    
                    # 1. Determine payment status and refund details
                    refund_amount = 0.00
                    refunded_at_str = ""
                    paid_at_str = ""
                    
                    if b_status == "CANCELLED":
                        payment_status = "REFUNDED"
                        # 90% refund (10% admin fee)
                        refund_amount = round(fare_amount * 0.90, 2)
                        paid_at_str = booked_at
                        refunded_at_str = cancelled_at
                    elif b_status in ["COMPLETED", "CONFIRMED", "NO_SHOW"]:
                        payment_status = "SUCCESS"
                        paid_at_str = booked_at
                    elif b_status == "PENDING":
                        # 80% pending, 20% failed payment attempts
                        payment_status = "PENDING" if random.random() < 0.80 else "FAILED"
                        if payment_status == "FAILED":
                            paid_at_str = "" # failed payments have no paid_at
                        else:
                            paid_at_str = ""
                    else:
                        payment_status = "PENDING"
                        
                    # 2. Determine payment method (cash vs cards vs online banking vs mobile wallets)
                    # For pending/failed, it is always digital
                    if payment_status in ["PENDING", "FAILED"]:
                        payment_method = random.choices(
                            ["CARD", "ONLINE_BANKING", "MOBILE_WALLET"], 
                            weights=[40, 30, 30], k=1
                        )[0]
                    else:
                        # Cash is very popular, but digital is also common
                        payment_method = random.choices(
                            ["CASH", "CARD", "ONLINE_BANKING", "MOBILE_WALLET", "KIOSK"],
                            weights=[50, 20, 15, 12, 3], k=1
                        )[0]
                        
                    # 3. Reference and Gateway IDs
                    # Transaction ref must be unique (BK reference appended)
                    transaction_ref = f"TXN-{b_ref}-{random.randint(10, 99)}"
                    
                    if payment_method == "CASH":
                        gateway_ref = "" # Cash doesn't go through an online gateway
                    else:
                        gateway_ref = f"PAY-GW-{uuid.uuid4().hex[:12].upper()}"
                        
                    payment_id = str(uuid.uuid4())
                    currency = "LKR"
                    
                    # Timestamps
                    created_at = booked_at
                    updated_at = refunded_at_str if payment_status == "REFUNDED" else booked_at
                    
                    # columns: id, booking_id, payment_method, amount, currency, transaction_ref, gateway_ref, payment_status, paid_at, refunded_at, refund_amount, created_at, updated_at
                    payments.append([
                        payment_id, b_id, payment_method, fare_amount, currency,
                        transaction_ref, gateway_ref, payment_status, paid_at_str,
                        refunded_at_str, refund_amount, created_at, updated_at
                    ])
                    count += 1
                    
                    if count % 100000 == 0:
                        print(f"Processed {count} records...")
                        
    print(f"Generated {len(payments)} payments.")
    print(f"Writing payments to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(payments)
        
    print("Success! Payments file generated.")

if __name__ == "__main__":
    main()
