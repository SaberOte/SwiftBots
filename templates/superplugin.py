from functools import wraps
def admin_only(func):
    @wraps(func)
    def check(self, *args, **kwargs):
        if self.user_id not in self.keys.oper_ids and self.user_id != self.keys.admin_id:
            self.refuse()
        else: 
            func(self, *args, **kwargs)
    return check

def superadmin_only(func):
    @wraps(func)
    def check(self, *args, **kwargs):
        if self.user_id != self.keys.admin_id:
            self.refuse()
        else: 
            func(self, *args, **kwargs)
    return check

class SuperPlugin:
    cmds = {}
    message = ''
    user_id = ''
    prefixes = {} 
    def __init__(self, bot):
        self.bot = bot
        vars_v = vars(bot)
        for var in vars_v:
            if not var.startswith('_'):
                vars(self).update({var : vars_v.get(var) })

    def refuse(self):
        self.sender.send(self.user_id, 'Эта команда недоступна для вас')
        #self.sender.send_sticker(self.user_id, '40')
        self.log('User %s has rejected' % self.user_id)
