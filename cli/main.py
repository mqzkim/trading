"""Trading System CLI entry point."""
import typer
from rich.console import Console

app = typer.Typer(name="trading", help="Trading System CLI")
console = Console()


@app.command()
def version():
    """Show version."""
    console.print("[bold green]Trading System v0.1.0[/bold green]")


if __name__ == "__main__":
    app()
