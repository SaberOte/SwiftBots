class SuperView:
    def __init__(self, bot):
        self.bot = bot
        vars_v = vars(bot)
        for var in vars_v:
            if not var.startswith('_'):
                vars(self).update({var : vars_v.get(var) })
