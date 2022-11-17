import vk_api
from vk_api.bot_longpoll import VkBotLongPoll

class ApiManager:
    def __init__(self, keys, log):
        try:
            session = vk_api.VkApi(token=keys.public_token, api_version='5.103')
            self.lp = VkBotLongPoll(session, keys.public_id)
            self.pub_api = session.get_api()
        except Exception as e:
            log('!!ERROR!! Critical error in ApiManager!\n'+str(type(e))+'\n'+str(e))
            import os
            os._exit(1)
