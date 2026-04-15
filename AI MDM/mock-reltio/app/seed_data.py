"""
Life-sciences seed data: HCPs (Healthcare Professionals), HCOs (Healthcare Organizations),
Products, and Affiliations. Includes intentional duplicates for governance demo.
"""

# HCPs - includes intentional duplicate pairs (variant spellings, name forms)
HCPS = [
    # Cluster 1: Sarah Chen - 3 variants
    {"FirstName": "Sarah", "LastName": "Chen", "MiddleName": "L", "Specialty": "Oncology", "NPI": "1234567890", "Email": "schen@mgh.org", "City": "Boston", "State": "MA", "Degree": "MD"},
    {"FirstName": "S", "LastName": "Chen", "Specialty": "Oncology", "NPI": "1234567890", "Email": "sarah.chen@partners.org", "City": "Boston", "State": "MA", "Degree": "MD"},
    {"FirstName": "Sara", "LastName": "Chen", "Specialty": "Hematology Oncology", "City": "Boston", "State": "MA", "Degree": "MD, PhD"},
    # Cluster 2: John Smith
    {"FirstName": "John", "LastName": "Smith", "Specialty": "Cardiology", "NPI": "2345678901", "Email": "jsmith@ccf.org", "City": "Cleveland", "State": "OH", "Degree": "MD"},
    {"FirstName": "Jonathan", "LastName": "Smith", "Specialty": "Cardiology", "City": "Cleveland", "State": "OH", "Degree": "MD"},
    # Cluster 3: Patel
    {"FirstName": "Anjali", "LastName": "Patel", "Specialty": "Endocrinology", "NPI": "3456789012", "City": "Houston", "State": "TX", "Degree": "MD"},
    {"FirstName": "Anjali", "LastName": "Patel", "MiddleName": "K", "Specialty": "Endocrinology Diabetes", "City": "Houston", "State": "TX", "Degree": "MD"},
    # Cluster 4: Garcia
    {"FirstName": "Maria", "LastName": "Garcia", "Specialty": "Pulmonology", "NPI": "4567890123", "City": "Miami", "State": "FL", "Degree": "MD"},
    {"FirstName": "Maria", "LastName": "Garcia-Lopez", "Specialty": "Pulmonology", "City": "Miami", "State": "FL", "Degree": "MD"},
    # Cluster 5: Wong
    {"FirstName": "David", "LastName": "Wong", "Specialty": "Neurology", "NPI": "5678901234", "City": "San Francisco", "State": "CA", "Degree": "MD"},
    {"FirstName": "Dave", "LastName": "Wong", "Specialty": "Neurology", "City": "San Francisco", "State": "CA", "Degree": "MD"},
    # Singletons
    {"FirstName": "Priya", "LastName": "Krishnan", "Specialty": "Rheumatology", "NPI": "6789012345", "City": "Chicago", "State": "IL", "Degree": "MD"},
    {"FirstName": "Michael", "LastName": "OBrien", "Specialty": "Gastroenterology", "NPI": "7890123456", "City": "Philadelphia", "State": "PA", "Degree": "MD"},
    {"FirstName": "Emily", "LastName": "Taylor", "Specialty": "Dermatology", "NPI": "8901234567", "City": "Seattle", "State": "WA", "Degree": "MD"},
    {"FirstName": "Robert", "LastName": "Johnson", "Specialty": "Psychiatry", "NPI": "9012345678", "City": "Atlanta", "State": "GA", "Degree": "MD"},
    {"FirstName": "Linda", "LastName": "Martinez", "Specialty": "Nephrology", "NPI": "1123456789", "City": "Phoenix", "State": "AZ", "Degree": "MD"},
    {"FirstName": "James", "LastName": "Anderson", "Specialty": "Oncology", "NPI": "2234567890", "City": "Boston", "State": "MA", "Degree": "MD"},
    {"FirstName": "Karen", "LastName": "Lee", "Specialty": "Oncology", "NPI": "3345678901", "City": "Boston", "State": "MA", "Degree": "MD"},
    {"FirstName": "Thomas", "LastName": "Brown", "Specialty": "Cardiology", "NPI": "4456789012", "City": "Dallas", "State": "TX", "Degree": "MD"},
    {"FirstName": "Susan", "LastName": "Davis", "Specialty": "Endocrinology", "NPI": "5567890123", "City": "Minneapolis", "State": "MN", "Degree": "MD"},
    {"FirstName": "Brian", "LastName": "Wilson", "Specialty": "Pulmonology", "NPI": "6678901234", "City": "Denver", "State": "CO", "Degree": "MD"},
    {"FirstName": "Jessica", "LastName": "Moore", "Specialty": "Neurology", "NPI": "7789012345", "City": "Portland", "State": "OR", "Degree": "MD"},
    {"FirstName": "Daniel", "LastName": "Clark", "Specialty": "Oncology", "NPI": "8890123456", "City": "Nashville", "State": "TN", "Degree": "MD"},
    {"FirstName": "Rachel", "LastName": "Hall", "Specialty": "Hematology", "NPI": "9901234567", "City": "Boston", "State": "MA", "Degree": "MD"},
    {"FirstName": "Kevin", "LastName": "Young", "Specialty": "Cardiology", "NPI": "1012345678", "City": "Cleveland", "State": "OH", "Degree": "MD"},
]

# HCOs - includes 3 variant pairs (Mass General, etc.)
HCOS = [
    {"Name": "Massachusetts General Hospital", "Type": "Academic Medical Center", "City": "Boston", "State": "MA", "DEA": "MA0001"},
    {"Name": "Mass General Hospital", "Type": "Hospital", "City": "Boston", "State": "MA"},
    {"Name": "MGH", "Type": "Hospital", "City": "Boston", "State": "MA"},
    {"Name": "Cleveland Clinic", "Type": "Academic Medical Center", "City": "Cleveland", "State": "OH", "DEA": "OH0001"},
    {"Name": "Cleveland Clinic Foundation", "Type": "Hospital", "City": "Cleveland", "State": "OH"},
    {"Name": "MD Anderson Cancer Center", "Type": "Cancer Center", "City": "Houston", "State": "TX", "DEA": "TX0001"},
    {"Name": "UT MD Anderson", "Type": "Cancer Center", "City": "Houston", "State": "TX"},
    {"Name": "UCSF Medical Center", "Type": "Academic Medical Center", "City": "San Francisco", "State": "CA"},
    {"Name": "Mayo Clinic Rochester", "Type": "Academic Medical Center", "City": "Rochester", "State": "MN"},
    {"Name": "Johns Hopkins Hospital", "Type": "Academic Medical Center", "City": "Baltimore", "State": "MD"},
    {"Name": "Memorial Sloan Kettering", "Type": "Cancer Center", "City": "New York", "State": "NY"},
    {"Name": "Dana-Farber Cancer Institute", "Type": "Cancer Center", "City": "Boston", "State": "MA"},
]

# Products - AZ-style pipeline (fictional names to avoid trademark issues)
PRODUCTS = [
    {"Name": "Tagrisso", "Therapy": "Oncology", "Indication": "EGFR-mutated NSCLC", "Status": "Marketed"},
    {"Name": "Imfinzi", "Therapy": "Oncology", "Indication": "Stage III NSCLC", "Status": "Marketed"},
    {"Name": "Lynparza", "Therapy": "Oncology", "Indication": "BRCA-mutated breast cancer", "Status": "Marketed"},
    {"Name": "Farxiga", "Therapy": "Cardiovascular Renal Metabolic", "Indication": "Type 2 Diabetes", "Status": "Marketed"},
    {"Name": "Brilinta", "Therapy": "Cardiovascular Renal Metabolic", "Indication": "Acute Coronary Syndrome", "Status": "Marketed"},
]
