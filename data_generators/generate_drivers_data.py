import csv
import uuid
import random
import datetime
import os

# Define name components for ethnic diversity in Sri Lanka
SINHALA_FIRST_NAMES = [
    "Kavindu", "Pathum", "Dilshan", "Kusal", "Nimal", "Amal", "Kamal", "Saman", "Sunil", "Ranjan",
    "Ruwan", "Kasun", "Chathura", "Dinesh", "Asanka", "Mahesh", "Roshan", "Sanjaya", "Harsha", "Duminda",
    "Gayan", "Pradeep", "Janaka", "Bandara", "Wasantha", "Samantha", "Anura", "Upul", "Jayantha", "Rohan",
    "Lalith", "Sarath", "Nihal", "Gamini", "Jagath", "Priyantha", "Thusitha", "Nuwan", "Chinthaka", "Suranga",
    "Manjula", "Dhammika", "Indika", "Chaminda", "Suresh", "Ishara", "Thilina", "Lahiru", "Sandun", "Charith"
]

SINHALA_LAST_NAMES = [
    "Perera", "Fernando", "Silva", "Jayasundara", "Karunaratne", "Wickramasinghe", "Ranasinghe", "Rathnayake",
    "Senanayake", "Bandara", "Herath", "Gunawardena", "Jayasekara", "Amarasinghe", "Liyanage", "Rajapaksa",
    "Weerasinghe", "Alwis", "Cooray", "Dias", "Fonseka", "Goonetilleke", "Mendis", "Peiris", "Rodrigo",
    "Salgado", "Jayasinghe", "Premadasa", "Siriwardena", "Tennakoon", "Dissanayake", "Samarasinghe", "Abeykoon",
    "Wickramaratne", "Hettiarachchi", "Edirisinghe", "Gunasekara", "Ariyaratne", "Nanayakkara", "Wickramasinghe"
]

TAMIL_FIRST_NAMES = [
    "Karthik", "Vijay", "Loganathan", "Sivaraman", "Arumugam", "Rasiah", "Subramaniam", "Karthikeyan", "Thavy",
    "Selvam", "Murugan", "Ravi", "Kumar", "Shankar", "Vasanth", "Prabhu", "Balasingham", "Thambiah", "Kanagasabai",
    "Ramanathan", "Yoganathan", "Chelvan", "Nadarajah", "Sivakumar", "Hariharan", "Chandran", "Thinesh", "Suresh",
    "Mahendran", "Ganeshan", "Lingam", "Vigneswaran", "Pratheepan", "Rajesh", "Sanjeev", "Sivanandan", "Yogesh"
]

TAMIL_LAST_NAMES = [
    "Ramanathan", "Karthikeyan", "Sivaraman", "Loganathan", "Arumugam", "Subramaniam", "Selvanathan", "Balasubramaniam",
    "Kanagaratnam", "Nadarajah", "Sivapalan", "Tharmarajah", "Vijayaratnam", "Shanmuganathan", "Kathiravelu",
    "Rajasingham", "Ganeshan", "Krishnakumar", "Thiyagarajah", "Velupillai", "Kandasamy", "Ponnambalam", "Santhirasegaram"
]

MUSLIM_FIRST_NAMES = [
    "Mohamed", "Abdul", "Rahman", "Shafi", "Rizwan", "Farook", "Ahamed", "Imran", "Sajid", "Rishan",
    "Nawaz", "Zakir", "Aslam", "Irfan", "Fazal", "Jazeel", "Faizer", "Salim", "Musthafa", "Naushad",
    "Feroz", "Raheem", "Zain", "Riffthi", "Yaseen", "Arshad", "Hassan", "Ali", "Usman", "Umar"
]

MUSLIM_LAST_NAMES = [
    "Rahman", "Shafi", "Rizwan", "Farook", "Ahamed", "Imran", "Nawaz", "Zakir", "Aslam", "Irfan",
    "Fazal", "Jazeel", "Musthafa", "Naushad", "Feroz", "Raheem", "Hassan", "Ali", "Usman", "Umar",
    "Suleiman", "Junaid", "Mansoor", "Ibrahim", "Nizar", "Rauf", "Ameen", "Latheef", "Jiffry"
]

# Sri Lankan Towns/Roads for Addresses
ROADS = ["Galle Road", "Kandy Road", "Negombo Road", "Horana Road", "High Level Road", "Low Level Road", "Temple Road", "Station Road", "School Lane", "Main Street"]
SUBURBS = ["Colpetty", "Wellawatte", "Bambalapitiya", "Kiribathgoda", "Kadawatha", "Nugegoda", "Maharagama", "Kottawa", "Moratuwa", "Panadura", "Kalutara", "Negombo", "Gampaha", "Kandy", "Peradeniya", "Matara", "Galle", "Jaffna", "Batticaloa", "Trincomalee", "Kurunegala", "Anuradhapura", "Ratnapura", "Badulla"]

def generate_address():
    no = random.randint(1, 450)
    road = random.choice(ROADS)
    suburb = random.choice(SUBURBS)
    return f"No. {no}, {road}, {suburb}, Sri Lanka"

def main():
    target_count = 100000
    output_csv = os.path.join(csv_dir, "srilankan_drivers_700k_no_header.csv")
    
    print(f"Generating {target_count} realistic Sri Lankan driver records...")
    
    # Track unique columns to prevent violations
    used_nics = set()
    used_phones = set()
    used_licenses = set()

    # Pre-generate phone sequence start to ensure fast execution and uniqueness
    # 077 0000001 -> 077 0100000
    phone_base = 770000000
    
    # Pre-generate license number sequence start to ensure uniqueness
    # e.g., B3000001 onwards
    license_base = 3000000
    
    # Setup CSV writing
    fields = [
        "id", "nic_number", "full_name", "license_number", "license_expiry",
        "license_class", "phone", "emergency_contact", "address", "date_of_birth",
        "gender", "is_active", "notes", "created_at", "updated_at", "deleted_at"
    ]
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        count = 0
        while count < target_count:
            # 1. Generate birthdate first to derive age, DOB, and NIC
            # Driver age between 21 and 65 (born between 1961 and 2005)
            birth_year = random.randint(1961, 2005)
            birth_month = random.randint(1, 12)
            # Handle max days in month simply
            if birth_month in [4, 6, 9, 11]:
                birth_day = random.randint(1, 30)
            elif birth_month == 2:
                # Approximate leap year
                birth_day = random.randint(1, 29) if birth_year % 4 == 0 else random.randint(1, 28)
            else:
                birth_day = random.randint(1, 31)
                
            dob = datetime.date(birth_year, birth_month, birth_day)
            
            # 2. Gender - 99% Male (highly realistic for bus drivers in Sri Lanka), 1% Female
            gender = "MALE" if random.random() < 0.99 else "FEMALE"
            
            # 3. Calculate Day of Year for NIC
            day_of_year = dob.timetuple().tm_yday
            if gender == "FEMALE":
                day_of_year += 500
                
            # 4. Generate Unique NIC matching DOB and gender
            # Use old format (9 digits + V/X) for birth years < 1990, new format (12 digits) for >= 1990
            is_old_format = birth_year < 1990
            nic_found = False
            for attempt in range(100): # Serial number resolver
                if is_old_format:
                    # YY + DDD + SSS + V/X
                    yy = str(birth_year)[2:]
                    ddd = f"{day_of_year:03d}"
                    sss = f"{random.randint(1, 999):03d}"
                    letter = "V" if random.random() < 0.95 else "X"
                    nic = f"{yy}{ddd}{sss}{letter}"
                else:
                    # YYYY + DDD + 0 + SSSS (last digit check digit)
                    yyyy = str(birth_year)
                    ddd = f"{day_of_year:03d}"
                    ssss = f"{random.randint(1, 9999):04d}"
                    nic = f"{yyyy}{ddd}0{ssss}"
                    
                if nic not in used_nics:
                    used_nics.add(nic)
                    nic_found = True
                    break
            
            if not nic_found:
                continue # Retry record generation if NIC collision (very rare)
                
            nic_number = nic
            # 5. Generate Ethnic/Realistic Names
            # Sri Lankan distribution: ~75% Sinhala, ~15% Tamil, ~10% Muslim
            rand_val = random.random()
            if rand_val < 0.75:
                # Sinhala Name
                first = random.choice(SINHALA_FIRST_NAMES)
                last = random.choice(SINHALA_LAST_NAMES)
                initial_parts = random.sample(["A.", "B.", "C.", "D.", "H.", "K.", "M.", "P.", "R.", "S.", "W."], random.randint(1, 3))
                initials = " ".join(initial_parts)
                full_name = f"{initials} {first} {last}"
            elif rand_val < 0.90:
                # Tamil Name
                first = random.choice(TAMIL_FIRST_NAMES)
                last = random.choice(TAMIL_LAST_NAMES)
                full_name = f"{first} {last}"
            else:
                # Muslim Name
                first = random.choice(MUSLIM_FIRST_NAMES)
                last = random.choice(MUSLIM_LAST_NAMES)
                # Frequently prefix with Mohamed/Abdul
                if random.random() < 0.6:
                    full_name = f"Mohamed {first} {last}"
                else:
                    full_name = f"{first} {last}"
            
            # 6. Generate Unique Phone Number
            phone_val = phone_base + count + 1
            phone = f"0{phone_val}"
            
            # 7. Generate Unique License Number
            license_val = license_base + count + 1
            license_number = f"B{license_val}"
            
            # 8. License Expiry & Classes
            # Expiry date between next year and next 10 years
            expiry_days = random.randint(365, 3650)
            license_expiry = (datetime.date.today() + datetime.timedelta(days=expiry_days)).isoformat()
            
            # Bus driver licenses: D (Heavy Bus - 80%), DE (Heavy Bus + Trailer - 15%), D1 (Light Bus - 5%)
            license_class = random.choices(["D", "DE", "D1"], weights=[80, 15, 5], k=1)[0]
            
            # 9. Emergency Contact
            # Another random mobile number
            emergency_contact = f"07{random.randint(0, 8)}{random.randint(1000000, 9999999)}"
            
            # 10. Metadata
            driver_id = str(uuid.uuid4())
            address = generate_address()
            is_active = "TRUE" if random.random() < 0.92 else "FALSE" # 92% active roster
            notes = random.choice(["Experienced bus driver", "Clean driving record", "Assigned to luxury long-routes", "Active roster", "", None])
            
            # Timestamps
            created_days_ago = random.randint(1, 1000)
            created_at = (datetime.datetime.now() - datetime.timedelta(days=created_days_ago, hours=random.randint(0, 23))).isoformat()
            updated_at = created_at
            deleted_at = "" # NULL in Postgres CSV representation is empty string
            
            # Write to CSV
            writer.writerow([
                driver_id, nic_number, full_name, license_number, license_expiry,
                license_class, phone, emergency_contact, address, dob.isoformat(),
                gender, is_active, notes if notes else "", created_at, updated_at, deleted_at
            ])
            
            count += 1
            if count % 100000 == 0:
                print(f"Generated {count} records...")
                
    print(f"Success! Generated {count} drivers and saved to {output_csv}")

if __name__ == "__main__":
    main()
