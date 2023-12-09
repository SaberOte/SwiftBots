from swiftbots.types import Controller, View


class Bot:
    """Storage of controllers and views"""

    view_type: type[View]
    controller_types: list[type[Controller]]
    view: View
    controllers: list[Controller]

    def __init__(self, view_type: type[View], controller_types: list[type[Controller]]):
        self.view_type = view_type
        self.controller_types = controller_types
