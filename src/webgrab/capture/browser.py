"""Low-level Playwright browser operations."""

import asyncio
from collections.abc import Callable
from typing import Self

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Response,
    async_playwright,
)

from ..errors import BrowserError, NavigationError
from ..models import CaptureConfig


class BrowserManager:
    """Manages Playwright browser lifecycle."""

    def __init__(self, config: CaptureConfig) -> None:
        """Initialize browser manager.

        Args:
            config: Capture configuration.
        """
        self.config = config
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def __aenter__(self) -> Self:
        """Launch browser and create context."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless
            )
            self.context = await self.browser.new_context(
                accept_downloads=True,
                bypass_csp=self.config.bypass_csp,
                user_agent=self.config.user_agent,
                viewport={
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
            )
            self.page = await self.context.new_page()
            return self
        except Exception as e:
            await self.cleanup()
            raise BrowserError(f"Failed to launch browser: {e}") from e

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up browser resources."""
        await self.cleanup()

    async def cleanup(self) -> None:
        """Close browser and clean up resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, "playwright"):
            await self.playwright.stop()

    async def navigate(
        self, url: str, on_response: Callable[[Response], None] | None = None
    ) -> None:
        """Navigate to a URL and set up response handler.

        Args:
            url: URL to navigate to.
            on_response: Optional callback for each response.

        Raises:
            NavigationError: If navigation fails.
        """
        if not self.page:
            raise BrowserError("Browser not initialized")

        # Set up response handler before navigation
        if on_response:
            self.page.on("response", on_response)

        try:
            await self.page.goto(
                url, wait_until="networkidle", timeout=self.config.timeout
            )
        except Exception as e:
            raise NavigationError(f"Failed to navigate to {url}: {e}") from e

    async def wait_for_content(self, wait_time: int) -> None:
        """Wait for additional dynamic content.

        Args:
            wait_time: Seconds to wait.
        """
        if wait_time > 0:
            await asyncio.sleep(wait_time)
