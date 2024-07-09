import inspect
import random
import string
from collections.abc import Callable
from traceback import format_exc
from typing import TYPE_CHECKING, Any, Dict, Optional

from swiftbots.all_types import IChatView, IContext
from swiftbots.types import DependencyContainer

if TYPE_CHECKING:
    from swiftbots.bots import Bot


def depends(dependency: Callable[..., Any]) -> DependencyContainer:
    """
    :param dependency: A "dependable" argument, must be function.
    """
    return DependencyContainer(dependency)


def is_dependable_param(param: inspect.Parameter) -> bool:
    return isinstance(param.default, DependencyContainer)


def resolve_function_args(function: Callable[..., Any], given_data: Dict) -> Dict:
    sig = inspect.signature(function)
    args = {}
    for param in sig.parameters.values():
        name = param.name
        if is_dependable_param(param):  # dependency to resolve
            # Dependency function also can have dependencies
            dep: DependencyContainer = param.default
            dep_func = dep.dependency
            dep_args = resolve_function_args(dep_func, given_data)
            # Call dependency function
            result = dep_func(**dep_args)
            args[name] = result
        elif name not in given_data:
            raise AssertionError(f"Can't use parameter {param}")
        else:  # simple parameter
            args[name] = given_data[name]

    return args


def decompose_bot_as_dependencies(bot: 'Bot') -> Dict[str, Any]:
    return {
        'name': bot.name,
        'view': bot.view,
        'logger': bot.logger,
        'controllers': bot.controllers,
        'db_session_maker': bot.db_session_maker,
    }


async def call_raisable_function_async(func: Callable[[], Any], bot: 'Bot', context: Optional[IContext] = None) -> Any:
    try:
        return await func()
    except (AttributeError, TypeError, KeyError, AssertionError) as e:
        await bot.logger.critical_async(
            f"Fix the code. Critical `{e.__class__.__name__}` "
            f"raised:\n{e}.\nFull traceback:\n{format_exc()}"
        )
        if context is not None and isinstance(bot.view, IChatView):
            await bot.view.error_async(context)
    except Exception as e:
        await bot.logger.exception_async(
            f"Bot {bot.name} was raised with unhandled `{e.__class__.__name__}` "
            f"and kept on working:\n{e}.\nFull traceback:\n{format_exc()}"
        )
        if context is not None and isinstance(bot.view, IChatView):
            await bot.view.error_async(context)


def generate_name(count: int = 7) -> str:
    assert count >= 1, 'Name cannot be length less than 1'
    return str(''.join(random.choices(string.ascii_lowercase + string.digits, k=count)))
