import re
import json
import unicodedata
import uuid

NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

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
    return str(uuid.uuid5(NAMESPACE, normalize_name(name.lower())))

family_data = {}
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
def extract_data(file_name):
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
                parent2_id = None  # Reset partner for new parent
                if parent1_id not in family_data:
                    parent_doc = {
                        "_id": parent1_id,
                        "name": parent_name,
                        "location": None,
                        "partner": None,
                        "generation": parent_generation,
                        "parents": []
                    }
                    family_data[parent1_id] = parent_doc
                continue
            
            # Detect partner line
            if line.startswith("$"):
                parent2_id = name_to_uuid(line[1:].strip() + str(parent_generation))
                family_data[parent1_id]["partner"] = parent2_id
                continue
            
            # Child line
            if line.startswith("@"):
                line = line[1:].strip()
                if line.endswith("*"):
                    line = line[:-1].strip()
                name, location = clean_name(line)
                child_id = name_to_uuid(name + str(parent_generation + 1))
                child_doc = {
                    "_id": child_id,
                    "name": name,
                    "location": location,
                    "partner": None,
                    "generation": parent_generation + 1, 
                    "parents": [parent1_id, parent2_id] if parent1_id and parent2_id else [parent1_id] if parent1_id else []
                }
                family_data[child_id] = child_doc

    # Save to JSON file
    with open("family.json", "w", encoding="utf-8") as f:
        json.dump(list(family_data.values()), f, indent=4, ensure_ascii=False) # ensure ascii makes sure that the non-english characters are saved correctly in the json file. indent makes the json file more readable by adding indentation and newlines
    print("Saved family tree to family.json")