from superapp import SuperApp, admin_only
class Online(SuperApp):
    def __init__(self):
        super().__init__()

    def launch(self):
        delay = 60*60
        while self.is_active:
            try:
                if self.api.pub_api.groups.getOnlineStatus(group_id=self.keys.public_id).get('status') != 'online':
                    self.api.pub_api.groups.enableOnline(group_id=self.keys.public_id)
            except Exception as e:
                self.sender.report('Exception in onliner:\n'+str(type(e))+'\n'+str(e))
            self.sleep(delay)

    def get_info(self):
        status = 'Статус сообщества - '
        if self.api.pub_api.groups.getOnlineStatus(group_id=self.keys.public_id).get('status') == 'online':
            status = status + '&#10004;Online'
        else:
            status = status + '&#10006;Offline'
        return status
