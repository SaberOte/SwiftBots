import json
import os
class KeyManager:
    def __init__(self, path, log):
        if not os.path.exists(path):
            log('There is no '+path)
            os._exit(1)
        with open(path, 'r') as file:
            data = json.load(file)
            self.public_id = data.get('public_id')
            self.admin_id = data.get('admin_id')
            self.public_token = data.get('public_token')
            self.oper_ids = data.get('operator_ids')
            if self.admin_id not in self.oper_ids:
                self.oper_ids.append(self.admin_id)
