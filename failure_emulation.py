import random
import logging

class FailureEmulator:
    def __init__(self, max_retries: int):
        self.max_retries = max_retries
        self.simulate_failure_page = random.randint(2, 10)
        self.simulate_failure_attempts_required = (
            random.randint(1, max_retries - 1) if max_retries > 1 else 0
        )
        self.simulate_failures_done = 0
        logging.info(
            f"Simulated failure will occur on page {self.simulate_failure_page} "
            f"and require {self.simulate_failure_attempts_required} failure(s) before succeeding."
        )

    def check_failure(self, current_page: int):
        if (
            current_page == self.simulate_failure_page and
            self.simulate_failures_done < self.simulate_failure_attempts_required
        ):
            self.simulate_failures_done += 1
            raise Exception(
                f"Simulated failure on page {current_page} "
                f"(attempt {self.simulate_failures_done} of {self.simulate_failure_attempts_required})"
            ) 