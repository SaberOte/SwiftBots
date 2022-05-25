import socket, random
class Communicator:
    BUFFER_AMOUNT = 8192

    def __init__(self, log=None, port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        is_random_port = None
        if port == 0:
            is_random_port = True
            counter = 1
            while 1:
                port = random.randint(49152, 65535)
                try:
                    self.sock.bind(('localhost', port))
                    break
                except OSError:
                    if counter >= 1000:
                        raise Exception('More than 1000 attempts to bind socket was unseccesfully')
                    counter += 1
                    continue
        else:
            is_random_port = False
            try:
                self.sock.bind(('localhost', port))
            except OSError:
                raise Exception('This port is already busy')
        self.port = port
        if log == None:
          log = print
        self.log = log
        if is_random_port:
            log(f'Binded socket with random port {port} with try {counter}')
        else:
            log(f'Binded socket with specified port {port}')
        
    def listen(self):
        self.log('Listening port %d...' % self.port)
        sock = self.sock
        sliced_messages = {}
        #cleaning
        self.sock.settimeout(0.01)
        while True:
            try:
                sock.recv(self.BUFFER_AMOUNT)
            except: break

        #listening
        while True:
            sock.settimeout(60*60*6)
            try:
                msg, addr = sock.recvfrom(self.BUFFER_AMOUNT)
            except socket.timeout: continue
            msg = msg.decode('utf-8')
            # strict check
            try:
              assert msg.startswith('SES'), 'Corrupted pattern of message in socket listener (SES...) - ' + msg
              try:
                  session_id = int(msg[3:9])
              except ValueError:
                  raise Exception('Corrupted pattern of message in socket listener (ses_number[3:9]) - ' + msg)
              assert msg.endswith('END') or msg.endswith('SLC'), 'Corrupted pattern of message in socket listener (wrong end) - ' + msg
            except Exception as e:
              self.close()
              raise e

            final_msg = ''
            if msg.endswith('END'):
                if session_id in sliced_messages:
                    final_msg = sliced_messages.pop(session_id) + msg[9:-3]
                    #received_messages[session_id] = final_msg
                    #print('session =',session_id, 'message -', final_msg)
                else:
                    #received_messages[session_id] = msg[9:-3]
                    final_msg = msg[9:-3]
                    #print('session =',session_id, 'message -', msg[9:-3])
                #print('Received message from', addr, 'with session_id =', session_id,  ':', final_msg)
                yield (final_msg, addr, session_id)
            elif msg.endswith('SLC'):
                if session_id in sliced_messages:
                    sliced_messages[session_id] += msg[9:-3]
                else:
                    sliced_messages[session_id] = msg[9:-3]

    def send(self, msg, port, session_id=0):
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
        # format: SES123456[sliceed_message]SLC
        for i in range(len(slices)):
            slices[i] = 'SES' + str(session_id) + slices[i]
            if i == len(slices)-1:
                slices[i] += 'END'
            else:
                slices[i] += 'SLC'
            self.sock.sendto(slices[i].encode('utf-8'), ('localhost', port))

    def close(self):
        self.sock.close()
