"""Domain models for webgrab."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Resource:
    """Immutable representation of a captured web resource."""

    url: str
    content_type: str
    body: bytes
    headers: dict[str, str]
    status_code: int

    @property
    def size(self) -> int:
        """Size of the resource body in bytes."""
        return len(self.body)


@dataclass
class CaptureConfig:
    """Configuration for the resource capture process."""

    url: str
    wait_time: int = 0
    timeout: int = 60000
    user_agent: str | None = None
    include_external: bool = False
    headless: bool = True
    bypass_csp: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.wait_time < 0:
            raise ValueError("wait_time must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class SaveConfig:
    """Configuration for the resource save process."""

    output_dir: Path
    base_url: str
    include_external: bool = False
    compress: bool = False
    overwrite: bool = False
    create_manifest: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.output_dir:
            raise ValueError("output_dir is required")


@dataclass
class CaptureStats:
    """Statistics about a capture operation."""

    total_requests: int = 0
    successful_captures: int = 0
    failed_captures: int = 0
    skipped_urls: int = 0
    total_bytes: int = 0
    duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_captures / self.total_requests) * 100


@dataclass
class SaveResult:
    """Result of a save operation."""

    saved_paths: list[Path] = field(default_factory=list)
    skipped_count: int = 0
    failed_saves: list[tuple[str, Exception]] = field(default_factory=list)

    @property
    def saved_count(self) -> int:
        """Number of successfully saved resources."""
        return len(self.saved_paths)

    @property
    def total_failures(self) -> int:
        """Total number of failed saves."""
        return len(self.failed_saves)
