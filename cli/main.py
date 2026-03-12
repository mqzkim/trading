"""Trading System CLI entry point."""
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

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


@app.command()
def dashboard(
    portfolio_id: str = typer.Option("default", "--portfolio-id", help="Portfolio ID"),
):
    """Show portfolio dashboard with positions and drawdown status."""
    from src.portfolio.infrastructure.sqlite_position_repo import SqlitePositionRepository
    from src.portfolio.infrastructure.sqlite_portfolio_repo import SqlitePortfolioRepository
    from src.portfolio.domain.value_objects import DrawdownLevel

    pos_repo = SqlitePositionRepository()
    port_repo = SqlitePortfolioRepository()

    portfolio = port_repo.find_by_id(portfolio_id)
    positions = pos_repo.find_all_open()

    # Portfolio header
    if portfolio:
        value = portfolio.total_value_or_initial
        dd = portfolio.drawdown
        dd_level = portfolio.drawdown_level
    else:
        value = 100_000.0
        dd = 0.0
        dd_level = DrawdownLevel.NORMAL

    dd_color = {
        DrawdownLevel.NORMAL: "green",
        DrawdownLevel.CAUTION: "yellow",
        DrawdownLevel.WARNING: "red",
        DrawdownLevel.CRITICAL: "bold red",
    }.get(dd_level, "white")

    console.print(Panel(
        f"[bold]Value:[/bold] ${value:,.2f}  |  "
        f"[bold]Drawdown:[/bold] [{dd_color}]{dd * 100:.1f}%[/{dd_color}]  |  "
        f"[bold]Level:[/bold] [{dd_color}]{dd_level.value.upper()}[/{dd_color}]",
        title="Portfolio Dashboard",
        border_style="blue",
    ))

    if not positions:
        console.print("[dim]No open positions.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Qty", justify="right")
    table.add_column("Entry Price", justify="right")
    table.add_column("Market Value", justify="right")
    table.add_column("Stop Price", justify="right")
    table.add_column("Sector")
    table.add_column("Strategy")

    for pos in positions:
        stop_str = f"${pos.atr_stop.stop_price:,.2f}" if pos.atr_stop else "-"
        table.add_row(
            pos.symbol,
            str(pos.quantity),
            f"${pos.entry_price:,.2f}",
            f"${pos.market_value:,.2f}",
            stop_str,
            pos.sector,
            pos.strategy,
        )

    console.print(table)


@app.command()
def screener(
    top_n: int = typer.Option(20, "--top-n", help="Number of results"),
    min_score: float = typer.Option(60.0, "--min-score", help="Minimum composite score"),
    signal_filter: str = typer.Option("BUY", "--signal", help="Signal filter (BUY/SELL/HOLD)"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Screen top-N stocks by risk-adjusted score."""
    import duckdb
    from src.signals.infrastructure.duckdb_signal_store import DuckDBSignalStore

    conn = duckdb.connect("data/analytics.duckdb")
    store = DuckDBSignalStore(conn)
    results = store.query_top_n(top_n=top_n, min_composite=min_score, signal_filter=signal_filter)

    if output == "json":
        console.print_json(json.dumps(results, default=str))
        return

    if not results:
        console.print("[dim]No stocks match criteria.[/dim]")
        return

    table = Table(title="Stock Screener", show_header=True, header_style="bold cyan")
    table.add_column("Rank", justify="right", style="bold")
    table.add_column("Symbol", style="bold")
    table.add_column("Composite", justify="right")
    table.add_column("Risk-Adj", justify="right")
    table.add_column("Intrinsic Val", justify="right")
    table.add_column("MoS%", justify="right")
    table.add_column("Signal", justify="center")
    table.add_column("Strength", justify="right")

    for i, r in enumerate(results, 1):
        sig = r.get("direction", "-")
        sig_color = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(sig, "white")
        mos = r.get("margin_of_safety")
        mos_str = f"{mos * 100:.1f}%" if mos is not None else "-"
        iv = r.get("intrinsic_value")
        iv_str = f"${iv:,.2f}" if iv is not None else "-"
        strength = r.get("strength")
        strength_str = f"{strength:.1f}" if strength is not None else "-"

        table.add_row(
            str(i),
            r.get("symbol", "-"),
            f"{r.get('composite_score', 0):.1f}",
            f"{r.get('risk_adjusted_score', 0):.1f}",
            iv_str,
            mos_str,
            f"[{sig_color}]{sig}[/{sig_color}]",
            strength_str,
        )

    console.print(table)


@app.command()
def watchlist_add(
    symbol: str = typer.Argument(..., help="Ticker symbol to add"),
    notes: str = typer.Option(None, "--notes", "-n", help="Notes about this symbol"),
    alert_above: float = typer.Option(None, "--alert-above", help="Alert when price goes above"),
    alert_below: float = typer.Option(None, "--alert-below", help="Alert when price goes below"),
):
    """Add a symbol to the watchlist."""
    from src.portfolio.domain.value_objects import WatchlistEntry
    from src.portfolio.infrastructure.sqlite_watchlist_repo import SqliteWatchlistRepository

    repo = SqliteWatchlistRepository()
    entry = WatchlistEntry(
        symbol=symbol.upper(),
        notes=notes,
        alert_above=alert_above,
        alert_below=alert_below,
    )
    repo.add(entry)
    console.print(f"[green]Added {symbol.upper()} to watchlist.[/green]")


@app.command()
def watchlist_remove(
    symbol: str = typer.Argument(..., help="Ticker symbol to remove"),
):
    """Remove a symbol from the watchlist."""
    from src.portfolio.infrastructure.sqlite_watchlist_repo import SqliteWatchlistRepository

    repo = SqliteWatchlistRepository()
    repo.remove(symbol.upper())
    console.print(f"[yellow]Removed {symbol.upper()} from watchlist.[/yellow]")


@app.command()
def watchlist_list():
    """List all watchlist entries."""
    from src.portfolio.infrastructure.sqlite_watchlist_repo import SqliteWatchlistRepository

    repo = SqliteWatchlistRepository()
    entries = repo.find_all()

    if not entries:
        console.print("[dim]Watchlist is empty.[/dim]")
        return

    table = Table(title="Watchlist", show_header=True, header_style="bold cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Added")
    table.add_column("Notes")
    table.add_column("Alert Above", justify="right")
    table.add_column("Alert Below", justify="right")

    for e in entries:
        table.add_row(
            e.symbol,
            str(e.added_date),
            e.notes or "-",
            f"${e.alert_above:,.2f}" if e.alert_above else "-",
            f"${e.alert_below:,.2f}" if e.alert_below else "-",
        )

    console.print(table)


if __name__ == "__main__":
    app()
