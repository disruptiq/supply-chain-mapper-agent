import sys
import time
from typing import Optional

class ProgressIndicator:
    """Simple progress indicator for CLI operations"""

    def __init__(self, total: int = 0, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.last_update = 0

    def update(self, increment: int = 1, new_description: Optional[str] = None):
        """Update progress and display"""
        self.current += increment
        if new_description:
            self.description = new_description

        # Throttle updates to avoid too much output
        current_time = time.time()
        if current_time - self.last_update < 0.1:  # Update at most 10 times per second
            return

        self.last_update = current_time
        self._display()

    def set_total(self, total: int):
        """Set the total number of items"""
        self.total = total

    def finish(self, message: str = "Complete"):
        """Finish the progress indicator"""
        elapsed = time.time() - self.start_time
        print(f"\r{message} ({elapsed:.1f}s)")
        sys.stdout.flush()

    def _display(self):
        """Display the current progress"""
        if self.total > 0:
            percentage = min(100, (self.current / self.total) * 100)
            bar_length = 30
            filled_length = int(bar_length * percentage / 100)
            bar = '=' * filled_length + '-' * (bar_length - filled_length)

            sys.stdout.write(f"\r{self.description}: [{bar}] {percentage:.1f}% ({self.current}/{self.total})")
        else:
            # Indeterminate progress
            spinner_chars = ['|', '/', '-', '\\']
            spinner = spinner_chars[int(time.time() * 2) % len(spinner_chars)]
            sys.stdout.write(f"\r{spinner} {self.description}...")

        sys.stdout.flush()

class Spinner:
    """Simple spinner for indeterminate progress"""

    def __init__(self, message: str = "Processing"):
        self.message = message
        self.start_time = time.time()
        self.running = False

    def start(self):
        """Start the spinner"""
        self.running = True
        self._spin()

    def stop(self, final_message: str = "Done"):
        """Stop the spinner"""
        self.running = False
        elapsed = time.time() - self.start_time
        print(f"\r{final_message} ({elapsed:.1f}s)")

    def _spin(self):
        """Run the spinner in a separate thread"""
        import threading

        def spin():
            spinner_chars = ['|', '/', '-', '\\']
            i = 0
            while self.running:
                sys.stdout.write(f"\r{spinner_chars[i % len(spinner_chars)]} {self.message}")
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1

        thread = threading.Thread(target=spin, daemon=True)
        thread.start()
