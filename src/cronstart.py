import sys
from communicator import Communicator
argv = sys.argv[1:]
plugin = argv[0]
task = argv[1]
names_path = argv[2]
comm = Communicator(names_path, 'crontest')
data = { 
  "plugin" : plugin,
  "task" : task,
}
comm.send(str(data), 'listener')
comm.close()
