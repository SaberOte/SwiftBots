import sys
from .communicators import Communicator
from .config import read_config
task_id = sys.argv[1]

#получить имя плагина и задачи
config = read_config('config.ini')
task_name = None
for i in config.items('Tasks'):
  if i[1] == task_id:
    task_name = i[0]
    break
if task_name:
  comm = Communicator('cron')
  comm.send('cron|'+task_name, 'core')
  comm.close()
else:
  pass # задача уже удалена
