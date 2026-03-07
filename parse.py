import re
import json
import uuid
from dotenv import load_dotenv
from pymongo import MongoClient

NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")
load_dotenv()

def clean_name(name):
    name = name.replace("*", "").strip()
    return " ".join(word.capitalize() for word in name.split())

def extract_location(line):
    match = re.search(r"\((.*?)\)", line)
    return match.group(1).strip().title() if match else None

def name_to_uuid(name):
    """Generate a deterministic UUID from name"""
    return str(uuid.uuid5(NAMESPACE, name))

family_data = []
family_data_dict = {}
child_id = None
parent_name = None
parent1_id = None
parent2_id = None

# Gets the data from the text file and saves it to a JSON file
"""
    The order of the names in the text file is important. The parent name must be followed by the partner name (if any) 
    and then the child names. The parent name is identified by the # symbol, the partner name is identified by the $ symbol 
    and the child names are identified by the @ symbol. The child names can also contain the location in parentheses
"""
def extract_data():
    with open("family.txt", "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue
            
            # Parent line
            if line.startswith("#"):
                parent_name = line[1:].strip()
                parent1_id = name_to_uuid(parent_name)
                parent2_id = None  # Reset partner for new parent
                continue
            
            # Detect partner line
            if line.startswith("$"):
                parent2_id = name_to_uuid(line[1:].strip())
                continue
            
            
            if line.startswith("@"):
                name_part = line[1:].strip()
                name = clean_name(re.sub(r"\(.*?\)", "", name_part))
                child_id = name_to_uuid(name + parent_name)  # Combine child name with parent name for uniqueness
                child_doc = {
                    "id": child_id,
                    "name": name,
                    "location": None,
                    "partner": None,
                    "parents": [parent1_id, parent2_id] if parent1_id and parent2_id else [parent1_id] if parent1_id else []
                }
                family_data.append(child_doc)
                #partner_name = None  # Reset partner for next parent
            

    # Save to JSON file
    with open("family.json", "w", encoding="utf-8") as f:
        json.dump(family_data, f, ensure_ascii=False, indent=2)
    print("Saved family tree to family.json")

def connect_to_mongoDB():
    url = os.getenv("MONGO_URI")
    client = MongoClient(url)
    db = client["family"]
    collection = db["family_members"]
    
    with open("family.json", "r", encoding="utf-8") as f:
        family_data = json.load(f)
        
    for person in family_data:
        person["_id"] = person.pop("id")
        
    collection.insert_many(family_data)
    print("Inserted family data into MongoDB")
    
if __name__ == "__main__":
    #extract_data()
    connect_to_mongoDB()