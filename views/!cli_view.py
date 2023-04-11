raise
from ...templates.super_view import SuperView
from ...communicators import Communicator


class CliView(SuperView):
    def __init__(self, flags):
        super().__init__(flags)

    controllers = ['test', 'admin_panel']

    def listen(self):
        print("Welcome in the command line chat! Good day, Friend!")
        while True:
            msg = input('-> ')
            ans = {
                'command': msg,
                'sender': 'pidaras',
                'hash': 'kakoy blyat hash',
            }
            yield ans

    def reply(self, message):
        self.report(message)

    def unknown_command(self):
        self.report('Неизвестная команда')

    def out(self, message):
        print('\b\b\b-------------------')
        print(message)
        print('-------------------')
        print('->')

    def report(self, message):
        if message.startswith('THIS view dies'):
            print(message)
            return
        self.log('It is cliview_ghost. Do not frighten')
        communicator = Communicator('cliview_ghost')
        try:
            communicator.send('com|report|'+message, 'cliview')
        except:
            self.log('Sending to cliview impossible now')
        finally:
            communicator.close()

    inner_commands = {
        'report': out,
    }
