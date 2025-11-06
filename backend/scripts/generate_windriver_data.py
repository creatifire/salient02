#!/usr/bin/env python3
"""
Generate diverse test data for hospital directory entries.
Creates configurable number of entries with specified distribution:
- 60% Physicians (MD/DO)
- 10% Advanced Practice (NPs, PAs, CNMs)
- 15% Therapists (PTs, OTs, SLPs, RTs)
- 15% Other Allied Health (trainers, techs, specialists)

All entries speak English, 50% speak 1+ additional languages.

Usage:
    python generate_windriver_data.py --count 500 --output backend/data/windriver/doctors_profiles.csv
    python generate_windriver_data.py --count 200 --output backend/data/newhospital/staff.csv
"""

import argparse
import csv
import os
import random
from datetime import datetime
from typing import List, Dict, Tuple

# Language options (all must include English)
LANGUAGES = ["English", "Spanish", "French", "Hindi", "Urdu", "Mandarin", "Cantonese", 
             "Arabic", "Swahili", "Japanese", "Korean", "Cambodian", "Telugu"]

# US Medical Schools (real)
US_MEDICAL_SCHOOLS = [
    "Harvard Medical School",
    "Johns Hopkins University School of Medicine",
    "Yale University School of Medicine",
    "Columbia University Vagelos College of Physicians and Surgeons",
    "Stanford University School of Medicine",
    "University of California San Francisco School of Medicine",
    "University of Pennsylvania Perelman School of Medicine",
    "Duke University School of Medicine",
    "University of Chicago Pritzker School of Medicine",
    "Cornell University Weill Cornell Medicine",
    "Northwestern University Feinberg School of Medicine",
    "University of Michigan Medical School",
    "Washington University in St. Louis School of Medicine",
    "Vanderbilt University School of Medicine",
    "New York University Grossman School of Medicine",
    "SUNY Downstate College of Medicine",
    "SUNY Stony Brook School of Medicine",
    "University of California Los Angeles David Geffen School of Medicine",
    "Boston University School of Medicine",
    "Tufts University School of Medicine",
    "Georgetown University School of Medicine",
    "George Washington University School of Medicine",
    "University of Pittsburgh School of Medicine",
    "Case Western Reserve University School of Medicine",
    "Emory University School of Medicine",
    "Baylor College of Medicine",
    "University of Texas Southwestern Medical Center",
    "University of Texas Medical Branch at Galveston",
    "University of Miami Miller School of Medicine",
    "University of Florida College of Medicine",
    "University of North Carolina School of Medicine",
    "Wake Forest School of Medicine",
    "Medical University of South Carolina",
    "University of Virginia School of Medicine",
    "Virginia Commonwealth University School of Medicine",
    "University of Maryland School of Medicine",
    "Jefferson Medical College",
    "Temple University School of Medicine",
    "Drexel University College of Medicine",
    "New York Medical College",
    "Albany Medical College",
    "University of Rochester School of Medicine",
    "SUNY Upstate Medical University",
    "University at Buffalo Jacobs School of Medicine",
    "Rutgers New Jersey Medical School",
    "Rutgers Robert Wood Johnson Medical School",
    "Albert Einstein College of Medicine",
    "Mount Sinai School of Medicine",
    "New York College of Osteopathic Medicine",
    "Rowan University School of Osteopathic Medicine",
    "Touro College of Osteopathic Medicine",
    "New York Institute of Technology College of Osteopathic Medicine",
]

# International Medical Schools (real)
INTERNATIONAL_MEDICAL_SCHOOLS = [
    "Universidad Central del Este",
    "Universidad Tecnologica De Santiago (Utesa)",
    "Universite d Etat d Haiti",
    "Universidad Nacional Autonoma de Mexico",
    "Instituto Tecnologico de Santo Domingo",
    "Universidad Autonoma de Santo Domingo",
    "Universidad Autonoma de Guadalajara",
    "Universidad de La Habana",
    "Universidad de Buenos Aires",
    "Universidade de São Paulo",
    "King Edward Medical University",
    "Government Medical College & Hospital Chandigarh",
    "All India Institute of Medical Sciences",
    "Jawaharlal Nehru Medical College",
    "Ayub Medical College",
    "Liaquat University of Medical & Health Sciences",
    "Dow University of Health Sciences",
    "Beijing Medical University",
    "Shanghai Medical University",
    "Fudan University Shanghai Medical College",
    "Peking Union Medical College",
    "University of Tokyo School of Medicine",
    "Kyoto University Faculty of Medicine",
    "Seoul National University College of Medicine",
    "Yonsei University College of Medicine",
    "Cairo University Faculty of Medicine",
    "Ain Shams University Faculty of Medicine",
    "Alexandria University Faculty of Medicine",
    "University of Khartoum Faculty of Medicine",
    "Makerere University School of Medicine",
    "University of Nairobi School of Medicine",
    "University of the West Indies",
    "University of the Philippines College of Medicine",
    "Chulalongkorn University Faculty of Medicine",
    "Mahidol University Faculty of Medicine",
    "University of Malaya Faculty of Medicine",
    "National University of Singapore Yong Loo Lin School of Medicine",
    "University of Sydney Medical School",
    "University of Melbourne Medical School",
    "Monash University Faculty of Medicine",
    "University of Toronto Faculty of Medicine",
    "McGill University Faculty of Medicine",
    "University of British Columbia Faculty of Medicine",
    "Université de Montréal Faculty of Medicine",
    "Université Laval Faculty of Medicine",
    "Russian State Medical University",
    "Samara State Medical University",
    "St. Petersburg State Medical Academy",
    "Moscow State University of Medicine and Dentistry",
    "Charité - Universitätsmedizin Berlin",
    "Heidelberg University Faculty of Medicine",
    "University of Paris Faculty of Medicine",
    "University of London School of Medicine",
    "Oxford University Medical School",
    "Cambridge University School of Clinical Medicine",
    "Trinity College Dublin School of Medicine",
    "University of Edinburgh Medical School",
    "University of Glasgow Medical School",
]

# US Nursing Schools
NURSING_SCHOOLS = [
    "Columbia University School of Nursing",
    "Johns Hopkins School of Nursing",
    "University of Pennsylvania School of Nursing",
    "Duke University School of Nursing",
    "Yale School of Nursing",
    "Vanderbilt University School of Nursing",
    "New York University Rory Meyers College of Nursing",
    "University of California San Francisco School of Nursing",
    "University of Michigan School of Nursing",
    "University of Washington School of Nursing",
    "Emory University Nell Hodgson Woodruff School of Nursing",
    "Georgetown University School of Nursing",
    "Boston College Connell School of Nursing",
    "University of North Carolina School of Nursing",
    "Ohio State University College of Nursing",
    "University of Maryland School of Nursing",
    "Rutgers University School of Nursing",
    "SUNY Downstate College of Nursing",
    "Lehman College (CUNY)",
    "Long Island University",
    "St. John's University",
    "Hunter College (CUNY)",
    "City College of New York (CUNY)",
    "New York University",
    "SUNY Stony Brook University",
    "University of Texas Health Science Center",
    "Texas A&M University College of Nursing",
]

# Physical Therapy Schools
PT_SCHOOLS = [
    "University of Southern California",
    "University of Delaware",
    "University of Pittsburgh",
    "Northwestern University",
    "Washington University in St. Louis",
    "Emory University",
    "University of Miami",
    "University of North Carolina",
    "University of Maryland",
    "Boston University",
    "New York University",
    "Columbia University",
    "Temple University",
    "Drexel University",
    "Thomas Jefferson University",
    "Rutgers University",
    "SUNY Stony Brook",
    "University of California San Francisco",
]

# Departments and their specialties
DEPARTMENTS_SPECIALTIES = {
    "Emergency Medicine": [
        "Emergency Medicine",
        "Trauma Surgery",
        "Critical Care Medicine",
        "Medical Toxicology",
    ],
    "Surgery": [
        "General Surgery",
        "Orthopedic Surgery",
        "Plastic Surgery",
        "Vascular Surgery",
        "Cardiothoracic Surgery",
        "Neurosurgery",
        "Urologic Surgery",
        "Ophthalmology",
        "Otolaryngology",
        "Colon and Rectal Surgery",
        "Surgical Oncology",
    ],
    "Medicine": [
        "General Internal Medicine",
        "Cardiology",
        "Interventional Cardiology",
        "Clinical Cardiac Electrophysiology",
        "Gastroenterology and Hepatology",
        "Nephrology",
        "Pulmonary and Critical Care",
        "Endocrinology",
        "Rheumatology",
        "Infectious Diseases",
        "Hematology/Oncology",
        "Medical Oncology",
        "Neurology",
        "Vascular Neurology",
        "Clinical Neurophysiology",
        "Psychiatry",
        "Addiction Medicine",
        "Geriatric Medicine",
        "Hospital Medicine",
    ],
    "Pediatrics": [
        "General Pediatrics",
        "Pediatric Cardiology",
        "Pediatric Pulmonology",
        "Pediatric Endocrinology",
        "Pediatric Hematology-Oncology",
        "Pediatric Neurology",
        "Neonatology",
        "Pediatric Emergency Medicine",
        "Adolescent Medicine",
        "Pediatric Critical Care",
    ],
    "OB/GYN": [
        "Obstetrics and Gynecology",
        "Maternal/Fetal Medicine",
        "Reproductive Endocrinology",
        "Gynecologic Oncology",
        "Uro-Gynecology",
        "Minimally Invasive Surgery",
    ],
    "Rehabilitation": [
        "Physical Medicine & Rehabilitation",
        "Sports Medicine",
        "Pain Medicine",
    ],
    "Radiology": [
        "Diagnostic Radiology",
        "Interventional Radiology",
        "Nuclear Medicine",
        "Radiation Oncology",
    ],
    "Pathology": [
        "Anatomic Pathology",
        "Clinical Pathology",
        "Forensic Pathology",
    ],
    "Anesthesiology": [
        "Anesthesiology",
        "Pain Medicine",
        "Critical Care Medicine",
    ],
    "Dental Medicine": [
        "General Dentistry",
        "Oral and Maxillofacial Surgery",
        "Dental Anesthesia",
        "Periodontics",
        "Endodontics",
    ],
    "Podiatry": [
        "Podiatric Surgery",
        "Podiatric Medicine",
    ],
}

# Advanced Practice specialties
ADVANCED_PRACTICE_SPECIALTIES = {
    "Nurse Practitioner": [
        ("Family Medicine", "Family"),
        ("Cardiology", "Adult Health"),
        ("Neurology", "Adult Health"),
        ("Pediatrics", "Pediatric"),
        ("Psychiatry", "Psychiatric-Mental Health"),
        ("Geriatrics", "Adult-Gerontology"),
        ("Emergency Medicine", "Acute Care"),
        ("Oncology", "Adult Health"),
        ("Women's Health", "Women's Health"),
    ],
    "Physician Assistant": [
        ("Emergency Medicine", "Emergency Medicine"),
        ("Surgery", "General Surgery"),
        ("Orthopedic Surgery", "Orthopedic Surgery"),
        ("Cardiology", "Cardiology"),
        ("Internal Medicine", "Internal Medicine"),
        ("Pediatrics", "Pediatrics"),
        ("Dermatology", "Dermatology"),
    ],
    "Certified Nurse Midwife": [
        ("OB/GYN", "Obstetrics and Gynecology"),
    ],
}

# Therapist specialties
THERAPIST_SPECIALTIES = {
    "Physical Therapist": [
        "Orthopedic Physical Therapy",
        "Neurologic Physical Therapy",
        "Cardiopulmonary Physical Therapy",
        "Geriatric Physical Therapy",
        "Pediatric Physical Therapy",
        "Sports Physical Therapy",
        "Women's Health Physical Therapy",
    ],
    "Occupational Therapist": [
        "Hand Therapy",
        "Pediatric Occupational Therapy",
        "Geriatric Occupational Therapy",
        "Neurologic Occupational Therapy",
        "Mental Health Occupational Therapy",
    ],
    "Speech-Language Pathologist": [
        "Pediatric Speech Therapy",
        "Adult Speech Therapy",
        "Swallowing Disorders",
        "Voice Disorders",
        "Cognitive Communication Disorders",
    ],
    "Respiratory Therapist": [
        "Critical Care Respiratory Therapy",
        "Pediatric Respiratory Therapy",
        "Neonatal Respiratory Therapy",
        "Pulmonary Rehabilitation",
    ],
}

# Other Allied Health
OTHER_ALLIED_HEALTH = {
    "Medical Trainer": [
        ("Training", "Medical Education"),
        ("Training", "Clinical Skills Training"),
        ("Training", "Simulation Training"),
    ],
    "Clinical Nurse Specialist": [
        ("Medicine", "Critical Care"),
        ("Surgery", "Perioperative Care"),
        ("Pediatrics", "Pediatric Critical Care"),
        ("Medicine", "Oncology"),
    ],
    "Perioperative Nurse": [
        ("Surgery", "Cardiothoracic Surgery"),
        ("Surgery", "Orthopedic Surgery"),
        ("Surgery", "General Surgery"),
        ("Surgery", "Neurosurgery"),
    ],
    "Surgical Technologist": [
        ("Surgery", "General Surgery"),
        ("Surgery", "Orthopedic Surgery"),
        ("Surgery", "Cardiothoracic Surgery"),
    ],
    "Radiologic Technologist": [
        ("Radiology", "Computed Tomography"),
        ("Radiology", "Magnetic Resonance Imaging"),
        ("Radiology", "Interventional Radiology"),
    ],
    "Medical Technologist": [
        ("Laboratory", "Clinical Chemistry"),
        ("Laboratory", "Hematology"),
        ("Laboratory", "Microbiology"),
    ],
    "Registered Dietitian": [
        ("Nutrition Services", "Clinical Nutrition"),
        ("Nutrition Services", "Pediatric Nutrition"),
        ("Nutrition Services", "Renal Nutrition"),
    ],
    "Pharmacist": [
        ("Pharmacy", "Clinical Pharmacy"),
        ("Pharmacy", "Oncology Pharmacy"),
        ("Pharmacy", "Critical Care Pharmacy"),
    ],
}

# Residency programs (common hospitals)
RESIDENCY_HOSPITALS = [
    "New York Presbyterian Hospital",
    "Mount Sinai Hospital",
    "NYU Langone Medical Center",
    "Montefiore Medical Center",
    "Maimonides Medical Center",
    "Brooklyn Hospital Center",
    "Elmhurst Hospital Center",
    "Bellevue Hospital Center",
    "Harlem Hospital Center",
    "Kings County Hospital Center",
    "Bronx Lebanon Hospital Center",
    "Jamaica Hospital Medical Center",
    "Staten Island University Hospital",
    "Winthrop University Hospital",
    "Long Island Jewish Medical Center",
    "North Shore University Hospital",
    "Lenox Hill Hospital",
    "Weill Cornell Medical Center",
    "Columbia University Irving Medical Center",
    "Memorial Sloan-Kettering Cancer Center",
    "Hospital for Special Surgery",
    "Massachusetts General Hospital",
    "Brigham and Women's Hospital",
    "Johns Hopkins Hospital",
    "Cleveland Clinic",
    "Mayo Clinic",
    "University of California San Francisco Medical Center",
    "University of Michigan Medical Center",
    "Duke University Medical Center",
    "Vanderbilt University Medical Center",
    "Emory University Hospital",
    "University of Texas Medical Center",
    "University of Chicago Medical Center",
    "Northwestern Memorial Hospital",
    "Rush University Medical Center",
    "University of Pennsylvania Hospital",
    "Thomas Jefferson University Hospital",
    "Temple University Hospital",
    "Drexel University Hospital",
    "University of Maryland Medical Center",
    "Georgetown University Hospital",
    "George Washington University Hospital",
    "Virginia Commonwealth University Medical Center",
    "University of Virginia Medical Center",
    "University of North Carolina Medical Center",
    "Wake Forest Baptist Medical Center",
    "Medical University of South Carolina",
]

# Fellowship programs (common institutions)
FELLOWSHIP_INSTITUTIONS = [
    "Cleveland Clinic",
    "Mayo Clinic",
    "Johns Hopkins Hospital",
    "Massachusetts General Hospital",
    "Brigham and Women's Hospital",
    "Memorial Sloan-Kettering Cancer Center",
    "MD Anderson Cancer Center",
    "Hospital for Special Surgery",
    "University of California San Francisco Medical Center",
    "Stanford University Medical Center",
    "Duke University Medical Center",
    "University of Pennsylvania Hospital",
    "New York Presbyterian Hospital",
    "Mount Sinai Hospital",
    "NYU Langone Medical Center",
    "Columbia University Irving Medical Center",
    "Weill Cornell Medical Center",
    "University of Chicago Medical Center",
    "Northwestern Memorial Hospital",
    "University of Michigan Medical Center",
    "Vanderbilt University Medical Center",
    "Emory University Hospital",
    "University of Texas Medical Center",
    "Cedars-Sinai Medical Center",
    "UCLA Medical Center",
    "University of Washington Medical Center",
    "University of Pittsburgh Medical Center",
    "University of Maryland Medical Center",
    "Georgetown University Hospital",
    "University of Virginia Medical Center",
    "University of North Carolina Medical Center",
    "Wake Forest Baptist Medical Center",
    "Medical University of South Carolina",
]

def generate_id(start_id: int) -> str:
    """Generate sequential ID starting from start_id."""
    return str(start_id)

def assign_languages(require_additional: bool) -> str:
    """Assign languages - all get English, some get additional."""
    lang_list = ["English"]
    if require_additional:
        # Assign 1-3 additional languages
        num_additional = random.randint(1, 3)
        additional = random.sample([l for l in LANGUAGES if l != "English"], num_additional)
        lang_list.extend(additional)
    return ",".join(lang_list)

def generate_name(professional_type: str, gender: str) -> str:
    """Generate realistic diverse names."""
    # First names (diverse)
    male_first = [
        "James", "Michael", "David", "Robert", "William", "Richard", "Joseph", "Thomas",
        "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
        "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Edward",
        "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas",
        "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon", "Frank",
        "Benjamin", "Gregory", "Raymond", "Alexander", "Patrick", "Jack", "Dennis",
        "Jerry", "Tyler", "Aaron", "Jose", "Henry", "Adam", "Douglas", "Nathan",
        "Zachary", "Kyle", "Noah", "Ethan", "Mason", "Lucas", "Aiden", "Logan",
        "Omar", "Ahmed", "Mohammed", "Hassan", "Ali", "Rahul", "Vikram", "Arjun",
        "Priyank", "Sachin", "Raj", "Anil", "Kumar", "Wei", "Chen", "Ming", "Li",
        "Hiroshi", "Kenji", "Takeshi", "Yuki", "Sung", "Min", "Jin", "Seung",
        "Diego", "Carlos", "Miguel", "Javier", "Fernando", "Ricardo", "Luis",
        "Antonio", "Juan", "Pedro", "Rafael", "Alejandro", "Gabriel", "Sergio",
        "Marc", "Jean", "Pierre", "François", "Philippe", "Nicolas", "Laurent",
        "Ahmed", "Khalid", "Youssef", "Amir", "Tariq", "Nasser", "Samir",
    ]
    
    female_first = [
        "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan",
        "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra",
        "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Dorothy", "Carol",
        "Amanda", "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura",
        "Cynthia", "Kathleen", "Amy", "Angela", "Shirley", "Anna", "Brenda",
        "Pamela", "Emma", "Nicole", "Helen", "Samantha", "Katherine", "Christine",
        "Debra", "Rachel", "Carolyn", "Janet", "Virginia", "Maria", "Heather",
        "Diane", "Julie", "Joyce", "Victoria", "Kelly", "Christina", "Joan",
        "Evelyn", "Judith", "Megan", "Andrea", "Cheryl", "Hannah", "Jacqueline",
        "Martha", "Gloria", "Teresa", "Sara", "Janice", "Marie", "Julia", "Grace",
        "Judy", "Theresa", "Madison", "Beverly", "Denise", "Marilyn", "Amber",
        "Danielle", "Brittany", "Diana", "Abigail", "Jane", "Lori", "Tammy",
        "Aisha", "Fatima", "Zainab", "Amina", "Leila", "Noor", "Sara", "Mariam",
        "Priya", "Anjali", "Kavita", "Meera", "Sneha", "Riya", "Diya", "Ananya",
        "Mei", "Li", "Xia", "Ying", "Hui", "Fang", "Jing", "Yan", "Yuki", "Sakura",
        "Hana", "Akiko", "Emiko", "Keiko", "Soo", "Min", "Jin", "Hee", "Young",
        "Maria", "Carmen", "Elena", "Isabel", "Sofia", "Ana", "Lucia", "Rosa",
        "Patricia", "Laura", "Cristina", "Monica", "Andrea", "Claudia", "Veronica",
        "Marie", "Sophie", "Isabelle", "Claire", "Camille", "Julie", "Elise",
        "Layla", "Amina", "Zara", "Noor", "Sana", "Maya", "Hannah", "Sarah",
    ]
    
    # Last names (diverse)
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
        "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris",
        "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen",
        "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
        "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter",
        "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz",
        "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Rogers", "Reed", "Cook",
        "Morgan", "Bell", "Murphy", "Bailey", "Rivera", "Cooper", "Richardson", "Cox",
        "Howard", "Ward", "Torres", "Peterson", "Gray", "Ramirez", "James", "Watson",
        "Brooks", "Kelly", "Sanders", "Price", "Bennett", "Wood", "Barnes", "Ross",
        "Henderson", "Coleman", "Jenkins", "Perry", "Powell", "Long", "Patterson", "Hughes",
        "Flores", "Washington", "Butler", "Simmons", "Foster", "Gonzales", "Bryant",
        "Alexander", "Russell", "Griffin", "Diaz", "Hayes", "Patel", "Singh", "Kumar",
        "Sharma", "Gupta", "Patel", "Shah", "Mehta", "Reddy", "Iyer", "Nair",
        "Chen", "Wang", "Li", "Zhang", "Liu", "Wu", "Yang", "Huang", "Zhou", "Xu",
        "Tanaka", "Yamamoto", "Sato", "Suzuki", "Watanabe", "Kobayashi", "Kato", "Ito",
        "Kim", "Park", "Lee", "Choi", "Jung", "Kang", "Yoon", "Jang", "Shin",
        "Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Hernandez", "Perez",
        "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Cruz",
        "Reyes", "Morales", "Ortiz", "Gutierrez", "Chavez", "Ramos", "Mendoza",
        "Martin", "Bernard", "Dubois", "Moreau", "Simon", "Laurent", "Lefebvre",
        "Hassan", "Ali", "Ahmed", "Khalid", "Ibrahim", "Mohammed", "Omar", "Youssef",
    ]
    
    first_names = male_first if gender == "male" else female_first
    first = random.choice(first_names)
    last = random.choice(last_names)
    
    # Add credentials based on type
    if professional_type in ["Physician", "MD", "DO"]:
        credential = random.choice(["MD", "DO"])
        return f"{first} {last}, {credential}"
    elif professional_type == "Nurse Practitioner":
        return f"{first} {last}, NP"
    elif professional_type == "Physician Assistant":
        return f"{first} {last}, PA"
    elif professional_type == "Certified Nurse Midwife":
        return f"{first} {last}, CNM"
    elif professional_type == "Physical Therapist":
        return f"{first} {last}, PT"
    elif professional_type == "Occupational Therapist":
        return f"{first} {last}, OT"
    elif professional_type == "Speech-Language Pathologist":
        return f"{first} {last}, SLP"
    elif professional_type == "Respiratory Therapist":
        return f"{first} {last}, RT"
    elif professional_type == "Clinical Nurse Specialist":
        return f"{first} {last}, CNS"
    elif professional_type == "Perioperative Nurse":
        return f"{first} {last}, RN"
    elif professional_type == "Surgical Technologist":
        return f"{first} {last}, CST"
    elif professional_type == "Radiologic Technologist":
        return f"{first} {last}, RT(R)"
    elif professional_type == "Medical Technologist":
        return f"{first} {last}, MT(ASCP)"
    elif professional_type == "Registered Dietitian":
        return f"{first} {last}, RD"
    elif professional_type == "Pharmacist":
        return f"{first} {last}, PharmD"
    elif professional_type == "Medical Trainer":
        return f"{first} {last}, MEd"
    else:
        return f"{first} {last}"

def generate_physician_education() -> str:
    """Generate medical school education."""
    if random.random() < 0.7:  # 70% US schools
        return random.choice(US_MEDICAL_SCHOOLS)
    else:  # 30% international
        return random.choice(INTERNATIONAL_MEDICAL_SCHOOLS)

def generate_residency(department: str, specialty: str) -> str:
    """Generate residency program."""
    hospital = random.choice(RESIDENCY_HOSPITALS)
    year_start = random.randint(1990, 2020)
    year_end = year_start + random.randint(3, 5)
    
    # Residency length depends on specialty
    if department == "Surgery":
        year_end = year_start + random.randint(5, 7)
    elif department == "Emergency Medicine":
        year_end = year_start + 4
    elif department == "Pediatrics" or department == "Medicine":
        year_end = year_start + 3
    
    return f"{hospital}, {specialty} {year_start}-{year_end}"

def generate_fellowship(department: str, specialty: str) -> str:
    """Generate fellowship program."""
    institution = random.choice(FELLOWSHIP_INSTITUTIONS)
    year_start = random.randint(1995, 2022)
    year_end = year_start + random.randint(1, 3)
    
    # Create subspecialty
    subspecialties = {
        "Cardiology": ["Interventional Cardiology", "Clinical Cardiac Electrophysiology", "Heart Failure"],
        "Surgery": ["Trauma Surgery", "Surgical Critical Care", "Minimally Invasive Surgery"],
        "Neurology": ["Vascular Neurology", "Clinical Neurophysiology", "Movement Disorders"],
        "Pediatrics": ["Pediatric Cardiology", "Pediatric Critical Care", "Neonatology"],
        "Medicine": ["Gastroenterology", "Nephrology", "Pulmonary and Critical Care"],
    }
    
    if department in subspecialties:
        subspecialty = random.choice(subspecialties[department])
    else:
        subspecialty = specialty
    
    return f"{institution}, {subspecialty} {year_start}-{year_end}"

def generate_board_certification(specialty: str, year: int) -> str:
    """Generate board certification."""
    certs = [f"{specialty}, {year}"]
    
    # Some have multiple certifications
    if random.random() < 0.3:
        base_specialty = specialty.split()[0] if " " in specialty else specialty
        if base_specialty == "Cardiology":
            certs.append(f"Internal Medicine, {year - 3}")
        elif base_specialty == "Surgery":
            certs.append(f"Surgery (General Surgery), {year - 5}")
        elif base_specialty == "Pediatric":
            certs.append(f"Pediatrics, {year - 3}")
    
    return "\n".join(certs)

def generate_physician_entry(id_num: int, require_additional_lang: bool) -> Dict:
    """Generate a physician entry."""
    gender = random.choice(["male", "female"])
    department = random.choice(list(DEPARTMENTS_SPECIALTIES.keys()))
    specialty = random.choice(DEPARTMENTS_SPECIALTIES[department])
    
    # Generate credentials
    credential = random.choice(["MD", "DO"])
    name = generate_name(credential, gender)
    
    # Education
    education = generate_physician_education()
    
    # Residency
    residency_year_start = random.randint(1990, 2020)
    residency = generate_residency(department, specialty)
    
    # Fellowship (50% have fellowships)
    fellowship = ""
    if random.random() < 0.5:
        fellowship = generate_fellowship(department, specialty)
    
    # Board certification
    cert_year = random.randint(2000, 2024)
    board_cert = generate_board_certification(specialty, cert_year)
    
    # Internship (some have it)
    internship = ""
    if random.random() < 0.3:
        hospital = random.choice(RESIDENCY_HOSPITALS)
        internship = f"{hospital}, {specialty} {residency_year_start-1}-{residency_year_start}"
    
    # Languages
    languages = assign_languages(require_additional_lang)
    
    return {
        "id": generate_id(id_num),
        "doctor_name": name,
        "department": department,
        "speciality": specialty,
        "facility": "",
        "phone": "",
        "location": "",
        "board_certifications": board_cert,
        "education": education,
        "residencies": residency,
        "fellowships": fellowship,
        "gender": gender,
        "language": languages,
        "insurance": "",
        "internship": internship,
        "badge": "",
        "profile_pic": "",
        "is_active": "1",
        "created_on": "0000-00-00 00:00:00",
    }

def generate_advanced_practice_entry(id_num: int, require_additional_lang: bool) -> Dict:
    """Generate an advanced practice provider entry."""
    gender = random.choice(["male", "female"])
    provider_type = random.choice(list(ADVANCED_PRACTICE_SPECIALTIES.keys()))
    
    if provider_type == "Nurse Practitioner":
        specialty_tuple = random.choice(ADVANCED_PRACTICE_SPECIALTIES[provider_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Nurse Practitioner", gender)
        education = random.choice(NURSING_SCHOOLS)
        cert = f"Nurse Practitioner, {specialty}, {random.randint(2015, 2024)}"
        residency = ""
        fellowship = ""
    elif provider_type == "Physician Assistant":
        specialty_tuple = random.choice(ADVANCED_PRACTICE_SPECIALTIES[provider_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Physician Assistant", gender)
        education = random.choice(["Harlem Hospital Physician Assistant Program",
                                 "St. John's University Physician Assistant Program",
                                 "Touro College", "Long Island University",
                                 "SUNY Stony Brook University"])
        cert = f"Physician Assistant, {random.randint(2015, 2024)}"
        residency = ""
        fellowship = ""
    else:  # CNM
        specialty_tuple = random.choice(ADVANCED_PRACTICE_SPECIALTIES[provider_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Certified Nurse Midwife", gender)
        education = random.choice(NURSING_SCHOOLS)
        cert = f"Midwife, Certified, {random.randint(2015, 2024)}"
        residency = ""
        fellowship = ""
    
    languages = assign_languages(require_additional_lang)
    
    return {
        "id": generate_id(id_num),
        "doctor_name": name,
        "department": department,
        "speciality": specialty,
        "facility": "",
        "phone": "",
        "location": "",
        "board_certifications": cert,
        "education": education,
        "residencies": residency,
        "fellowships": fellowship,
        "gender": gender,
        "language": languages,
        "insurance": "",
        "internship": "",
        "badge": "",
        "profile_pic": "",
        "is_active": "1",
        "created_on": "0000-00-00 00:00:00",
    }

def generate_therapist_entry(id_num: int, require_additional_lang: bool) -> Dict:
    """Generate a therapist entry."""
    gender = random.choice(["male", "female"])
    therapist_type = random.choice(list(THERAPIST_SPECIALTIES.keys()))
    specialty = random.choice(THERAPIST_SPECIALTIES[therapist_type])
    
    name = generate_name(therapist_type, gender)
    
    if therapist_type == "Physical Therapist":
        education = random.choice(PT_SCHOOLS)
        department = "Rehabilitation"
        cert = f"Physical Therapy, {random.randint(2015, 2024)}"
    elif therapist_type == "Occupational Therapist":
        education = random.choice(PT_SCHOOLS)  # Similar schools
        department = "Rehabilitation"
        cert = f"Occupational Therapy, {random.randint(2015, 2024)}"
    elif therapist_type == "Speech-Language Pathologist":
        education = random.choice(PT_SCHOOLS)  # Similar schools
        department = "Rehabilitation"
        cert = f"Speech-Language Pathology, {random.randint(2015, 2024)}"
    else:  # Respiratory Therapist
        education = random.choice(["University of California San Francisco",
                                 "University of North Carolina",
                                 "SUNY Stony Brook"])
        department = "Medicine"
        cert = f"Respiratory Therapy, {random.randint(2015, 2024)}"
    
    languages = assign_languages(require_additional_lang)
    
    return {
        "id": generate_id(id_num),
        "doctor_name": name,
        "department": department,
        "speciality": specialty,
        "facility": "",
        "phone": "",
        "location": "",
        "board_certifications": cert,
        "education": education,
        "residencies": "",
        "fellowships": "",
        "gender": gender,
        "language": languages,
        "insurance": "",
        "internship": "",
        "badge": "",
        "profile_pic": "",
        "is_active": "1",
        "created_on": "0000-00-00 00:00:00",
    }

def generate_other_allied_entry(id_num: int, require_additional_lang: bool) -> Dict:
    """Generate an other allied health entry."""
    gender = random.choice(["male", "female"])
    role_type = random.choice(list(OTHER_ALLIED_HEALTH.keys()))
    
    if role_type == "Medical Trainer":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Medical Trainer", gender)
        education = random.choice(["Columbia University", "New York University",
                                 "Johns Hopkins University", "University of Pennsylvania"])
        cert = f"Medical Education, {random.randint(2015, 2024)}"
    elif role_type == "Clinical Nurse Specialist":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Clinical Nurse Specialist", gender)
        education = random.choice(NURSING_SCHOOLS)
        cert = f"Clinical Nurse Specialist, {specialty}, {random.randint(2015, 2024)}"
    elif role_type == "Perioperative Nurse":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Perioperative Nurse", gender)
        education = random.choice(NURSING_SCHOOLS)
        cert = f"Certified Nurse Operating Room (CNOR), {random.randint(2015, 2024)}"
    elif role_type == "Surgical Technologist":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Surgical Technologist", gender)
        education = random.choice(["Touro College", "SUNY Stony Brook",
                                 "Long Island University"])
        cert = f"Certified Surgical Technologist (CST), {random.randint(2015, 2024)}"
    elif role_type == "Radiologic Technologist":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Radiologic Technologist", gender)
        education = random.choice(["SUNY Stony Brook", "New York University",
                                 "University of California San Francisco"])
        cert = f"Radiologic Technology, {specialty}, {random.randint(2015, 2024)}"
    elif role_type == "Medical Technologist":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Medical Technologist", gender)
        education = random.choice(["SUNY Stony Brook", "Rutgers University",
                                 "University of Maryland"])
        cert = f"Medical Technology, {specialty}, {random.randint(2015, 2024)}"
    elif role_type == "Registered Dietitian":
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Registered Dietitian", gender)
        education = random.choice(["New York University", "Columbia University",
                                 "University of California Berkeley"])
        cert = f"Registered Dietitian (RD), {random.randint(2015, 2024)}"
    else:  # Pharmacist
        specialty_tuple = random.choice(OTHER_ALLIED_HEALTH[role_type])
        department = specialty_tuple[0]
        specialty = specialty_tuple[1]
        name = generate_name("Pharmacist", gender)
        education = random.choice(["University of California San Francisco",
                                  "University of North Carolina",
                                  "University of Michigan",
                                  "Rutgers University"])
        cert = f"Pharmacy, {specialty}, {random.randint(2015, 2024)}"
    
    languages = assign_languages(require_additional_lang)
    
    return {
        "id": generate_id(id_num),
        "doctor_name": name,
        "department": department,
        "speciality": specialty,
        "facility": "",
        "phone": "",
        "location": "",
        "board_certifications": cert,
        "education": education,
        "residencies": "",
        "fellowships": "",
        "gender": gender,
        "language": languages,
        "insurance": "",
        "internship": "",
        "badge": "",
        "profile_pic": "",
        "is_active": "1",
        "created_on": "0000-00-00 00:00:00",
    }

def main():
    """Generate healthcare professional entries based on command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate diverse test data for hospital directory entries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 500 entries for Windriver Hospital
  python generate_windriver_data.py --count 500 --output backend/data/windriver/windriver_doctors_profiles.csv
  
  # Generate 200 entries for a new hospital
  python generate_windriver_data.py --count 200 --output backend/data/newhospital/staff.csv
  
  # Generate 1000 entries with custom starting ID
  python generate_windriver_data.py --count 1000 --output data/hospital.csv --start-id 9400000
        """
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Total number of entries to generate (default: 500)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output CSV file path (e.g., backend/data/windriver/doctors_profiles.csv)"
    )
    
    parser.add_argument(
        "--start-id",
        type=int,
        default=9300000,
        help="Starting ID number for entries (default: 9300000)"
    )
    
    args = parser.parse_args()
    
    # Validate count
    if args.count < 1:
        parser.error("--count must be at least 1")
    
    # Calculate distribution based on percentages
    num_physicians = int(args.count * 0.60)
    num_advanced_practice = int(args.count * 0.10)
    num_therapists = int(args.count * 0.15)
    num_other = args.count - num_physicians - num_advanced_practice - num_therapists  # Remainder
    
    # Ensure total matches (handle rounding)
    total_generated = num_physicians + num_advanced_practice + num_therapists + num_other
    if total_generated != args.count:
        # Adjust physicians to match exact count
        num_physicians += (args.count - total_generated)
    
    print(f"Generating {args.count} entries with distribution:")
    print(f"  - Physicians: {num_physicians} (60%)")
    print(f"  - Advanced Practice: {num_advanced_practice} (10%)")
    print(f"  - Therapists: {num_therapists} (15%)")
    print(f"  - Other Allied Health: {num_other} (15%)")
    print()
    
    entries = []
    id_counter = args.start_id
    
    # Track which entries need additional languages (50% of total)
    num_additional_lang = args.count // 2
    require_additional = [True] * num_additional_lang + [False] * (args.count - num_additional_lang)
    random.shuffle(require_additional)
    additional_lang_index = 0
    
    # Generate Physicians (60%)
    print(f"Generating {num_physicians} physicians...")
    for i in range(num_physicians):
        entries.append(generate_physician_entry(
            id_counter,
            require_additional[additional_lang_index]
        ))
        id_counter += 1
        additional_lang_index += 1
    
    # Generate Advanced Practice (10%)
    print(f"Generating {num_advanced_practice} advanced practice providers...")
    for i in range(num_advanced_practice):
        entries.append(generate_advanced_practice_entry(
            id_counter,
            require_additional[additional_lang_index]
        ))
        id_counter += 1
        additional_lang_index += 1
    
    # Generate Therapists (15%)
    print(f"Generating {num_therapists} therapists...")
    for i in range(num_therapists):
        entries.append(generate_therapist_entry(
            id_counter,
            require_additional[additional_lang_index]
        ))
        id_counter += 1
        additional_lang_index += 1
    
    # Generate Other Allied Health (15%)
    print(f"Generating {num_other} other allied health professionals...")
    for i in range(num_other):
        entries.append(generate_other_allied_entry(
            id_counter,
            require_additional[additional_lang_index]
        ))
        id_counter += 1
        additional_lang_index += 1
    
    # Verify language requirement
    additional_lang_count = sum(1 for e in entries if "," in e["language"] and e["language"] != "English")
    print(f"\nLanguage verification: {additional_lang_count} entries speak additional languages (target: {num_additional_lang})")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    
    # Write to CSV
    fieldnames = [
        "id", "doctor_name", "department", "speciality", "facility", "phone",
        "location", "board_certifications", "education", "residencies",
        "fellowships", "gender", "language", "insurance", "internship",
        "badge", "profile_pic", "is_active", "created_on"
    ]
    
    print(f"\nWriting {len(entries)} entries to {args.output}...")
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(entries)
    
    print(f"✅ Successfully generated {len(entries)} entries!")
    print(f"   - Physicians: {num_physicians}")
    print(f"   - Advanced Practice: {num_advanced_practice}")
    print(f"   - Therapists: {num_therapists}")
    print(f"   - Other Allied Health: {num_other}")

if __name__ == "__main__":
    main()

