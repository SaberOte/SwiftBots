import time


class ErrorRateMonitor:
    def __init__(self, cooldown: int = 60):
        self.start_time = time.time()
        self.cooldown = cooldown
        self.error_count = 0
        self.last_error_time = 0.0

    def evoke(self) -> int:
        """
        Remember time and rate of errors.
        Return rate of errors from 0 to ERROR NUMBER PER COOLDOWN.
        """
        self.error_count += 1
        elapsed_time = time.time() - self.last_error_time
        self.last_error_time = time.time()
        if elapsed_time > self.cooldown:
            self.error_count = 1  # reset counter because a previous error was long ago:
        return self.error_count

    @property
    def since_start(self) -> float:
        return time.time() - self.start_time
