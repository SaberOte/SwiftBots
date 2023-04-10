import os
import signal
import time
from typing import Callable
from src.botcore import crons
from src.botcore.templates.super_view import SuperView
from src.botcore.templates.super_controller import SuperController, admin_only
from src.botcore.views import launch_view


def remember_request(func):
    """Decorator for admin panel. Remembers last command, then it may be used to repeat this.
    Must be BELOW @admin_only"""
    def wrapper(self, view, context):
        self.last_exec = (func, view, context)
        func(self, view, context)
    return wrapper


class AdminPanel(SuperController):
    last_exec: tuple[Callable, SuperView, dict] = ()

    def __init__(self, bot):
        super().__init__(bot)

    @admin_only
    @remember_request
    def reboot(self, view: SuperView, context):
        """Reboot the core bot. """
        view.report('Now restarting...')
        self.log('Program is rebooting by admin')
        res_path = os.path.join(os.getcwd(), 'logs')
        os.system(f'nohup python3 main.py @botcore_core@ '
                  f'start -MS -FR > {res_path}/core_launch_log.txt 2>&1 &')
        time.sleep(10)
        # Class Communicator another view must force kill this process.
        # If it won't, something's wrong
        self.log('Program was not rebooted')
        view.report("Core isn't rebooted")

    @admin_only
    @remember_request
    def exit(self, view: SuperView, context):
        self._bot.communicator.close()
        self.log('Program is suspended by admin')
        view.report('Core stopped.')
        os.kill(os.getpid(), signal.SIGKILL)

    @admin_only
    @remember_request
    def update_module(self, view: SuperView, context):
        module: str = context['message']
        module = module.replace(' ', '_')
        if len(module) == 0:
            view.reply('You can\'t update all controllers at the time. Specify certain one', context)
            return
        updated = self._bot.controller_manager.update_controller(module)
        if updated > 0:
            view.reply(f'Controller {module}\'s updated in RAM', context)
            return
        try:
            updated = self._bot.views_manager.update_view(module)
        except Exception as e:
            view.reply(str(e), context)
            return
        if updated == 1:
            view.reply(f"View {module}'s updated in RAM, but it doesn't launched", context)
        elif updated == 2:
            view.reply(f"View {module}'s updated in RAM", context)
        elif updated == 0:
            view.reply('No such name modules', context)

    @admin_only
    @remember_request
    def start_view(self, view: SuperView, context):
        module: str = context['message']
        module = module.replace(' ', '_')
        if module in self._bot.views_manager.views:
            view.reply(f'{module} is already launched', context)
            return
        launch_view(module, [])
        view.reply(f'{module} is asked to start', context)

    @admin_only
    @remember_request
    def reboot_view(self, view: SuperView, context):
        module: str = context['message']
        module = module.replace(' ', '_')
        if module not in self._bot.views_manager.views:
            view.reply(f'{module} is not launched yet', context)
        view_flags = ['from reboot']
        try:
            del self._bot.views_manager.views[module]
        except KeyError:
            pass
        launch_view(module, view_flags)
        view.reply(f'{module} is asked to restart', context)

    @admin_only
    @remember_request
    def kill_view(self, view: SuperView, context):
        module: str = context['message']
        module = module.replace(' ', '_')
        if module not in self._bot.views_manager.views:
            view.reply(f'{module} is not launched', context)
            return
        killed: int = self._bot.views_manager.kill_view(module)
        if killed == 0:
            view.reply(f'View {module}\'s not launched!', context)
        elif killed == 1:
            view.reply(f'View {module} sent unexpected answer. Its destiny is unknown', context)
        elif killed == 2:
            view.reply(f'{module} stopped', context)
        del self._bot.views_manager.views[module]

    @admin_only
    def total_exit(self, view: SuperView, context):
        for module in self._bot.views_manager.views:
            self._bot.views_manager.kill_view(module)
        self.exit(view, context)

    @admin_only
    @remember_request
    def send_status(self, view: SuperView, context):
        views = self._bot.views_manager.ping_views()
        report = ''
        if len(views) > 0:
            report += 'Launched views:\n- ' + '\n- '.join(views) + '\n\n'
        else:
            report += 'No launched views\n\n'
        if len(self._bot.controller_manager.controllers) > 0:
            report += 'Loaded controllers:\n- ' + \
                  '\n- '.join([x.__module__.split('.')[-1] for x in self._bot.controller_manager.controllers])
        else:
            report += 'No loaded controllers'
        view.reply(report, context)

    @admin_only
    def repeat_cmd(self, view: SuperView, context: dict):
        if self.last_exec:
            func, view, context = self.last_exec
            func(self, view, context)
        else:
            view.reply('There is no command in memory', context)

    def _get_tasks_status(self):
        tasks = crons.get('../resources/config.ini')
        respond = ''
        all_tasks = []
        for x in self.bot.controller_manager.controllers:
            for j in x.tasks:
                all_tasks.append(j)
        for t in all_tasks:
            if t in tasks:
                respond += '- ' + t +' активен&#128640;\n'
        for t in all_tasks:
            if t not in tasks:
                respond += '- ' + t +' неактивен&#9898;\n'
        return respond

    def show_tasks(self):
        tasks = crons.get('../resources/config.ini')
        respond = ''
        all_tasks = []
        for x in self.bot.controller_manager.controllers:
            for j in x.tasks:
                all_tasks.append(j)
        for t in all_tasks:
            if t in tasks:
                respond += '- ' + t +' активен&#128640;\n'
        for t in all_tasks:
            if t not in tasks:
                respond += '- ' + t +' неактивен&#9898;\n'
        self.sender.send(self.user_id, respond)

    def schedule_task(self):
        task = self.message
        controller = None
        for cont in self.bot.controllers:
            if task in cont.tasks:
                controller = cont
        if controller == None:
            all_tasks = []
            for cont in self.bot.controllers:
                for x in cont.tasks:
                    all_tasks.append(x)
            self.sender.send(self.user_id, 'Такой задачи нет. Все задачи: ' + ', '.join(all_tasks))
            self.log(f'Unknown task {task} is called')
            return
        delay = controller.tasks[task][1]
        path = os.path.split(os.getcwd())[0]
        crons.add(controller.__class__.__name__, task, delay, path)
        self.log(f'Task {task} is scheduled')
        self.sender.send(self.user_id, 'Задача запущена')

    def unschedule_task(self):
        task = self.message
        controller = None
        for cont in self.bot.controllers:
            if task in cont.tasks:
                controller = cont
        if controller == None:
            all_tasks = []
            for cont in self.bot.controllers:
                for x in cont.tasks:
                    all_tasks.append(x)
            self.sender.send(self.user_id, 'Такой задачи нет. Все задачи: ' + ', '.join(all_tasks))
            self.log(f'Unknown task {task} is called')
            return
        path = os.path.split(os.getcwd())[0]
        crons.remove(controller.__class__.__name__, task, path)
        self.log(f'Task {task} is unscheduled')
        self.sender.send(self.user_id, 'Задача удалена')

    prefixes = {
        # "start": schedule_task,
        # "stop": unschedule_task,
        "update": update_module,
        "stop": kill_view,
        "exit": kill_view,
        "kill": kill_view,
        "reboot": reboot_view,
        "restart": reboot_view,
        "launch": start_view,
        "start": start_view,
    }
    cmds = {
        # "tasks": show_tasks,
        # "задачи": show_tasks,
        "выход": exit,
        "exit": exit,
        "stop": exit,
        "exit all": total_exit,
        "перезагрузить": reboot,
        "перезапустить": reboot,
        "reboot": reboot,
        "ребут": reboot,
        "status": send_status,
        ".": repeat_cmd,
    }
