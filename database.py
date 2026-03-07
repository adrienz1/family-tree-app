import os
import json
from pymongo import MongoClient

#  Insert the family data from a json file into the MongoDB database. The JSON file is created by the parse.py script and contains the family data extracted from the text file.
def upload_data():
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