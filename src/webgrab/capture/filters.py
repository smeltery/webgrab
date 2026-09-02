"""Resource filtering logic."""

from typing import Protocol

from ..url.parser import should_skip_url


class ResourceFilter(Protocol):
    """Protocol for resource filters."""

    def should_capture(self, url: str, content_type: str, status_code: int) -> bool:
        """Check if a resource should be captured.

        Args:
            url: Resource URL.
            content_type: Content-Type header.
            status_code: HTTP status code.

        Returns:
            True if resource should be captured.
        """
        ...


class DefaultFilter:
    """Default resource filter."""

    def should_capture(self, url: str, content_type: str, status_code: int) -> bool:
        """Check if a resource should be captured.

        Args:
            url: Resource URL.
            content_type: Content-Type header.
            status_code: HTTP status code.

        Returns:
            True if resource should be captured.
        """
        # Skip non-success responses
        if status_code < 200 or status_code >= 400:
            return False

        # Skip data URLs, blob URLs, etc.
        return not should_skip_url(url)


class CompositeFilter:
    """Composite filter that combines multiple filters."""

    def __init__(self, filters: list[ResourceFilter]) -> None:
        """Initialize composite filter.

        Args:
            filters: List of filters to apply.
        """
        self.filters = filters

    def should_capture(self, url: str, content_type: str, status_code: int) -> bool:
        """Check if a resource should be captured.

        Args:
            url: Resource URL.
            content_type: Content-Type header.
            status_code: HTTP status code.

        Returns:
            True if all filters approve capture.
        """
        return all(f.should_capture(url, content_type, status_code) for f in self.filters)
