if __name__ == '__main__':
    import os, json, re, time, vk_api
    from requests.exceptions import ReadTimeout, ConnectionError
    from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
    from inspect import getsourcefile

    os.chdir(os.path.abspath(getsourcefile(lambda:0))[:-11])
    data_path = os.getcwd()[:-7]+'/resources/data.json'
    with open(data_path, 'r') as data_file:
        data = json.load(data_file)
        token = data.get('public_token')
        public_id = data.get('public_id')
        admin_id = data.get('admin_id')
        debug_id = data.get('debug_person_id')
    ses = vk_api.VkApi(token=token, api_version='5.103')
    lp = VkBotLongPoll(ses, public_id)
    api = ses.get_api()

    def send(user, msg):
        api.messages.send(
                    user_id=user,
                    random_id=vk_api.utils.get_random_id(),
                    message=msg
        ) 

    def send_sticker(user, sticker_id):
        api.messages.send(
                    user_id=user,
                    random_id=vk_api.utils.get_random_id(),
                    sticker_id=sticker_id
        ) 

    mode = 0
    while True:
        try:
            if mode == 0:
                send(admin_id, 'Helper запущен!')
                mode = 1
            else:
                send(debug_id, 'helper перезапущен...')
 
            for event in lp.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    msg = event.object.message.get('text')
                    user = str(event.object.message.get('from_id'))
                    if user != admin_id:
                        continue

                    if msg.lower() == 'статус':
                        send(admin_id, 'Helper активен!&#10004;')
                        continue

                    if not msg.startswith(('do', 'Do')):
                        continue
                    command = msg[3:]

                    if command == 'hi':
                        send_sticker(user, 4275)
                        continue
                        
                    elif command == 'reboot':
                        send(admin_id, 'Helper закрыт')
                        os.system('python3 starthelper.py')
                        exit(0)
                        
                    elif command == 'logs':
                        command = 'python3 getlogs.py'

                    elif command == 'exit':
                        send(admin_id, 'Helper закрыт')
                        exit(0)

                    elif msg.lower() == 'do upbot':
                        os.system('python3 upbot.py')
                        send(admin_id, 'бот запускается...')
                        continue
                    
                    open('./out.txt', 'w').close()
                    os.system(command)
                        
                    with open('./out.txt', 'r') as out:
                        output = out.read()
                        if len(output) > 1:
                            i = 0
                            for c in output:
                                if ord(c) == 0:
                                    i += 1
                            output = output[i:]
                        if len(output) == 1:
                            output = 'No output...'
                        outputs = []
                        while len(output) > 4000:
                            outputs.append(output[:4000])
                            output = output[4000:]
                        outputs.append(output)
                        for msg in outputs:
                            if msg=='':
                                continue
                            send(admin_id, msg)
                    
        except ReadTimeout:
            time.sleep(50)
        except ConnectionError:
            time.sleep(60)
        except Exception as e:
            send(admin_id, "Exception in Helper!\n"+str(type(e))+'\n'+str(e))
            print(str(type(e))+'\n'+str(e))
            exit(0)

