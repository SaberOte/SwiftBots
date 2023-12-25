"""Minimal demonstration of the simple vkontakte view"""
import os

from swiftbots.views import VkontakteView


class MyVkVIew(VkontakteView):
    """
    Simple example how use vkontakte view
    """

    def __init__(self):
        token = os.environ.get('VK_TOKEN')
        assert token, f'Missing environment variable "VK_TOKEN"'
        admin = os.environ.get('VK_ADMIN_ID')
        public_id = os.environ.get('VK_PUBLIC')
        assert public_id, f'Missing environment variable "VK_PUBLIC"'

        super().__init__(token, int(public_id), admin)
