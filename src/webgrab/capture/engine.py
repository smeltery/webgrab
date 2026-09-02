"""High-level resource capture orchestration."""

import asyncio
import time
from collections.abc import Callable

from playwright.async_api import Response

from ..models import CaptureConfig, CaptureStats, Resource
from .browser import BrowserManager
from .filters import DefaultFilter, ResourceFilter
from .processor import ResourceProcessor


class CaptureEngine:
    """Orchestrates the resource capture process."""

    def __init__(
        self,
        config: CaptureConfig,
        resource_filter: ResourceFilter | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize capture engine.

        Args:
            config: Capture configuration.
            resource_filter: Optional custom resource filter.
            on_status: Optional callback for status updates.
        """
        self.config = config
        self.filter = resource_filter or DefaultFilter()
        self.on_status = on_status
        self.response_queue: asyncio.Queue[Response | None] = asyncio.Queue()
        self.processor = ResourceProcessor(self.filter, on_status)

    def _update_status(self, message: str) -> None:
        """Send status update if callback is set.

        Args:
            message: Status message.
        """
        if self.on_status:
            self.on_status(message)

    async def capture_resources(self) -> tuple[list[Resource], CaptureStats]:
        """Capture all resources from the configured URL.

        Returns:
            Tuple of (resources list, capture statistics).
        """
        start_time = time.time()
        resources: list[Resource] = []

        self._update_status("Launching browser...")

        async with BrowserManager(self.config) as browser:

            def on_response(response: Response) -> None:
                """Callback for browser responses."""
                # Put response in queue for processing
                asyncio.create_task(self.response_queue.put(response))

            self._update_status(f"Navigating to {self.config.url}...")
            await browser.navigate(self.config.url, on_response)

            # Wait for additional content if configured
            if self.config.wait_time > 0:
                self._update_status(
                    f"Waiting {self.config.wait_time}s for additional content..."
                )
                await browser.wait_for_content(self.config.wait_time)

            # Signal end of responses
            await self.response_queue.put(None)

            # Process all responses
            self._update_status("Processing captured resources...")
            async for resource in self.processor.process_responses_stream(
                self.response_queue
            ):
                resources.append(resource)

        # Update statistics
        self.processor.stats.duration_seconds = time.time() - start_time

        return resources, self.processor.stats


async def capture_page_resources(
    config: CaptureConfig,
    resource_filter: ResourceFilter | None = None,
    on_status: Callable[[str], None] | None = None,
) -> tuple[list[Resource], CaptureStats]:
    """Convenience function to capture resources from a page.

    Args:
        config: Capture configuration.
        resource_filter: Optional custom resource filter.
        on_status: Optional callback for status updates.

    Returns:
        Tuple of (resources list, capture statistics).
    """
    engine = CaptureEngine(config, resource_filter, on_status)
    return await engine.capture_resources()
