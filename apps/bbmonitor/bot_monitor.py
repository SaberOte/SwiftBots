import time
from superapp import SuperApp, admin_only
class BaseBotMonitor(SuperApp):
    def __init__(self):
        super().__init__()
        super_is_all_right = self.is_all_right
        self.last_check = time.time()
        def is_all_right_adapter(*args, **kwargs):
            self.last_check = time.time()
            return super_is_all_right(*args, **kwargs)
        self.is_all_right = is_all_right_adapter

    def launch(self):
        is_botbase_alive = True
        while self.is_active:
            if is_botbase_alive and time.time() - self.last_check > 2*60*60:
                self.sender.report('BOTBASE перестал работать!')
                is_botbase_alive = False
            elif not is_botbase_alive and time.time() - self.last_check < 2*60*60:
                is_botbase_alive = True
            self.sleep(60*10)

    def get_info(self):
        now = time.time()
        t = self.last_check
        dif = int(now - t)
        hours = dif // 60*60
        minutes = dif // 60
        seconds = dif
        return f'Последняя проверка ботом была {(str(hours)+" часов ") if hours > 0 else ""} {(str(minutes)+" минут ") if minutes > 0 else ""} {(str(seconds)+" секунд ") if seconds > 0 else ""} назад'
