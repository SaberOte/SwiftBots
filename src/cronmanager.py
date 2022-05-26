import crontab, getpass, os, configparser, uuid
def add(plugin, task, freq, proj_path):
  cron = crontab.CronTab(user=getpass.getuser())
  task_name = f'{plugin}|{task}'
  config_path = os.path.join(proj_path, "resources/config.ini") 
  
  # добавить задачу в конфиг
  config = configparser.ConfigParser()
  config.read(config_path)
  if 'Tasks' not in config.sections():
    config.add_section("Tasks")
  task_id = str(uuid.uuid4())
  config.set('Tasks', task_name, task_id)
  with open(config_path, 'w') as file:
    config.write(file)

  # очистить старые задачи с таким же именем
  for job in cron:
    if job.comment == task_name:
      cron.remove(job)
  
  # сделать посекундое ожидание
  sec = 0
  seconds = []
  while not sec or sec % 60:
    seconds.append(sec)
    sec += freq
  
  cronstart_path = os.path.join(proj_path, "src/cronstart.py")
  for i in seconds:
    command = f'sleep {i}; python3 "{cronstart_path}" "{task_id}" "{config_path}"'
    tab = cron.new(comment=task_name, command=command)
    tab.minute.every(seconds[-1]//60+1)
  cron.write()

def remove(plugin, task, proj_path):
  config_path = os.path.join(proj_path, "resources/config.ini") 
  cron = crontab.CronTab(user=getpass.getuser())
  task_name = f'{plugin}|{task}'
  for job in cron:
    if job.comment == task_name:
      cron.remove(job)
  cron.write()

  # убрать задачу из конфигa
  config = configparser.ConfigParser()
  config.read(config_path)
  config.remove_option('Tasks', task_name)
  with open(config_path, 'w') as file:
    config.write(file)

def get(config_path):
  config = configparser.ConfigParser()
  config.read(config_path)
  tasks = config.items('Tasks')
  return list(map(lambda x: x[0].split('|')[1], tasks))
