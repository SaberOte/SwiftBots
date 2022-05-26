import communicator
class Listener():
  def __init__(self, log):
    self.log = log
    self.communicator = communicator.Communicator('../resources/config.ini', 'mainlistener')
  
  def listen(self):
    for command in self.communicator.listen():
      self.log(command)
