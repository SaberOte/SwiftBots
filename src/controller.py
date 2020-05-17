import threading, os, re, subprocess, datetime, time, sys

class Controller:
    user_id = ''
    message = ''
    def __init__(self, bot):
        self.bot = bot
        self.sender = bot.sender
        self.api = bot.api
        self.keys = bot.keys
    
    def refuse(self):
        self.sender.send(self.user_id, 'Сори, но этот бот служит только @polkadot')
        self.sender.send_sticker(self.user_id, '40')

    def send_pong(self):
        self.sender.send(self.user_id, 'pong')
        self.sender.send_sticker(self.user_id, '6111')

    def send_menu(self):   
        self.sender.send_menu()
                    
    def say_hi(self):
        self.sender.send_sticker(self.user_id, '12116')

    def start_helper(self):
        os.system('python3 ./../helper/starthelper.py')
        self.sender.report('helper запускается...')
	
    def reboot(self):
        os.system('python3 ./../helper/upbot.py')
        self.exit()

    def exit(self):
        self.sender.report('Бот остановлен.')
        print('Program\'s successfully suspended')
        sys.stdout.flush()
        os._exit(1)
        
    def common_status(self):
        status = 'Статус сообщества - '
        if self.api.pub_api.groups.getOnlineStatus(group_id=self.keys.public_id).get('status') == 'online':
            status = status + '&#10004;Online'    
        else:
            status = status + '&#10006;Offline'    
        dt = datetime.datetime.utcnow()-self.bot.start_time
        if dt.seconds < 60:
            dt = str(dt.seconds) + " секунд"
        elif dt.seconds < 60*60:
            dt = str(dt.seconds//60) + " минут"
        elif dt.seconds < 60*60*24:
            dt = str(dt.seconds//60//60) + " часов"
        elif dt.days < 7:
            dt = str(dt.days) + " дней"
        elif dt.days < 30:
            dt = str(dt.days // 7) + " недель"
        elif dt.days < 365:
            dt = str(dt.days//30) + " месяцев"
        else: dt = str(dt.days//365) + " лет"
        '''
        if dt.days != 0:
            dt = str(dt.days) + " дней"
        elif dt.seconds // 60 // 60 != 0:
            dt = str(dt.seconds//60//60) + " часов"
        elif dt.seconds // 60 != 0:
            dt = str(dt.seconds//60) + " минут"
        else:
            dt = str(dt.seconds) + " секунд"
        '''
        self.sender.report(status + f'\nС запуска бота прошло {dt}') 

    def unknown_cmd(self):
        self.api.pub_api.messages.markAsRead(group_id=self.keys.public_id,mark_conversation_as_read=1,peer_id=self.user_id)
        return
        self.sender.send(self.user_id, 'непонятная команда')
        
