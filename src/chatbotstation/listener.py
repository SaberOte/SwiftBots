from traceback import format_exc
import ast, threading, traceback
from . import crons


class Listener:
    def __init__(self, bot):
        self._bot = bot
        self.log = bot.log
        self.report = bot.report
        self.error = bot.error
        self.communicator = bot.communicator

    def check_handlers(self, command, view, context):
        controllers = self._bot.controller_manager.controllers
        accepted_controllers = [x.lower() for x in view.controllers]
        controllers = list(filter(lambda cont: cont.__module__.split('.')[-1] in accepted_controllers, controllers))
        # check "cmds"
        for controller in controllers:
            if command in controller.cmds:
                return controller.cmds[command], controller
        # then check "prefixes"
        for controller in controllers:
            for prefix in controller.prefixes:
                if command.startswith(prefix):
                    if len(prefix) == len(command):
                        context['message'] = ''
                    elif command[len(prefix)] == ' ':
                        context['message'] = command[len(prefix)+1:]
                    else:
                        continue
                    return controller.prefixes[prefix], controller
        # finally check "any"
        for controller in controllers:
            if callable(controller.any):
                return controller.any.__func__, controller
        return None, None

    def handle_message(self, data, sender_view):
        context = ast.literal_eval(data)
        message = context['message']
        view = self._bot.views_manager.views[sender_view]
        method, controller = self.check_handlers(message, view, context)
        if not controller:
            view.unknown_command(context)
            return
        if not callable(method):
            self.error(
                f'There\'s fatal error! "{str(method)}" from class "{type(controller).__name__}" is not a method '
                'or a function!')
            return
        self.log(f'Method "{method.__name__}" from class "{type(controller).__name__}" is called')
        try:
            method(controller, view, context)
        except Exception as e:
            view.error(format_exc(), context)

    def do_cron(self, controller_name, task):
        raise Exception("Сейчас не работает. ИЗ за изменения контекста")
        controller = None
        for cont in self._bot.controller_manager.controllers:
            if task in cont.tasks:
                controller = cont
        if not controller:
            crons.remove(controller_name, task)
            self.log(f'Message {task} is not recognized. Then removed')
            return
        task_info = controller.tasks[task]
        view_name = task_info[2]
        try:
            view = next(filter(lambda x: x == view_name, self._bot.views_manager.views))
            view = self._bot.views_manager.views[view]
        except StopIteration:
            self.error(f'View {view_name} is disabled or does not exist. Call from cron {controller_name} {task}')
            return
        method = task_info[0]
        if not callable(method):
            self.error(
                f'There\'s fatal error! "{str(method)}" from class "{type(controller).__name__}" is not a method '
                'or a function!')
            return
        self.log(f'Method "{method.__name__}" from class "{type(controller).__name__}" is called by cron')
        try:
            method(controller, view)
        except Exception as e:
            self.error(
                f'Exception in "{method.__name__}" from "{type(controller).__name__}":\n{str(type(e))}\n{str(e)}')

    def handle_signal(self, raw_data):
        try:
            # Могут прийти 3 типа сообщения:
            # mes|... - сообщение формата mes|информация. Приходит от вьюшки
            # cron|... - сообщение от крона. имеет формат controller_name|task
            # report|... - сообщение от какого то компонента. Переслать одмену
            # Если ни один не подходит, то считается, что это сообщение от внутренних компонентов бота

            raw_message = raw_data['message']
            self.log(f'Came message: {raw_message}')
            if raw_message.startswith('mes|'):
                sender_view = raw_data['sender_view']
                self.handle_message(raw_message[4:], sender_view)
            elif raw_message.startswith('cron|'):
                controller_name, task = raw_message[5:].split('|')
                if controller_name is None or task is None:
                    self.error('Unknown form of cron task' + str(controller_name) + ' ' + str(task))
                self.do_cron(controller_name, task)
            elif raw_message.startswith('report|'):
                self.report(raw_message[7:])
            elif raw_message.startswith('started'):
                new_view = raw_data['sender_view']
                self._bot.views_manager.fill_views_dict([new_view])
            elif raw_message.startswith('unknown|'):
                self.report('View received unknown message: ' + raw_message[8:])
            else:
                self.report('Unknown message from ' + raw_data['sender_view'] + ' in listener:\n'+str(raw_message))

        except Exception as e:
            self.error(format_exc())
            # self.error(f'Exception in handling message:\n{str(type(e))}\n{str(e)}')

    def listen(self):
        self.log('Start listening...')
        while 1:
            try:
                for raw_data in self.communicator.listen():
                    threading.Thread(target=self.handle_signal, args=(raw_data,), daemon=True).start()
            except Exception as e:
                self.error(f'Exception in Listener:\n{str(type(e))}\n{str(e)}')
