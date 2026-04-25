import json
import os
import re
import uuid
import unicodedata
from dotenv import load_dotenv
from pymongo import MongoClient
import hashlib

class Database:
    def __init__(self):
        load_dotenv()
        url = os.getenv("MONGO_URI")
        self.client = MongoClient(url)
        self.db = self.client["family"]
        self.collection = self.db["family_members"]
        self.admin_collection = self.db["admins"]
        self.spouse_collection = self.db["spouses"]
            
    def find_person_by_id(self, person_id):
        person = self.collection.find_one({"_id": person_id})
        return person
    
    def find_person_by_name(self, name):
        person = self.collection.find({"name": {
            "$regex": name,
            "$options": "i"  # case-insensitive
        }})
        return list(person)

    def find_parent(self, person_id):
        person = self.find_person_by_id(person_id)
        if not person:
            return None
        
        parent = None
        for parent_id in person.get("parents", []):
            parent = self.find_person_by_id(parent_id)
            if parent:
                break
                
        return parent
    
    def find_children(self, person_id):
        children = self.collection.find({"parents": {"$in": [person_id]}})
        return list(children)   
    
    def find_spouse(self, person_id):
        spouse = self.spouse_collection.find_one({"_id": person_id})
        return spouse
    
    def add_person(self, person_data):
        result = self.collection.insert_one(person_data)
        return str(result.inserted_id)
    
    def get_all_people(self):
        people = self.collection.find().sort([
            ("generation", 1),
            ("name", 1)
        ])
        return list(people)
    
    def update_person(self, person_id, updated_data):
        person = self.find_person_by_id(person_id)
        if not person:
            return False

        generation = person.get("generation")
        update_fields = {}

        if "name" in updated_data and updated_data["name"] != person.get("name"):
            update_fields["name"] = updated_data["name"]

        if "location" in updated_data and updated_data["location"] != person.get("location"):
            update_fields["location"] = updated_data["location"]

        if updated_data.get("spouse"):
            spouse_name = updated_data["spouse"]
            spouse_id = name_to_uuid(spouse_name + str(generation))

            if person.get("spouse") != spouse_id:
                update_fields["spouse"] = spouse_id

        if not update_fields:
            return False

        result = self.collection.update_one(
            {"_id": person_id},
            {"$set": update_fields}
        )

        return result.modified_count > 0
    
    def validate_user(self, username, password):
        user = self.admin_collection.find_one({"username": username})
        if user:
            stored_password = user.get("password", "")
            salt = stored_password[:32]
            unsalted_hash = stored_password[32:]
            salted_password = password + salt
            hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
            if hashed_password == unsalted_hash:
                return True
        return False
    
def normalize_name(name):
    # Convert accented characters → base characters
    normalized = unicodedata.normalize("NFD", name)
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return normalized.lower()

def clean_name(line):
    match = re.match(r'^(.*?)\s*(?:\((.*?)\))?$', line)
    if match:
        name = match.group(1).strip()
        location = match.group(2).strip() if match.group(2) else None
        return name, location
    return None, None

def name_to_uuid(name):
    """Generate a deterministic UUID from name"""
    load_dotenv()
    NAMESPACE = uuid.UUID(os.getenv("NAMESPACE"))
    return str(uuid.uuid5(NAMESPACE, normalize_name(name.lower())))

def create_person(id=None, name=None, location=None, spouse=None, generation=None, parents=None):
    person_data = {
        "_id": id or name_to_uuid(name + str(generation)),
        "name": name,
        "location": location,
        "spouse": spouse,
        "generation": generation,
        "parents": parents
    }
    return person_data

# Gets the data from the text file and saves it to a JSON file
"""
    The order of the names in the text file is important. The parent name must be followed by the spouse name (if any) 
    and then the child names. The parent name is identified by the # symbol, the spouse name is identified by the $ symbol 
    and the child names are identified by the @ symbol. The child names can also contain the location in parentheses
"""
def extract_data(file_name):    
    family_data = {}
    spouse_data = {}
    child_id = None
    parent_name = None
    parent1_id = None
    parent2_id = None
    parent_generation = 1
    with open(file_name, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue
            
            # Parent line
            if line.startswith("#"):
                line = line[1:].strip()
                parent_generation = int(line.split()[-1])
                parent_name = line[:-1].strip()
                parent1_id = name_to_uuid(parent_name + str(parent_generation))
                parent2_id = None  # Reset spouse for new parent
                if parent1_id not in family_data:
                    parent_doc = create_person(
                        id=parent1_id,
                        name=parent_name,
                        location=None,
                        spouse=None,
                        generation=parent_generation,
                        parents=[]
                    )
                    family_data[parent1_id] = parent_doc
                continue
            
            # Detect spouse line
            if line.startswith("$"):
                if line.endswith("*"):
                    line = line[:-1]
                parent2_id = name_to_uuid(line[1:].strip() + str(parent_generation))
                family_data[parent1_id]["spouse"] = parent2_id
                parent2_doc = create_person(
                    id=parent2_id,
                    name=line[1:].strip(),
                    location=None,
                    spouse=parent1_id,
                    generation=parent_generation,
                    parents=[]
                )
                
                spouse_data[parent2_id] = parent2_doc
                continue
            
            # Child line
            if line.startswith("@"):
                line = line[1:].strip()
                if line.endswith("*"):
                    line = line[:-1].strip()
                name, location = clean_name(line)
                child_id = name_to_uuid(name + str(parent_generation + 1))
                child_doc = create_person(
                    id=child_id,
                    name=name,
                    location=location,
                    spouse=None,
                    generation=parent_generation + 1,
                    parents=[parent1_id, parent2_id] if parent1_id and parent2_id else [parent1_id] if parent1_id else []
                )
                family_data[child_id] = child_doc

    # Save to JSON file
    with open("family.json", "w", encoding="utf-8") as f:
        json.dump(list(family_data.values()), f, indent=4, ensure_ascii=False) # ensure ascii makes sure that the non-english characters are saved correctly in the json file. indent makes the json file more readable by adding indentation and newlines
    print("Saved family tree to family.json")# Save to JSON file
    
    with open("spouses.json", "w", encoding="utf-8") as f:
        json.dump(list(spouse_data.values()), f, indent=4, ensure_ascii=False) # ensure ascii makes sure that the non-english characters are saved correctly in the json file. indent makes the json file more readable by adding indentation and newlines
    print("Saved spouse data to spouses.json")

#  Insert the family data from a json file into the MongoDB database
def upload_data():
    load_dotenv()
    url = os.getenv("MONGO_URI")
    client = MongoClient(url)
    db = client["family"]
    collection = db["family_members"]
    collection2 = db["spouses"]
    with open("family.json", "r", encoding="utf-8") as f:
        family_data = json.load(f)
    collection.insert_many(family_data)
    print("Inserted family data into MongoDB")
    
    with open("spouses.json", "r", encoding="utf-8") as f:
        spouse_data = json.load(f)
    collection2.insert_many(spouse_data)
    print("Inserted spouse data into MongoDB")
    