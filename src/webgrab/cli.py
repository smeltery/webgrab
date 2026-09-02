"""CLI entry point for webgrab."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .capture.engine import capture_page_resources
from .config import create_capture_config, create_save_config
from .errors import BrowserError, ConfigurationError, NavigationError, WebGrabError
from .storage.saver import ResourceSaver
from .url.parser import parse_url

app = typer.Typer(
    name="webgrab",
    help="Capture all resources from a webpage like browser DevTools Sources tab.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"webgrab {__version__}")
        raise typer.Exit()


@app.command()
def capture(
    url: str = typer.Argument(
        ...,
        help="URL of the webpage to capture resources from.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for saved resources. Defaults to ./webgrab_output",
    ),
    wait: int = typer.Option(
        0,
        "--wait", "-w",
        help="Additional seconds to wait after page load for JS content.",
    ),
    include_external: bool = typer.Option(
        False,
        "--include-external", "-e",
        help="Include external resources (CDN assets, third-party scripts).",
    ),
    version: bool = typer.Option(
        False,
        "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Capture all resources loaded by a webpage and save them locally."""
    # Validate URL
    try:
        parsed = parse_url(url)
        full_url = parsed.geturl()
    except ConfigurationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Set default output directory
    if output is None:
        output = Path("./webgrab_output")

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Capturing resources from:[/bold] {full_url}")
    console.print(f"[bold]Output directory:[/bold] {output.absolute()}")

    if include_external:
        console.print("[dim]Including external resources[/dim]")

    # Create configurations
    capture_config = create_capture_config(full_url, wait_time=wait)
    save_config = create_save_config(output, full_url, include_external=include_external)

    # Capture resources
    try:
        with console.status("[bold blue]Loading page and capturing resources...") as status:
            def on_status(msg: str) -> None:
                status.update(f"[bold blue]{msg}")

            resources, stats = asyncio.run(
                capture_page_resources(capture_config, on_status=on_status)
            )
    except BrowserError as e:
        console.print(f"[red]Browser Error: {e}[/red]")
        console.print("[dim]Hint: Make sure you've run 'playwright install chromium'[/dim]")
        raise typer.Exit(1)
    except NavigationError as e:
        console.print(f"[red]Navigation Error: {e}[/red]")
        raise typer.Exit(1)
    except WebGrabError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(130)

    console.print(f"[green]OK[/green] Captured {len(resources)} resources")
    if stats.skipped_urls > 0:
        console.print(f"[dim]Skipped {stats.skipped_urls} URLs (filtered)[/dim]")

    # Save resources
    if resources:
        with console.status("[bold blue]Saving resources to disk..."):
            saver = ResourceSaver(save_config)
            result = saver.save_resources(resources)

        console.print(f"[green]OK[/green] Saved {result.saved_count} resources")
        if result.skipped_count > 0:
            console.print(f"[dim]Skipped {result.skipped_count} external resources (use --include-external to include)[/dim]")
        if result.total_failures > 0:
            console.print(f"[yellow]Warning: {result.total_failures} resources failed to save[/yellow]")
    else:
        console.print("[yellow]No resources captured[/yellow]")

    console.print(f"\n[bold green]Done![/bold green] Resources saved to: {output.absolute()}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
