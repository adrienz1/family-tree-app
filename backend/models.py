class person:
    def __init__(self, name, parent1, parent2, location, generation):
        self.name = name
        self.parent1 = parent1
        self.parent2 = parent2
        self.location = location
        self.generation = generation

    def get_name(self):
        return self.name

    def get_location(self):
        return self.location
    
    def get_generation(self):
        return self.generation

class child(person):
    def __init__(self, name, parent1, parent2, location, generation):
        super().__init__(name, parent1, parent2, location, generation)
        
    def get_parents(self):
        return self.parent1, self.parent2
        
class parent(person):
    def __init__(self, name, location, generation):
        super().__init__(name, None, None, location, generation)
        self.children = []

    def add_child(self, child):
        self.children.append(child)
    
class user:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def get_name(self):
        return self.name
    
    def get_email(self):
        return self.email

    def get_password(self):
        return self.password