"""Errors."""


class ExitApp(Exception):
    """Exception to indicate app should exit."""

    def __init__(self, reason, exit_code=1):
        """Initialize the exit app exception."""
        super().__init__(reason)
        self.reason = reason
        self.exit_code = exit_code
