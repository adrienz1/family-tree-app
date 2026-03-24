import os
import json
from pymongo import MongoClient

class Database:
    def __init__(self):
        url = os.getenv("MONGO_URI")
        self.client = MongoClient(url)
        self.db = self.client["family"]
        self.collection = self.db["family_members"]
    
    #  Insert the family data from a json file into the MongoDB database. The JSON file is created by the parse.py script and contains the family data extracted from the text file.
    def upload_data(self):
        with open("family.json", "r", encoding="utf-8") as f:
            family_data = json.load(f)
            
        for person in family_data:
            person["_id"] = person.pop("id")
            
        self.collection.insert_many(family_data)
        print("Inserted family data into MongoDB")
        
    def find_person_by_id(self, person_id):
        person = self.collection.find_one({"_id": person_id})
        client = MongoClient(url)
        db = client["family"]
        collection = db["family_members"]
        
        person = collection.find_one({"_id": person_id})
        return person

    def find_parents(self, person_id):
        person = self.collection.find_one({"_id": person_id})
        if not person:
            return None
        
        parents = []
        for parent_id in person.get("parents", []):
            parent = self.collection.find_one({"_id": parent_id})
            if parent:
                parents.append(parent)
        
        return parents
    
    def find_children(self, person_id):
        children = self.collection.find({"parents": person_id})
        return list(children)   