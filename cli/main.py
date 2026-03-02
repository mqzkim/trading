"""Trading System CLI entry point."""
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

app = typer.Typer(name="trading", help="Trading System CLI")
console = Console()


@app.command()
def version():
    """Show version."""
    console.print("[bold green]Trading System v0.1.0[/bold green]")


@app.command()
def regime(
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Detect the current market regime."""
    from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
    from core.regime.classifier import classify
    from core.regime.weights import get_weights, get_risk_adjustment

    try:
        vix = get_vix()
        sp500_ratio = get_sp500_vs_200ma()
        yield_curve = get_yield_curve_slope()
    except Exception as e:
        console.print(f"[bold red]Error fetching market data: {e}[/bold red]")
        raise typer.Exit(code=1)

    result = classify(vix, sp500_ratio, adx=20.0, yield_curve_bps=yield_curve)
    weights = get_weights(result["regime"])
    risk_adj = get_risk_adjustment(result["regime"])

    if output == "json":
        console.print_json(json.dumps({
            "regime": result["regime"],
            "confidence": result["confidence"],
            "vix": vix,
            "sp500_vs_200ma": sp500_ratio,
            "yield_curve_bps": yield_curve,
            "strategy_weights": weights,
            "risk_adjustment": risk_adj,
            "warning": result.get("warning"),
        }))
        return

    # Table output
    table = Table(title="Market Regime Detection", show_header=True, header_style="bold cyan")
    table.add_column("Indicator", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Regime", f"[bold yellow]{result['regime']}[/bold yellow]")
    table.add_row("Confidence", f"{result['confidence']:.0%}")
    table.add_row("VIX", f"{vix:.2f}")
    table.add_row("S&P 500 / 200MA", f"{sp500_ratio:.4f}")
    table.add_row("Yield Curve (bps)", f"{yield_curve:.1f}")
    table.add_row("Risk Adjustment", f"{risk_adj:.1f}x")

    # Strategy weights sub-table
    weight_parts = [f"{k}: {v:.0%}" for k, v in weights.items()]
    table.add_row("Strategy Weights", " | ".join(weight_parts))

    if result.get("warning"):
        table.add_row("Warning", f"[bold red]{result['warning']}[/bold red]")

    console.print(table)


@app.command()
def score(
    symbol: str = typer.Argument(..., help="Ticker symbol (e.g. AAPL)"),
    strategy: str = typer.Option("swing", "--strategy", "-s", help="swing|position"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Compute composite score for a symbol."""
    from core.data.client import DataClient
    from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
    from core.regime.classifier import classify
    from core.scoring.composite import score_symbol
    from core.orchestrator import _estimate_fundamental_score, _estimate_technical_score

    symbol = symbol.upper()
    console.print(f"[dim]Fetching data for {symbol}...[/dim]")

    try:
        client = DataClient()
        data = client.get_full(symbol)
    except Exception as e:
        console.print(f"[bold red]Error fetching data: {e}[/bold red]")
        raise typer.Exit(code=1)

    indicators = data.get("indicators", {})
    price = data.get("price", {})
    close = price.get("close", 0.0)
    adx_val = indicators.get("adx14", 15.0) or 15.0

    # Regime for context
    try:
        vix = get_vix()
        sp500_ratio = get_sp500_vs_200ma()
        yield_curve = get_yield_curve_slope()
        regime_result = classify(vix, sp500_ratio, adx_val, yield_curve)
        regime_name = regime_result["regime"]
    except Exception:
        regime_name = "Transition"

    fund = data.get("fundamentals", {}).get("highlights", {})
    fundamental_result = {
        "safety_passed": True,
        "fundamental_score": _estimate_fundamental_score(fund),
    }
    technical_result = {
        "technical_score": _estimate_technical_score(indicators, close),
    }
    sentiment_result = {"sentiment_score": 50.0}

    result = score_symbol(symbol, fundamental_result, technical_result, sentiment_result, strategy)

    if output == "json":
        console.print_json(json.dumps(result, default=str))
        return

    table = Table(title=f"Composite Score: {symbol}", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Symbol", symbol)
    table.add_row("Strategy", strategy)
    table.add_row("Regime", regime_name)
    table.add_row("Composite Score", f"[bold yellow]{result.get('composite_score', 0):.1f}[/bold yellow]")
    table.add_row("Risk-Adjusted Score", f"{result.get('risk_adjusted_score', 0):.1f}")
    table.add_row("Safety Passed", "[green]YES[/green]" if result.get("safety_passed") else "[red]NO[/red]")
    table.add_row("Fundamental", f"{result.get('fundamental_score', 0):.1f}")
    table.add_row("Technical", f"{result.get('technical_score', 0):.1f}")
    table.add_row("Sentiment", f"{result.get('sentiment_score', 50):.1f}")

    console.print(table)


@app.command()
def signal(
    symbol: str = typer.Argument(..., help="Ticker symbol (e.g. AAPL)"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Generate 4-strategy consensus signal for a symbol."""
    from core.data.client import DataClient
    from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
    from core.regime.classifier import classify
    from core.signals.consensus import generate_signals

    symbol = symbol.upper()
    console.print(f"[dim]Generating signals for {symbol}...[/dim]")

    try:
        client = DataClient()
        data = client.get_full(symbol)
    except Exception as e:
        console.print(f"[bold red]Error fetching data: {e}[/bold red]")
        raise typer.Exit(code=1)

    indicators = data.get("indicators", {})
    adx_val = indicators.get("adx14", 15.0) or 15.0

    try:
        vix = get_vix()
        sp500_ratio = get_sp500_vs_200ma()
        yield_curve = get_yield_curve_slope()
        regime_result = classify(vix, sp500_ratio, adx_val, yield_curve)
        regime_name = regime_result["regime"]
    except Exception:
        regime_name = "Transition"

    result = generate_signals(symbol, data, regime_name)

    if output == "json":
        console.print_json(json.dumps(result, default=str))
        return

    # Consensus header
    consensus = result.get("consensus", "NEUTRAL")
    agreement = result.get("agreement", 0)
    color = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "yellow"}.get(consensus, "white")
    console.print(Panel(
        f"[bold {color}]{consensus}[/bold {color}] (Agreement: {agreement}/4)",
        title=f"Signal Consensus: {symbol}",
        subtitle=f"Regime: {regime_name}",
    ))

    # Per-strategy table
    methods = result.get("methods", {})
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Strategy", style="bold")
    table.add_column("Signal", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Max", justify="right")

    for name, m in methods.items():
        sig = m.get("signal", "N/A")
        sig_color = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(sig, "white")
        table.add_row(
            name,
            f"[{sig_color}]{sig}[/{sig_color}]",
            str(m.get("score", "N/A")),
            str(m.get("score_max", "N/A")),
        )

    table.add_row("", "", "", "")
    table.add_row(
        "[bold]Weighted Score[/bold]", "", f"[bold]{result.get('weighted_score', 0):.3f}[/bold]", "1.000"
    )

    console.print(table)


@app.command()
def analyze(
    symbol: str = typer.Argument(..., help="Ticker symbol (e.g. AAPL)"),
    capital: float = typer.Option(100000.0, "--capital", "-c", help="Portfolio capital"),
    strategy: str = typer.Option("swing", "--strategy", "-s", help="swing|position"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Run full 9-layer pipeline analysis for a symbol."""
    from core.orchestrator import run_full_pipeline

    symbol = symbol.upper()
    console.print(f"[dim]Running full pipeline for {symbol} (capital=${capital:,.0f}, strategy={strategy})...[/dim]")

    result = run_full_pipeline(symbol, capital, strategy)

    if output == "json":
        result_dict = {
            "symbol": result.symbol,
            "regime": result.regime,
            "regime_confidence": result.regime_confidence,
            "consensus": result.consensus,
            "agreement": result.agreement,
            "composite_score": result.composite_score,
            "safety_passed": result.safety_passed,
            "position_shares": result.position_shares,
            "position_value": result.position_value,
            "risk_level": result.risk_level,
            "entry_plan": result.entry_plan,
            "warnings": result.warnings,
            "error": result.error,
        }
        console.print_json(json.dumps(result_dict, default=str))
        return

    # Rich Panel report
    if result.error:
        console.print(Panel(
            f"[bold red]Error: {result.error}[/bold red]",
            title=f"Analysis: {result.symbol}",
        ))
        return

    # Regime section
    regime_color = {
        "Low-Vol Bull": "green", "High-Vol Bull": "yellow",
        "Low-Vol Range": "cyan", "High-Vol Bear": "red", "Transition": "white",
    }.get(result.regime, "white")

    # Signal section
    signal_color = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "yellow"}.get(
        result.consensus, "white"
    )

    # Build report lines
    lines = []
    lines.append(f"[bold]Regime:[/bold] [{regime_color}]{result.regime}[/{regime_color}] ({result.regime_confidence:.0%})")
    lines.append(f"[bold]Signal:[/bold] [{signal_color}]{result.consensus}[/{signal_color}] (Agreement: {result.agreement}/4)")
    lines.append(f"[bold]Composite Score:[/bold] [yellow]{result.composite_score:.1f}[/yellow] / 100")
    lines.append(f"[bold]Safety Gate:[/bold] {'[green]PASSED[/green]' if result.safety_passed else '[red]FAILED[/red]'}")
    lines.append("")
    lines.append("[bold underline]Position Sizing[/bold underline]")
    lines.append(f"  Shares: {result.position_shares}")
    lines.append(f"  Value: ${result.position_value:,.2f}")
    lines.append(f"  Risk Level: {result.risk_level}")
    lines.append("")

    if result.entry_plan:
        lines.append("[bold underline]Entry Plan[/bold underline]")
        status = result.entry_plan.get("status", "N/A")
        status_color = "green" if status == "APPROVED" else "red"
        lines.append(f"  Status: [{status_color}]{status}[/{status_color}]")
        if status == "APPROVED":
            lines.append(f"  Order Type: {result.entry_plan.get('order_type', 'N/A')}")
            lines.append(f"  Entry: ${result.entry_plan.get('entry_price', 0):,.2f}")
            lines.append(f"  Stop: ${result.entry_plan.get('stop_price', 0):,.2f}")
            lines.append(f"  Risk: {result.entry_plan.get('risk_pct', 0):.3f}%")

    if result.warnings:
        lines.append("")
        lines.append("[bold underline]Warnings[/bold underline]")
        for w in result.warnings:
            lines.append(f"  [yellow]- {w}[/yellow]")

    console.print(Panel(
        "\n".join(lines),
        title=f"Full Analysis: {result.symbol}",
        subtitle=f"Capital: ${capital:,.0f} | Strategy: {strategy}",
        border_style="blue",
    ))


if __name__ == "__main__":
    app()
