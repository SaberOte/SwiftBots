import sys, communicator, configparser

argv = sys.argv[1:]
task_id = argv[0]
config_path = argv[1]

#получить имя плагина и задачи
config = configparser.ConfigParser()
config.read(config_path)
task_name = None
for i in config.items('Tasks'):
  if i[1] == task_id:
    task_name = i[0]
    break
if task_name:
  comm = communicator.Communicator(config_path, 'cron')
  comm.send(task_name, 'listener')
  comm.close()
else:
  pass # задача уже удалена
