from ..templates.vkontakte_view import VkontakteView
from ..config import read_config


class TestTgView(VkontakteView):
    controllers = ['test']

    def __init__(self):
        config = read_config('credentials.ini')
        self.token = config['VkView']['token']
        self.admin = config['VkView']['admin']
