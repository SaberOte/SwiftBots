from typing import Callable, Optional, TYPE_CHECKING
from abc import ABC

def admin_only(func):
    """Decorator. Should be with controller functions to prevent non admin execution"""
    def wrapper(self, view, context: dict):
        if 'admin' in dir(view):
            if str(context['sender']) != str(view.admin):
                view.refuse(context)
            else:
                func(self, view, context)
        else:
            view.error('admin_only decorator requires `admin` property in view', context)
    return wrapper


class BaseController(ABC):
    error: Callable
    report: Callable
    def init(self, error: Callable, report: Callable):
        """
        :param error: method to log the error and notify admin
        :param report: method to send message to admin
        """
        self.error = error
        self.report = report
