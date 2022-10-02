import socket, random, configparser, os


class Communicator:
    BUFFER_AMOUNT = 8192
    sock = None

    def __init__(self, config_dir, name, log=print):
        if not os.path.exists(config_dir):
            raise Exception('No such config directory for names')
        self.config_dir = config_dir
        self.log = log
        self.name = name
        
    def get_name(self, port):
        config = configparser.ConfigParser()
        config.read(self.config_dir)
        for i in config.items("Names"):
            if i[1] == port:
                return i[0]
        raise Exception('No such port in Names config')

    def get_port(self, name):
        config = configparser.ConfigParser()
        config.read(self.config_dir)
        return int(config.get("Names", name))

    def set_name(self):
        if not self.port:
            raise Exception("Port is not assigned")
        config = configparser.ConfigParser()
        config.read(self.config_dir)
        if 'Names' not in config.sections():
            config.add_section("Names")
        config.set("Names", self.name, str(self.port))
        with open(self.config_dir, 'w') as file:
            config.write(file)

    def assign_port(self, port=0):
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        is_random_port = None
        if port == 0:
            is_random_port = True
            counter = 1
            while 1:
                port = random.randint(49152, 65535)
                try:
                    self.sock.bind(('localhost', port))
                    self.port = port
                    break
                except OSError:
                    if counter >= 1000:
                        raise Exception('More than 1000 attempts to bind socket was unsuccesfully')
                    counter += 1
                    continue
        else:
            is_random_port = False
            try:
                self.sock.bind(('localhost', port))
                self.port = port
            except OSError:
                raise Exception('This port is already busy')
        self.set_name()
        if is_random_port:
            self.log(f'Binded socket with random port {port} with try {counter}')
        else:
            self.log(f'Binded socket with specified port {port}')

    def listen(self, requested=None):
        if not self.sock:
            self.assign_port()
        self.log('Listening port %d...' % self.port)
        sliced_messages = {}
        sock = self.sock
        #cleaning
        sock.settimeout(0.001)
        while True:
            try:
                sock.recv(self.BUFFER_AMOUNT)
            except: break

        if requested:
            requested_ses_id = self.send(*requested)
        #listening
        try:
          while True:
              if requested:
                  sock.settimeout(1)
              else:
                  sock.settimeout(60*60*6)
              try:
                  msg, addr = sock.recvfrom(self.BUFFER_AMOUNT)
              except socket.timeout:
                  if requested:
                      yield None
                  continue
              msg = msg
              # strict check
              try:
                assert msg.startswith(b'SES'), 'Corrupted pattern of message in socket listener (SES...) - ' + msg
                try:
                    session_id = int(msg[3:9])
                except ValueError:
                    raise Exception('Corrupted pattern of message in socket listener (ses_number[3:9]) - ' + msg)
                assert msg.endswith(b'END') or msg.endswith(b'SLC'), 'Corrupted pattern of message in socket listener (wrong end) - ' + msg
              except Exception as e:
                self.close()
                raise e

              final_msg = ''
              if msg.endswith(b'END'):
                  if session_id in sliced_messages:
                      final_msg = sliced_messages.pop(session_id) + msg[9:-3]
                  else:
                      final_msg = msg[9:-3]
                  if not requested or requested and session_id == requested_ses_id:
                      yield {
                        'message': final_msg.decode('utf-8'),
                        'address': addr,
                        'session_id': session_id,
                      }
              elif msg.endswith(b'SLC'):
                  if session_id in sliced_messages:
                      sliced_messages[session_id] += msg[9:-3]
                  else:
                      sliced_messages[session_id] = msg[9:-3]
        except Exception as e:
          self.close()
          raise e

    def send(self, msg, name, session_id=0):
        msg = msg.encode('utf-8')
        port = self.get_port(name)
        if not self.sock:
            self.assign_port()
        # session_id generating
        if session_id == 0:
            session_id = random.randint(100000, 999999)
                
        # cutting message on slices. If message size isn't greater than the buffer, then message won't be cut
        slice_size = self.BUFFER_AMOUNT - 12
        slices = []
        slice = msg 
        if len(msg) > slice_size:
            while len(slice) > slice_size:
                slices.append(slice[:slice_size])
                slice = slice[slice_size:]
        slices.append(slice)

        # format: SES123456[all_message]END
        # format: SES123456[sliced_message]SLC
        for i in range(len(slices)):
            slices[i] = 'SES'.encode('utf-8') + str(session_id).encode('utf-8') + slices[i]
            if i == len(slices)-1:
                slices[i] += 'END'.encode('utf-8')
            else:
                slices[i] += 'SLC'.encode('utf-8')
            try:
              self.sock.sendto(slices[i], ('localhost', port))
            except:
              self.assign_port()
              self.sock.sendto(slices[i], ('localhost', port))
        return session_id

    def request(self, msg, name):
        for i in self.listen((msg, name)):
            return i

    def close(self):
        if self.sock:
            self.sock.close()
        config = configparser.ConfigParser()
        config.read(self.config_dir)
        if 'Names' not in config.sections():
            config.add_section("Names")
        if config.remove_option("Names", self.name):
          with open(self.config_dir, 'w') as file:
              config.write(file)
