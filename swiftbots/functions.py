import inspect
from collections.abc import Callable
from traceback import format_exc
from typing import TYPE_CHECKING, Any, Dict, Optional

from swiftbots.all_types import IChatView, IContext
from swiftbots.types import AnnotatedType, DependableParam, DependencyContainer

if TYPE_CHECKING:
    from swiftbots.bots import Bot


def depends(dependency: Callable[..., Any]) -> DependencyContainer:
    """
    :param dependency: A "dependable" argument, must be function.
    """
    return DependencyContainer(dependency)


def is_dependable_param(param: AnnotatedType) -> bool:
    return (type(param) is AnnotatedType and
            any(filter(lambda x: type(x) is DependencyContainer, param.__metadata__)))


def get_dep_function(param: DependableParam) -> Callable[..., Any]:
    for dep_container in filter(lambda x: type(x) is DependencyContainer, param.__metadata__):
        function = dep_container.dependency
        return function


def resolve_function_args(function: Callable[..., Any], given_data: Dict) -> Dict:
    spec = inspect.getfullargspec(function)
    arg_names = spec.args
    params = {prm: spec.annotations[prm] for prm in spec.annotations if prm in arg_names}

    # Collect simple params
    not_dependable_params = {key for key in params
                             if not is_dependable_param(params[key])}
    invalid_params = set(not_dependable_params) - set(given_data.keys())
    assert len(invalid_params) == 0, f"Can't use parameters: {invalid_params}"

    args = {param_name: given_data[param_name] for param_name in not_dependable_params}

    # Collect dependable parameters
    dependable_params: Dict[str, DependableParam] = {key: params[key]
                                                     for key in params
                                                     if is_dependable_param(params[key])}
    # Dependency function also can have dependencies
    for param_name in dependable_params:
        dep_function = get_dep_function(dependable_params[param_name])
        dep_args = resolve_function_args(dep_function, given_data)
        # Call dependency function
        result = dep_function(**dep_args)
        args[param_name] = result

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
