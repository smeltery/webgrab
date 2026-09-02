"""Resource processing with streaming architecture."""

import asyncio
from collections.abc import AsyncIterator, Callable

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Response

from ..models import CaptureStats, Resource
from .filters import DefaultFilter, ResourceFilter


class ResourceProcessor:
    """Processes browser responses into Resource objects."""

    def __init__(
        self,
        resource_filter: ResourceFilter | None = None,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the processor.

        Args:
            resource_filter: Filter to determine which resources to capture.
            on_progress: Optional callback for progress updates.
        """
        self.filter = resource_filter or DefaultFilter()
        self.on_progress = on_progress
        self.stats = CaptureStats()

    async def process_response(self, response: Response) -> Resource | None:
        """Process a single response into a Resource.

        Args:
            response: Playwright Response object.

        Returns:
            Resource object or None if filtered out or failed.
        """
        self.stats.total_requests += 1
        url = response.url
        status = response.status
        content_type = response.headers.get("content-type", "")

        # Apply filter
        if not self.filter.should_capture(url, content_type, status):
            self.stats.skipped_urls += 1
            return None

        # Fetch body
        try:
            body = await response.body()
            self.stats.successful_captures += 1
            self.stats.total_bytes += len(body)

            # Convert headers dict
            headers = dict(response.headers)

            return Resource(
                url=url,
                content_type=content_type,
                body=body,
                headers=headers,
                status_code=status,
            )
        except PlaywrightError as e:
            self.stats.failed_captures += 1
            if self.on_progress:
                self.on_progress(f"Failed to capture {url}: {e}")
            return None

    async def process_responses_stream(
        self, response_queue: asyncio.Queue[Response | None]
    ) -> AsyncIterator[Resource]:
        """Process responses from a queue as a stream.

        Args:
            response_queue: Queue of responses to process. None signals end.

        Yields:
            Resource objects as they are processed.
        """
        while True:
            response = await response_queue.get()
            if response is None:
                # Sentinel value indicating end of stream
                break

            resource = await self.process_response(response)
            if resource is not None:
                yield resource
