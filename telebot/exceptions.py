class TelebotException(Exception):
    """Base exception for all library exceptions."""
    pass

class TelebotAPIError(TelebotException):
    """Raised when Telegram API returns an error."""
    def __init__(self, description: str, error_code: Optional[int] = None):
        self.description = description
        self.error_code = error_code
        super().__init__(f"Error {error_code}: {description}" if error_code else description)

class NetworkError(TelebotException):
    """Raised for network-related errors (e.g., timeouts)."""
    pass
