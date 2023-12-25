from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.types import IChatView


def admin_only(func):
    """Decorator. Should wrap controller method to prevent non admin execution"""
    def wrapper(self, view: 'IChatView', context: 'IChatView.Context'):
        if view._admin is not None:
            if str(context.sender) != str(view._admin):
                view.refuse_async(context)
            else:
                func(self, view, context)
        else:
            view._logger.error('admin_only decorator requires `_admin` property in view')
            view.error_async(context)
    return wrapper
