import os
from dotenv import load_dotenv
from pymongo import MongoClient

class Database:
    def __init__(self):
        load_dotenv()
        url = os.getenv("MONGO_URI")
        self.client = MongoClient(url)
        self.db = self.client["family"]
        self.collection = self.db["family_members"]
            
    def find_person_by_id(self, person_id):
        person = self.collection.find_one({"_id": person_id})
        return person
    
    def find_person_by_name(self, name):
        person = self.collection.find({"name": {
            "$regex": name,
            "$options": "i"  # case-insensitive
        }})
        return list(person)

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
        children = self.collection.find({"parents": {"$in": [person_id]}})
        return list(children)   
    
    def add_person(self, person_data):
        result = self.collection.insert_one(person_data)
        return str(result.inserted_id)
    
    def get_all_people(self):
        people = self.collection.find()
        return list(people)
    
    def update_person(self, person_id, update_data):
        result = self.collection.update_one({"_id": person_id}, {"$set": update_data})
        return result.modified_count > 0
    
    def create_person(self, person_data):
        result = self.collection.insert_one(person_data)
        return str(result.inserted_id)