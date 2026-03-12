"""Trading System CLI entry point."""
import asyncio
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(name="trading", help="Trading System CLI")
console = Console()

# -- Bootstrap context (lazy-loaded) --
_ctx: dict | None = None


def _get_ctx() -> dict:
    """Lazily bootstrap the application context and cache it."""
    global _ctx
    if _ctx is None:
        from src.bootstrap import bootstrap
        _ctx = bootstrap()
    return _ctx


@app.command()
def version():
    """Show version."""
    console.print("[bold green]Trading System v0.1.0[/bold green]")


@app.command()
def regime(
    history: int = typer.Option(0, "--history", help="Show N days of regime history"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Detect the current market regime."""
    ctx = _get_ctx()
    handler = ctx["regime_handler"]

    if history > 0:
        # History mode: query saved regimes from repository
        from datetime import datetime, timedelta, timezone

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=history)
        regimes = handler._regime_repo.find_by_date_range(start, end)

        if output == "json":
            import json as json_mod

            data = [
                {
                    "regime_type": r.regime_type.value,
                    "confidence": r.confidence,
                    "confirmed_days": r.confirmed_days,
                    "is_confirmed": r.is_confirmed,
                    "detected_at": r.detected_at.isoformat(),
                }
                for r in regimes
            ]
            console.print_json(json_mod.dumps(data))
            return

        # Table output for history
        table = Table(
            title=f"Regime History (past {history} days)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Date", style="dim")
        table.add_column("Regime", style="bold")
        table.add_column("Confidence", justify="right")
        table.add_column("Confirmed Days", justify="right")
        table.add_column("Status")

        for r in regimes:
            regime_color = {
                "Bull": "green",
                "Bear": "red",
                "Sideways": "yellow",
                "Crisis": "bold red",
            }.get(r.regime_type.value, "white")
            status = (
                "[green]Confirmed[/green]"
                if r.is_confirmed
                else "[dim]Pending[/dim]"
            )
            table.add_row(
                r.detected_at.strftime("%Y-%m-%d"),
                f"[{regime_color}]{r.regime_type.value}[/{regime_color}]",
                f"{r.confidence:.0%}",
                str(r.confirmed_days),
                status,
            )

        console.print(table)
        if not regimes:
            console.print(
                "[dim]No regime data found for this period. "
                "Run 'regime' command first to detect.[/dim]"
            )
        return

    # Current regime detection
    from src.regime.application.commands import DetectRegimeCommand

    cmd = DetectRegimeCommand(
        vix=0.0, sp500_price=0.0, sp500_ma200=0.0, adx=0.0, yield_spread=0.0,
    )

    console.print("[dim]Fetching market data for regime detection...[/dim]")
    result_wrapper = handler.handle(cmd)

    if not result_wrapper.is_ok():
        console.print(
            f"[bold red]Regime detection failed: {result_wrapper.error}[/bold red]"
        )
        raise typer.Exit(code=1)

    result = result_wrapper.value

    if output == "json":
        console.print_json(json.dumps(result, default=str))
        return

    # Table output
    regime_type = result["regime_type"]
    regime_color = {
        "Bull": "green",
        "Bear": "red",
        "Sideways": "yellow",
        "Crisis": "bold red",
    }.get(regime_type, "white")

    table = Table(
        title="Market Regime Detection",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Indicator", style="bold")
    table.add_column("Value", justify="right")

    table.add_row(
        "Regime",
        f"[{regime_color}]{regime_type}[/{regime_color}]",
    )
    table.add_row("Confidence", f"{result['confidence']:.0%}")
    table.add_row("VIX", f"{result['vix']:.2f}")
    table.add_row("ADX", f"{result['adx']:.1f}")
    table.add_row("Yield Spread", f"{result['yield_spread']:.2f}%")
    table.add_row(
        "S&P 500 vs MA200",
        f"{result['sp500_deviation_pct']:+.2f}%"
        + (" (above)" if result["sp500_above_ma200"] else " (below)"),
    )
    table.add_row("Confirmed Days", str(result["confirmed_days"]))
    table.add_row(
        "Status",
        "[green]Confirmed[/green]"
        if result["is_confirmed"]
        else "[dim]Pending[/dim]",
    )

    if regime_type in ("Bear", "Crisis"):
        table.add_row(
            "Warning",
            f"[bold red]{regime_type} regime -- consider defensive positioning[/bold red]",
        )

    console.print(table)


@app.command()
def score(
    symbol: str = typer.Argument(..., help="Ticker symbol (e.g. AAPL)"),
    strategy: str = typer.Option("swing", "--strategy", "-s", help="swing|position"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Compute composite score for a symbol."""
    from src.scoring.application.commands import ScoreSymbolCommand

    symbol = symbol.upper()
    console.print(f"[dim]Fetching data for {symbol}...[/dim]")

    ctx = _get_ctx()
    handler = ctx["score_handler"]
    cmd = ScoreSymbolCommand(symbol=symbol, strategy=strategy)
    result_wrapper = handler.handle(cmd)

    if not result_wrapper.is_ok():
        console.print(f"[bold red]Scoring failed: {result_wrapper.error}[/bold red]")
        raise typer.Exit(code=1)

    result = result_wrapper.unwrap()

    # Regime is informational context, not part of scoring
    regime_name = "N/A"
    try:
        from core.data.market import get_vix, get_sp500_vs_200ma, get_yield_curve_slope
        from core.regime.classifier import classify
        vix = get_vix()
        sp500_ratio = get_sp500_vs_200ma()
        yield_curve = get_yield_curve_slope()
        regime_result = classify(vix, sp500_ratio, 20.0, yield_curve)
        regime_name = regime_result["regime"]
    except Exception:
        regime_name = "Transition"

    if output == "json":
        json_result = {k: v for k, v in result.items() if k != "event"}
        console.print_json(json.dumps(json_result, default=str))
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

    # Technical Indicators sub-table (if sub-scores available)
    sub_scores = result.get("technical_sub_scores", [])
    if sub_scores:
        tech_table = Table(
            title="Technical Indicators",
            show_header=True,
            header_style="bold cyan",
        )
        tech_table.add_column("Indicator", style="bold")
        tech_table.add_column("Score", justify="right")
        tech_table.add_column("Explanation")

        for sub in sub_scores:
            score_val = sub.get("value", 0)
            if score_val >= 60:
                score_style = "green"
            elif score_val >= 40:
                score_style = "yellow"
            else:
                score_style = "red"

            tech_table.add_row(
                sub.get("name", "-"),
                f"[{score_style}]{score_val:.1f}[/{score_style}]",
                sub.get("explanation", "-"),
            )

        console.print(tech_table)


def _build_signal_symbol_data(symbol: str) -> dict:
    """Fetch data needed by 4 strategy evaluators."""
    try:
        from core.data.client import DataClient

        client = DataClient()
        data = client.get_full(symbol)
    except Exception:
        return {}

    indicators = data.get("indicators", {})
    financials = data.get("financials", {})
    return {
        # CAN SLIM inputs
        "eps_growth_qoq": financials.get("eps_growth_qoq"),
        "eps_cagr_3y": financials.get("eps_cagr_3y"),
        "near_52w_high": indicators.get("near_52w_high", False),
        "volume_ratio": indicators.get("volume_ratio", 1.0),
        "relative_strength": indicators.get("relative_strength", 50),
        "institutional_increase": financials.get("institutional_increase", False),
        # market_uptrend will be injected by handler from regime_type
        # Magic Formula inputs
        "earnings_yield": financials.get("earnings_yield"),
        "return_on_capital": financials.get("return_on_capital"),
        "ey_percentile": financials.get("ey_percentile", 50.0),
        "roc_percentile": financials.get("roc_percentile", 50.0),
        # Dual Momentum inputs
        "return_12m": indicators.get("return_12m"),
        "return_12m_benchmark": indicators.get("return_12m_benchmark"),
        "tbill_rate": indicators.get("tbill_rate", 0.04),
        # Trend Following inputs
        "above_ma50": indicators.get("above_ma50", False),
        "above_ma200": indicators.get("above_ma200", False),
        "adx": indicators.get("adx14", 15.0) or 15.0,
        "at_20d_high": indicators.get("at_20d_high", False),
    }


def _render_signal_output(
    data: dict, regime_type: str | None, regime_confidence: float | None,
) -> None:
    """Render Rich Panel + Table + reasoning for signal output."""
    direction = data["direction"]
    dir_color = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(direction, "white")
    consensus_count = data.get("consensus_count", 0)
    methodology_count = data.get("methodology_count", 4)

    # Panel header
    subtitle = ""
    if regime_type:
        conf_str = f" ({regime_confidence:.0%} confidence)" if regime_confidence else ""
        subtitle = f"Regime: {regime_type}{conf_str}"

    console.print(Panel(
        f"[bold {dir_color}]{direction}[/bold {dir_color}] ({consensus_count}/{methodology_count} strategies agree)",
        title=f"Signal Consensus: {data['symbol']}",
        subtitle=subtitle,
    ))

    # Strategy breakdown table
    weights = data.get("strategy_weights", {})
    scores = data.get("methodology_scores", {})
    methodology_directions = data.get("methodology_directions", {})
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Strategy", style="bold")
    table.add_column("Signal", justify="center")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")

    for method_key in ["CAN_SLIM", "MAGIC_FORMULA", "DUAL_MOMENTUM", "TREND_FOLLOWING"]:
        display_name = method_key.replace("_", " ").title()
        if display_name == "Can Slim":
            display_name = "CAN SLIM"
        score_val = scores.get(method_key, 0.0)
        weight_val = weights.get(method_key, 0.25)
        sig = methodology_directions.get(method_key, "N/A")
        sig_color = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(sig, "white")
        score_color = "green" if score_val >= 60 else ("yellow" if score_val >= 40 else "red")
        table.add_row(
            display_name,
            f"[{sig_color}]{sig}[/{sig_color}]",
            f"[{score_color}]{score_val:.1f}[/{score_color}]",
            f"{weight_val:.0%}",
        )

    # Weighted strength summary
    strength = data.get("strength", 0)
    table.add_row("", "", "", "")
    table.add_row("[bold]Weighted Strength[/bold]", "", f"[bold]{strength:.1f}[/bold]", "")
    console.print(table)

    # Composite score info
    composite = data.get("composite_score")
    if composite is not None:
        safety = data.get("safety_passed", True)
        safety_str = "[green]PASS[/green]" if safety else "[red]FAIL[/red]"
        console.print(f"  Composite Score: {composite:.1f}/100 | Safety Gate: {safety_str}")

    # Full reasoning chain below table (SIGNAL-07)
    reasoning_trace = data.get("reasoning_trace", "")
    if reasoning_trace:
        console.print()
        console.print(Panel(reasoning_trace, title="Reasoning Chain", border_style="dim"))


@app.command()
def signal(
    symbol: str = typer.Argument(..., help="Ticker symbol (e.g. AAPL)"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Generate 4-strategy consensus signal for a symbol."""
    ctx = _get_ctx()
    symbol = symbol.upper()
    console.print(f"[dim]Generating signals for {symbol}...[/dim]")

    # 1. Get regime from DDD handler (sentinel zeros trigger auto-fetch)
    from src.regime.application.commands import DetectRegimeCommand

    regime_result = ctx["regime_handler"].handle(
        DetectRegimeCommand(vix=0.0, sp500_price=0.0, sp500_ma200=0.0, adx=0.0, yield_spread=0.0)
    )
    regime_type = None
    regime_confidence = None
    if regime_result.is_ok():
        regime_data = regime_result.unwrap()
        regime_type = regime_data.get("regime_type")
        regime_confidence = regime_data.get("confidence")

    # 2. Get composite score from DDD handler
    from src.scoring.application.commands import ScoreSymbolCommand

    score_result = ctx["score_handler"].handle(ScoreSymbolCommand(symbol=symbol))
    composite_score = None
    safety_passed = True
    if score_result.is_ok():
        score_data = score_result.unwrap()
        composite_score = score_data.get("composite_score")
        safety_passed = score_data.get("safety_passed", True)

    # 3. Build symbol_data for signal adapter
    symbol_data = _build_signal_symbol_data(symbol)

    # 4. Generate signal through DDD handler
    from src.signals.application.commands import GenerateSignalCommand

    cmd = GenerateSignalCommand(
        symbol=symbol,
        composite_score=composite_score,
        safety_passed=safety_passed,
        regime_type=regime_type,
        symbol_data=symbol_data,
    )
    result = ctx["signal_handler"].handle(cmd)

    if result.is_err():
        console.print(f"[bold red]Error: {result.error}[/bold red]")
        raise typer.Exit(code=1)

    data = result.unwrap()

    if output == "json":
        console.print_json(json.dumps(data, default=str))
        return

    # 5. Rich output -- Panel + Table + reasoning
    _render_signal_output(data, regime_type, regime_confidence)


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
    from src.portfolio.domain.value_objects import DrawdownLevel

    ctx = _get_ctx()
    port_repo = ctx["portfolio_handler"]._portfolio_repo
    pos_repo = ctx["portfolio_handler"]._position_repo

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
    ctx = _get_ctx()
    db = ctx["db_factory"]
    from src.signals.infrastructure.duckdb_signal_store import DuckDBSignalStore

    conn = db.duckdb_conn()
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


@app.command()
def approve(
    symbol: str = typer.Argument(..., help="Ticker symbol to approve/reject"),
):
    """Review and approve/reject a pending trade plan."""
    from src.execution.application.commands import ApproveTradePlanCommand, ExecuteOrderCommand

    ctx = _get_ctx()
    handler = ctx["trade_plan_handler"]

    symbol = symbol.upper()
    plan_dict = handler._repo.find_by_symbol(symbol)

    if plan_dict is None or plan_dict.get("status") != "PENDING":
        console.print(f"[bold red]No pending plan for {symbol}.[/bold red]")
        raise typer.Exit(code=1)

    # Display trade plan details
    table = Table(title=f"Trade Plan: {symbol}", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Symbol", plan_dict["symbol"])
    table.add_row("Direction", plan_dict["direction"])
    table.add_row("Entry Price", f"${plan_dict['entry_price']:,.2f}")
    table.add_row("Stop-Loss", f"${plan_dict['stop_loss_price']:,.2f}")
    table.add_row("Take-Profit", f"${plan_dict['take_profit_price']:,.2f}")
    table.add_row("Quantity", str(plan_dict["quantity"]))
    table.add_row("Position Value", f"${plan_dict['position_value']:,.2f}")
    table.add_row("Composite Score", f"{plan_dict.get('composite_score', 0):.1f}")
    mos = plan_dict.get("margin_of_safety", 0)
    table.add_row("Margin of Safety", f"{mos * 100:.1f}%")
    table.add_row("Reasoning", plan_dict.get("reasoning_trace", "-") or "-")

    console.print(table)

    # Ask for approval
    confirmed = typer.confirm("Execute this trade?", default=False)

    if not confirmed:
        handler.approve(ApproveTradePlanCommand(symbol=symbol, approved=False))
        console.print("[yellow]Trade plan rejected.[/yellow]")
        return

    # Ask if user wants to modify parameters
    modify = typer.confirm("Modify quantity or stop-loss?", default=False)
    mod_qty = None
    mod_stop = None
    if modify:
        mod_qty_str = typer.prompt("New quantity", default=str(plan_dict["quantity"]))
        mod_qty = int(mod_qty_str) if mod_qty_str != str(plan_dict["quantity"]) else None
        mod_stop_str = typer.prompt("New stop-loss price", default=str(plan_dict["stop_loss_price"]))
        mod_stop = float(mod_stop_str) if mod_stop_str != str(plan_dict["stop_loss_price"]) else None

    handler.approve(ApproveTradePlanCommand(
        symbol=symbol,
        approved=True,
        modified_quantity=mod_qty,
        modified_stop_loss=mod_stop,
    ))

    # Execute the order
    exec_result = handler.execute(ExecuteOrderCommand(symbol=symbol))

    if exec_result.status in ("filled", "accepted", "partially_filled", "new"):
        console.print(f"[bold green]Order submitted: {exec_result.order_id}[/bold green]")
    else:
        console.print(f"[bold red]Order failed: {exec_result.error_message or exec_result.status}[/bold red]")


@app.command()
def execute(
    symbol: str = typer.Argument(..., help="Ticker symbol to execute"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Execute an approved trade plan as a bracket order."""
    from src.execution.application.commands import ExecuteOrderCommand

    ctx = _get_ctx()
    handler = ctx["trade_plan_handler"]

    symbol = symbol.upper()
    plan_dict = handler._repo.find_by_symbol(symbol)

    if plan_dict is None:
        console.print(f"[bold red]No trade plan found for {symbol}.[/bold red]")
        raise typer.Exit(code=1)

    if plan_dict.get("status") not in ("APPROVED", "MODIFIED"):
        console.print(f"[bold red]Trade plan for {symbol} is not approved (status={plan_dict.get('status')}).[/bold red]")
        raise typer.Exit(code=1)

    if not force:
        console.print(f"[dim]Executing {plan_dict['direction']} {plan_dict['quantity']} {symbol} @ ${plan_dict['entry_price']:,.2f}[/dim]")
        confirmed = typer.confirm("Confirm execution?", default=False)
        if not confirmed:
            console.print("[yellow]Execution cancelled.[/yellow]")
            return

    result = handler.execute(ExecuteOrderCommand(symbol=symbol))

    if result.status in ("filled", "accepted", "partially_filled", "new"):
        console.print(f"[bold green]Order submitted: {result.order_id}[/bold green]")
        if result.filled_price:
            console.print(f"[dim]Filled at ${result.filled_price:,.2f}[/dim]")
    else:
        console.print(f"[bold red]Order failed: {result.error_message or result.status}[/bold red]")


@app.command()
def monitor(
    portfolio_id: str = typer.Option("default", "--portfolio-id", help="Portfolio ID"),
):
    """Monitor positions, alerts, and drawdown status (one-shot check)."""
    from src.portfolio.infrastructure.sqlite_watchlist_repo import SqliteWatchlistRepository
    from src.portfolio.domain.value_objects import DrawdownLevel

    ctx = _get_ctx()
    pos_repo = ctx["portfolio_handler"]._position_repo
    port_repo = ctx["portfolio_handler"]._portfolio_repo
    wl_repo = SqliteWatchlistRepository()

    positions = pos_repo.find_all_open()
    portfolio = port_repo.find_by_id(portfolio_id)
    watchlist = wl_repo.find_all()

    alert_count = 0

    # Check positions for stop conditions
    for pos in positions:
        if pos.atr_stop:
            stop_price = pos.atr_stop.stop_price
            # v1: use entry_price as proxy (real price fetch enhancement planned)
            if pos.entry_price <= stop_price:
                console.print(
                    f"[bold red]STOP ALERT: {pos.symbol} entry ${pos.entry_price:,.2f} "
                    f"<= stop ${stop_price:,.2f}[/bold red]"
                )
                alert_count += 1

    # Check portfolio drawdown
    if portfolio:
        dd_level = portfolio.drawdown_level
        if dd_level != DrawdownLevel.NORMAL:
            dd_pct = portfolio.drawdown * 100
            console.print(
                f"[bold red]DRAWDOWN ALERT: {dd_level.value.upper()} "
                f"({dd_pct:.1f}%)[/bold red]"
            )
            alert_count += 1
    else:
        dd_level = DrawdownLevel.NORMAL

    # Check watchlist price alerts
    for entry in watchlist:
        if entry.alert_above is not None:
            console.print(
                f"[dim]Watchlist alert: {entry.symbol} above ${entry.alert_above:,.2f} (monitoring)[/dim]"
            )
        if entry.alert_below is not None:
            console.print(
                f"[dim]Watchlist alert: {entry.symbol} below ${entry.alert_below:,.2f} (monitoring)[/dim]"
            )

    # Summary panel
    dd_color = {
        DrawdownLevel.NORMAL: "green",
        DrawdownLevel.CAUTION: "yellow",
        DrawdownLevel.WARNING: "red",
        DrawdownLevel.CRITICAL: "bold red",
    }.get(dd_level, "white")

    console.print(Panel(
        f"[bold]{len(positions)}[/bold] positions monitored  |  "
        f"[bold]{alert_count}[/bold] alerts active  |  "
        f"Drawdown: [{dd_color}]{dd_level.value.upper()}[/{dd_color}]",
        title="Monitoring Summary",
        border_style="blue",
    ))


# -- New commands (Plan 05-03) --


@app.command()
def ingest(
    tickers: list[str] = typer.Argument(None, help="Ticker symbols to ingest"),
    universe: str = typer.Option(None, "--universe", "-u", help="Universe name (e.g. sp500)"),
    max_concurrent: int = typer.Option(5, "--concurrent", help="Max concurrent ingestions"),
    regime: bool = typer.Option(False, "--regime", help="Ingest regime data (VIX, S&P 500, yield curve)"),
    market: str = typer.Option("us", "--market", "-m", help="Market (us|kr)"),
):
    """Ingest market data for given tickers or a universe."""
    if regime:
        _ingest_regime(tickers, market)
        return

    if not tickers and not universe:
        console.print("[bold red]Error: Provide ticker symbols or --universe flag.[/bold red]")
        raise typer.Exit(code=1)

    from src.data_ingest.infrastructure.pipeline import DataPipeline
    from src.data_ingest.domain.value_objects import MarketType

    market_type = MarketType.KR if market.lower() == "kr" else MarketType.US

    # Lazy-import PyKRXClient only when needed (Korean market)
    pykrx_client = None
    if market_type == MarketType.KR:
        from src.data_ingest.infrastructure.pykrx_client import PyKRXClient
        pykrx_client = PyKRXClient()

    pipeline = DataPipeline(max_concurrent=max_concurrent, pykrx_client=pykrx_client)

    try:
        if universe:
            console.print(f"[dim]Ingesting universe: {universe}...[/dim]")
            result = asyncio.run(pipeline.ingest_universe(market=market_type))
        else:
            console.print(f"[dim]Ingesting {len(tickers)} tickers...[/dim]")
            result = asyncio.run(pipeline.ingest_universe(tickers, market=market_type))

        # Display results
        table = Table(title="Ingestion Results", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total", str(result["total"]))
        table.add_row("Succeeded", f"[green]{result['succeeded_count']}[/green]")
        table.add_row("Failed", f"[yellow]{result['failed_count']}[/yellow]")
        table.add_row("Errors", f"[red]{result['errors_count']}[/red]")

        console.print(table)
    finally:
        asyncio.run(pipeline.close())


def _ingest_regime(tickers: list[str] | None, market: str) -> None:
    """Handle regime data ingestion flow."""
    if market.lower() == "kr":
        console.print("[bold red]Error: Regime data is US-market-only. Cannot use --regime with --market kr.[/bold red]")
        raise typer.Exit(code=1)

    if tickers:
        console.print("[bold red]Error: --regime does not accept ticker symbols. Regime data has no per-ticker granularity.[/bold red]")
        raise typer.Exit(code=1)

    from src.data_ingest.infrastructure.regime_data_client import RegimeDataClient
    from src.data_ingest.infrastructure.duckdb_store import DuckDBStore

    console.print("[dim]Ingesting regime data (VIX, S&P 500, yield curve)...[/dim]")

    client = RegimeDataClient()
    df = client.fetch_regime_history(years=2)

    store = DuckDBStore()
    store.connect()
    try:
        store.store_regime_data(df)
    finally:
        store.close()

    # Display results
    table = Table(title="Regime Data Ingestion", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Rows Stored", f"[green]{len(df)}[/green]")
    table.add_row("Date Range", f"{df['date'].min()} to {df['date'].max()}")
    table.add_row("Columns", ", ".join(c for c in df.columns if c != "date"))

    console.print(table)


def _fetch_ohlcv_for_backtest(symbol: str, start: str, end: str):
    """Fetch OHLCV data and generate signals for backtesting.

    Returns (ohlcv_df, signals_series) tuple.
    """
    from core.data.client import DataClient
    import pandas as pd

    client = DataClient()
    data = client.get_full(symbol)

    # Build a simple OHLCV DataFrame from the data client
    price = data.get("price", {})
    ohlcv_df = pd.DataFrame({
        "open": [price.get("open", 100.0)],
        "high": [price.get("high", 101.0)],
        "low": [price.get("low", 99.0)],
        "close": [price.get("close", 100.0)],
        "volume": [price.get("volume", 1_000_000)],
    })

    # Generate a simple signal series
    signals_series = pd.Series([1])

    return ohlcv_df, signals_series


@app.command(name="generate-plan")
def generate_plan(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    capital: float = typer.Option(100000.0, "--capital", "-c", help="Portfolio capital"),
    strategy: str = typer.Option("swing", "--strategy", "-s", help="swing|position"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Generate a trade plan for a symbol."""
    from src.bootstrap import bootstrap
    from src.execution.application.commands import GenerateTradePlanCommand

    ctx = bootstrap()
    handler = ctx["trade_plan_handler"]

    symbol = symbol.upper()
    console.print(f"[dim]Generating trade plan for {symbol}...[/dim]")

    cmd = GenerateTradePlanCommand(
        symbol=symbol,
        entry_price=100.0,  # placeholder -- real price from data client
        atr=3.0,
        capital=capital,
        peak_value=capital,
        current_value=capital,
        intrinsic_value=120.0,
        composite_score=70.0,
        margin_of_safety=0.15,
        signal_direction="BUY",
        reasoning_trace=f"Generated via CLI for {symbol}",
    )

    plan = handler.generate(cmd)

    if plan is None:
        console.print(f"[yellow]Trade plan for {symbol} rejected by risk gates.[/yellow]")
        return

    if output == "json":
        plan_dict = {
            "symbol": plan.symbol,
            "direction": plan.direction,
            "entry_price": plan.entry_price,
            "stop_loss_price": plan.stop_loss_price,
            "take_profit_price": plan.take_profit_price,
            "quantity": plan.quantity,
            "position_value": plan.position_value,
            "composite_score": plan.composite_score,
            "margin_of_safety": plan.margin_of_safety,
            "reasoning_trace": plan.reasoning_trace,
        }
        console.print_json(json.dumps(plan_dict, default=str))
        return

    table = Table(title=f"Trade Plan: {symbol}", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Symbol", plan.symbol)
    table.add_row("Direction", plan.direction)
    table.add_row("Entry Price", f"${plan.entry_price:,.2f}")
    table.add_row("Stop-Loss", f"${plan.stop_loss_price:,.2f}")
    table.add_row("Take-Profit", f"${plan.take_profit_price:,.2f}")
    table.add_row("Quantity", str(plan.quantity))
    table.add_row("Position Value", f"${plan.position_value:,.2f}")
    table.add_row("Composite Score", f"{plan.composite_score:.1f}")
    table.add_row("Margin of Safety", f"{plan.margin_of_safety * 100:.1f}%")
    table.add_row("Reasoning", plan.reasoning_trace or "-")

    console.print(table)


@app.command()
def backtest(
    symbol: str = typer.Argument(..., help="Ticker symbol"),
    start: str = typer.Option("2020-01-01", "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("2024-12-31", "--end", help="End date (YYYY-MM-DD)"),
    strategy: str = typer.Option("swing", "--strategy", "-s", help="swing|position"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """Run backtest for a symbol over a date range."""
    from src.backtest.application.handlers import BacktestHandler
    from src.backtest.application.commands import RunBacktestCommand
    from src.backtest.domain.services import BacktestValidationService
    from src.backtest.infrastructure.core_backtest_adapter import CoreBacktestAdapter

    symbol = symbol.upper()
    console.print(f"[dim]Running backtest for {symbol} ({start} to {end})...[/dim]")

    try:
        ohlcv_df, signals_series = _fetch_ohlcv_for_backtest(symbol, start, end)
    except Exception as e:
        console.print(f"[bold red]Error fetching data: {e}[/bold red]")
        raise typer.Exit(code=1)

    adapter = CoreBacktestAdapter()
    validation_svc = BacktestValidationService()
    handler = BacktestHandler(adapter=adapter, validation_svc=validation_svc)

    cmd = RunBacktestCommand(
        symbol=symbol,
        ohlcv_df=ohlcv_df,
        signals_series=signals_series,
    )

    result = handler.run_backtest(cmd)

    if not result.is_ok:
        console.print(f"[bold red]Backtest failed: {result.error}[/bold red]")
        raise typer.Exit(code=1)

    report = result.value["performance_report"]

    if output == "json":
        console.print_json(json.dumps({"symbol": symbol, **report}, default=str))
        return

    table = Table(title=f"Backtest: {symbol}", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Symbol", symbol)
    table.add_row("Period", f"{start} to {end}")
    table.add_row("Total Return", f"{report.get('total_return', 0):.1%}")
    table.add_row("Sharpe Ratio", f"{report.get('sharpe_ratio', 0):.2f}")
    table.add_row("Max Drawdown", f"{report.get('max_drawdown', 0):.1%}")
    table.add_row("Win Rate", f"{report.get('win_rate', 0):.1%}")
    table.add_row("Profit Factor", f"{report.get('profit_factor', 0):.2f}")

    console.print(table)


if __name__ == "__main__":
    app()
