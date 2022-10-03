import sys, communicator
from config import readconfig
task_id = sys.argv[1]

#получить имя плагина и задачи
config = readconfig()
task_name = None
for i in config.items('Tasks'):
  if i[1] == task_id:
    task_name = i[0]
    break
if task_name:
  comm = communicator.Communicator('cron')
  comm.send(task_name, 'core')
  comm.close()
else:
  pass # задача уже удалена
