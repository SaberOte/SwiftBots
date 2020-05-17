import time, threading

class Online:
    is_active = True

    def do_online(self, delay, api, report, id):
        while self.is_active:
            try:
                if api.groups.getOnlineStatus(group_id=id).get('status') != 'online':
                    api.groups.enableOnline(group_id=id)
            except Exception as e:
                report('Exception in onliner:\n'+str(type(e))+'\n'+str(e))
            time.sleep(delay)

    def __init__(self, api, report, id):
        threading.Thread(target=self.do_online, args=(60*60, api, report, id)).start()

    def stop(self):
        self.is_active = False
