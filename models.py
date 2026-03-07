class person:
    def __init__(self, name, parent, location):
        self.name = name
        self.parent = parent
        self.location = location

    def get_name(self):
        return self.name
    
    def get_parent(self):
        return self.parent

    def get_location(self):
        return self.location

    
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