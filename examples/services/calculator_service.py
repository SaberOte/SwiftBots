class CalculatorService:

    def add(self, a, b):
        return a + b

    def sub(self, a, b):
        return a - b


calc: CalculatorService = CalculatorService()


def get_calculator_service():
    return calc
