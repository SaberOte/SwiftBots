from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from swiftbots.types import IContext, IView


def get_available_commands_for_user(view: 'IView', is_admin: bool) -> dict[str: list[str]]:
    """
    :returns: dictionary of controllers and their commands.
    Key is a name of controller, value is list of commands which available for this user.
    Example:
    {
      'CalculatorApi': ['add', 'subtract', 'multiply'],
      'AdminApi': ['close', 'exit', 'start']
    }
    """

    result: dict[str: list[str]] = {}

    for ctrl in view.bot.controllers:
        if len(ctrl.cmds) > 0:
            if is_admin:
                commands = ctrl.cmds.keys()
            else:
                commands = filter(lambda cmd: not __is_function_admin_only_wrapped(ctrl.cmds[cmd]), ctrl.cmds.keys())
            result[ctrl.__class__.__name__] = list(commands)
    return result


def is_bot_has_default_message_handler(view: 'IView', context: 'IContext') -> bool:
    for ctrl in view.bot.controllers:
        if ctrl.default is not None and callable(ctrl.default):
            return True
    return False


def __is_function_admin_only_wrapped(func: Callable) -> bool:
    return func.__doc__ is not None and 'admin_only_wrapper' in func.__doc__
