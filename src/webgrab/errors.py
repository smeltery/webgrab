"""Custom exceptions for webgrab."""


class WebGrabError(Exception):
    """Base exception for all webgrab errors."""


class CaptureError(WebGrabError):
    """Base exception for capture-related errors."""


class BrowserError(CaptureError):
    """Exception raised for browser-related errors."""


class NavigationError(BrowserError):
    """Exception raised when page navigation fails."""


class ResourceError(CaptureError):
    """Exception raised when capturing a resource fails."""

    def __init__(self, url: str, message: str, original_error: Exception | None = None):
        """Initialize resource error.

        Args:
            url: URL of the resource that failed.
            message: Error message.
            original_error: Original exception if any.
        """
        self.url = url
        self.original_error = original_error
        super().__init__(f"Resource error for {url}: {message}")


class StorageError(WebGrabError):
    """Base exception for storage-related errors."""


class PathResolutionError(StorageError):
    """Exception raised when URL to path resolution fails."""


class FileWriteError(StorageError):
    """Exception raised when writing a file fails."""

    def __init__(self, path: str, message: str, original_error: Exception | None = None):
        """Initialize file write error.

        Args:
            path: Path that failed to write.
            message: Error message.
            original_error: Original exception if any.
        """
        self.path = path
        self.original_error = original_error
        super().__init__(f"Failed to write {path}: {message}")


class ConfigurationError(WebGrabError):
    """Exception raised for configuration errors."""
