"""High-level resource saving orchestration."""

from pathlib import Path

from ..errors import StorageError
from ..mime.detector import infer_extension
from ..models import Resource, SaveConfig, SaveResult
from ..url.parser import is_same_origin
from .deduplicator import PathDeduplicator
from .path_resolver import url_to_local_path
from .writer import write_file


class ResourceSaver:
    """Orchestrates saving resources to disk."""

    def __init__(self, config: SaveConfig) -> None:
        """Initialize the resource saver.

        Args:
            config: Save configuration.
        """
        self.config = config
        self.deduplicator = PathDeduplicator()

    def save_resource(self, resource: Resource) -> Path | None:
        """Save a single resource to disk.

        Args:
            resource: The resource to save.

        Returns:
            Path where resource was saved, or None if skipped.

        Raises:
            StorageError: If writing the resource fails.
            OSError: If path resolution or filesystem operations fail.
            ValueError: If URL or path inputs are invalid.
        """
        # Filter external resources if not included
        if not self.config.include_external and not is_same_origin(
            resource.url, self.config.base_url
        ):
            return None

        # Get base path from URL
        local_path = url_to_local_path(resource.url, self.config.output_dir)

        # Infer extension from content-type if needed
        path_str = str(local_path)
        path_with_ext = infer_extension(path_str, resource.content_type)
        local_path = Path(path_with_ext)

        # Deduplicate if path already used
        local_path = self.deduplicator.get_unique_path(local_path)

        write_file(local_path, resource.body)
        return local_path

    def save_resources(self, resources: list[Resource]) -> SaveResult:
        """Save all resources to disk.

        Args:
            resources: List of resources to save.

        Returns:
            SaveResult with statistics and any failures.
        """
        result = SaveResult()

        for resource in resources:
            try:
                saved_path = self.save_resource(resource)
                if saved_path is not None:
                    result.saved_paths.append(saved_path)
                else:
                    result.skipped_count += 1
            except (StorageError, OSError, ValueError) as e:
                result.failed_saves.append((resource.url, e))

        return result
