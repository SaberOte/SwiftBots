import json
import os
class KeyManager:
    filename = './../resources/data.json'
    def __init__(self):
        if not os.path.exists(self.filename):
            print('There is no '+self.filename)
            exit(0)
        with open(self.filename, 'r') as file:
            data = json.load(file)
            self.public_id = data.get('public_id')
            self.admin_id = data.get('admin_id')
            self.debug_person_id = data.get('debug_person_id')
            self.public_token = data.get('public_token')
