import os
import csv
import uuid
import random
import datetime

# Define name components for demographic realism in Sri Lanka
SINHALA_MALE_FIRST = [
    "Kavindu", "Pathum", "Dilshan", "Kusal", "Nimal", "Amal", "Kamal", "Saman", "Sunil", "Ranjan",
    "Ruwan", "Kasun", "Chathura", "Dinesh", "Asanka", "Mahesh", "Roshan", "Sanjaya", "Harsha", "Duminda",
    "Gayan", "Pradeep", "Janaka", "Bandara", "Wasantha", "Samantha", "Anura", "Upul", "Jayantha", "Rohan",
    "Lalith", "Sarath", "Nihal", "Gamini", "Jagath", "Priyantha", "Thusitha", "Nuwan", "Chinthaka", "Suranga",
    "Manjula", "Dhammika", "Indika", "Chaminda", "Suresh", "Ishara", "Thilina", "Lahiru", "Sandun", "Charith"
]

SINHALA_FEMALE_FIRST = [
    "Anusha", "Dilhani", "Kavindi", "Nisha", "Nilmini", "Priyanka", "Sanduni", "Thilini", "Ruwanthi",
    "Chathurika", "Sajeewani", "Hasini", "Menaka", "Upeksha", "Ganga", "Hiruni", "Malani", "Kumari",
    "Shashika", "Chandi", "Madhushani", "Achini", "Eranga", "Nirosha", "Kaushalya", "Samanthi", "Wasanthi",
    "Kanchana", "Hansini", "Sachini", "Ishara", "Niluka", "Gayani", "Inoka", "Imalka", "Bhagya", "Deepika",
    "Sunethra", "Damayanthi", "Swarna", "Malkanthi", "Manel", "Shanthi", "Pushpa", "Champa"
]

SINHALA_LAST_NAMES = [
    "Perera", "Fernando", "Silva", "Jayasundara", "Karunaratne", "Wickramasinghe", "Ranasinghe", "Rathnayake",
    "Senanayake", "Bandara", "Herath", "Gunawardena", "Jayasekara", "Amarasinghe", "Liyanage", "Rajapaksa",
    "Weerasinghe", "Alwis", "Cooray", "Dias", "Fonseka", "Goonetilleke", "Mendis", "Peiris", "Rodrigo",
    "Salgado", "Jayasinghe", "Premadasa", "Siriwardena", "Tennakoon", "Dissanayake", "Samarasinghe", "Abeykoon",
    "Wickramaratne", "Hettiarachchi", "Edirisinghe", "Gunasekara", "Ariyaratne", "Nanayakkara"
]

TAMIL_MALE_FIRST = [
    "Karthik", "Vijay", "Loganathan", "Sivaraman", "Arumugam", "Rasiah", "Subramaniam", "Karthikeyan", "Thavy",
    "Selvam", "Murugan", "Ravi", "Kumar", "Shankar", "Vasanth", "Prabhu", "Balasingham", "Thambiah", "Kanagasabai",
    "Ramanathan", "Yoganathan", "Chelvan", "Nadarajah", "Sivakumar", "Hariharan", "Chandran", "Thinesh", "Suresh",
    "Mahendran", "Ganeshan"
]

TAMIL_FEMALE_FIRST = [
    "Abirami", "Priya", "Divya", "Saraswathi", "Anusha", "Laxmi", "Sivagami", "Tharshini", "Kalaivani",
    "Thangam", "Meera", "Renuka", "Gayathri", "Kamala", "Shalini", "Janaki", "Tharini", "Suganya",
    "Pavithra", "Archana", "Geethanjali", "Nalini", "Vasanthi", "Malini", "Uma", "Preethi", "Reka",
    "Suba", "Radha"
]

TAMIL_LAST_NAMES = [
    "Ramanathan", "Karthikeyan", "Sivaraman", "Loganathan", "Arumugam", "Subramaniam", "Selvanathan", "Balasubramaniam",
    "Kanagaratnam", "Nadarajah", "Sivapalan", "Tharmarajah", "Vijayaratnam", "Shanmuganathan", "Kathiravelu",
    "Rajasingham", "Ganeshan", "Krishnakumar", "Thiyagarajah", "Velupillai"
]

MUSLIM_MALE_FIRST = [
    "Mohamed", "Abdul", "Rahman", "Shafi", "Rizwan", "Farook", "Ahamed", "Imran", "Sajid", "Rishan",
    "Nawaz", "Zakir", "Aslam", "Irfan", "Fazal", "Jazeel", "Faizer", "Salim", "Musthafa", "Naushad",
    "Feroz", "Raheem", "Zain", "Riffthi", "Yaseen", "Arshad", "Hassan", "Ali", "Usman", "Umar"
]

MUSLIM_FEMALE_FIRST = [
    "Fathima", "Aisha", "Zainab", "Mariam", "Aminah", "Khadijah", "Riza", "Shabnam", "Yasmin",
    "Farhana", "Nusrath", "Rizna", "Sumaiya", "Sajida", "Afrin", "Zahra", "Salma", "Nazreen",
    "Rifka", "Shazna", "Nafha", "Ishra", "Jasmine", "Sana", "Amra"
]

MUSLIM_LAST_NAMES = [
    "Rahman", "Shafi", "Rizwan", "Farook", "Ahamed", "Imran", "Nawaz", "Zakir", "Aslam", "Irfan",
    "Fazal", "Jazeel", "Musthafa", "Naushad", "Feroz", "Raheem", "Hassan", "Ali", "Usman", "Umar",
    "Suleiman", "Junaid", "Mansoor", "Ibrahim", "Nizar", "Rauf", "Ameen", "Latheef"
]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "ymail.com"]

def clean_name_for_email(name):
    # Removes initials and formats name for email (e.g. "a. b. c. pathum perera" -> "pathumperera")
    parts = name.lower().split()
    cleaned = [p for p in parts if len(p) > 2 and p.isalpha()]
    return "".join(cleaned) if cleaned else "passenger"

def main():
    target_count = 1000000
    output_csv = os.path.join(csv_dir, "srilankan_passengers_1m_no_header.csv")
    
    print(f"Generating {target_count} realistic Sri Lankan passenger records...")
    
    # Pre-generate phone sequence start (separate range from drivers to avoid any conflicts)
    # We will use 076 0000001 -> 076 1000000
    phone_base = 760000000
    
    # Store used NICs to ensure uniqueness
    used_nics = set()
    used_emails = set()
    
    count = 0
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        while count < target_count:
            # 1. Age & DOB (Passengers age from 5 to 90 years, born between 1936 and 2021)
            birth_year = random.randint(1936, 2021)
            birth_month = random.randint(1, 12)
            if birth_month in [4, 6, 9, 11]:
                birth_day = random.randint(1, 30)
            elif birth_month == 2:
                birth_day = random.randint(1, 29) if birth_year % 4 == 0 else random.randint(1, 28)
            else:
                birth_day = random.randint(1, 31)
                
            dob = datetime.date(birth_year, birth_month, birth_day)
            
            # 2. Gender (51% Female, 49% Male - demographically realistic)
            gender = "FEMALE" if random.random() < 0.51 else "MALE"
            
            # 3. NIC logic (linked to DOB & Gender, generated for ~75% of passengers, remaining are NULL)
            nic_number = ""
            if random.random() < 0.75:
                day_of_year = dob.timetuple().tm_yday
                if gender == "FEMALE":
                    day_of_year += 500
                    
                is_old_format = birth_year < 1990
                nic_found = False
                for attempt in range(100):
                    if is_old_format:
                        yy = str(birth_year)[2:]
                        ddd = f"{day_of_year:03d}"
                        sss = f"{random.randint(1, 999):03d}"
                        letter = "V" if random.random() < 0.95 else "X"
                        nic = f"{yy}{ddd}{sss}{letter}"
                    else:
                        yyyy = str(birth_year)
                        ddd = f"{day_of_year:03d}"
                        ssss = f"{random.randint(1, 9999):04d}"
                        nic = f"{yyyy}{ddd}0{ssss}"
                        
                    if nic not in used_nics:
                        used_nics.add(nic)
                        nic_number = nic
                        nic_found = True
                        break
                if not nic_found:
                    continue # Retry record generation on collision
            
            # 4. Generate Ethnic Names based on Gender
            rand_val = random.random()
            if rand_val < 0.75:
                # Sinhala
                last = random.choice(SINHALA_LAST_NAMES)
                if gender == "MALE":
                    first = random.choice(SINHALA_MALE_FIRST)
                    initial_parts = random.sample(["A.", "B.", "C.", "D.", "H.", "K.", "M.", "P.", "R.", "S.", "W."], random.randint(1, 3))
                    initials = " ".join(initial_parts)
                    full_name = f"{initials} {first} {last}"
                else:
                    first = random.choice(SINHALA_FEMALE_FIRST)
                    full_name = f"{first} {last}"
            elif rand_val < 0.90:
                # Tamil
                last = random.choice(TAMIL_LAST_NAMES)
                first = random.choice(TAMIL_MALE_FIRST) if gender == "MALE" else random.choice(TAMIL_FEMALE_FIRST)
                full_name = f"{first} {last}"
            else:
                # Muslim
                last = random.choice(MUSLIM_LAST_NAMES)
                first = random.choice(MUSLIM_MALE_FIRST) if gender == "MALE" else random.choice(MUSLIM_FEMALE_FIRST)
                if gender == "MALE" and random.random() < 0.5:
                    full_name = f"Mohamed {first} {last}"
                elif gender == "FEMALE" and random.random() < 0.5:
                    full_name = f"Fathima {first} {last}"
                else:
                    full_name = f"{first} {last}"
                    
            # 5. Unique Phone Number
            phone_val = phone_base + count + 1
            phone = f"0{phone_val}"
            
            # 6. Email (Generated for ~80% of passengers, remaining are NULL)
            email = ""
            if random.random() < 0.80:
                name_clean = clean_name_for_email(full_name)
                # Ensure email uniqueness
                email_found = False
                for attempt in range(100):
                    rand_suffix = random.randint(10, 99999)
                    domain = random.choice(DOMAINS)
                    temp_email = f"{name_clean}{rand_suffix}@{domain}"
                    if temp_email not in used_emails:
                        used_emails.add(temp_email)
                        email = temp_email
                        email_found = True
                        break
                if not email_found:
                    continue # Retry on collision
            
            # 7. Metadata & Timestamps
            passenger_id = str(uuid.uuid4())
            is_verified = "TRUE" if random.random() < 0.85 else "FALSE"
            is_active = "TRUE" if random.random() < 0.96 else "FALSE"
            
            # Timestamps
            created_days_ago = random.randint(1, 1000)
            created_at = (datetime.datetime.now() - datetime.timedelta(days=created_days_ago, hours=random.randint(0, 23))).isoformat()
            updated_at = created_at
            deleted_at = "" # Empty for NULL in copy
            
            # Write to CSV row (no header row!)
            # Columns: id, full_name, phone, email, nic_number, date_of_birth, gender, is_verified, is_active, created_at, updated_at, deleted_at
            writer.writerow([
                passenger_id, full_name, phone, email, nic_number, dob.isoformat(),
                gender, is_verified, is_active, created_at, updated_at, deleted_at
            ])
            
            count += 1
            if count % 200000 == 0:
                print(f"Generated {count} records...")
                
    print(f"Success! Generated {count} passengers and saved to {output_csv}")

if __name__ == "__main__":
    main()
