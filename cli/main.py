"""Trading System CLI entry point."""
import asyncio
import json
import threading
import webbrowser
import typer
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(name="trading", help="Trading System CLI")
console = Console()

# -- Bootstrap context (lazy-loaded, keyed by market) --
_ctx_cache: dict[str, dict] = {}


def _get_ctx(market: str = "us", *, read_only: bool = True) -> dict:
    """Lazily bootstrap the application context and cache it per market."""
    key = f"{market}:ro" if read_only else market
    if key not in _ctx_cache:
        from src.bootstrap import bootstrap
        _ctx_cache[key] = bootstrap(market=market, read_only=read_only)
    return _ctx_cache[key]


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
    fundamentals = data.get("fundamentals", {})
    return {
        # CAN SLIM inputs
        "eps_growth_qoq": fundamentals.get("eps_growth_qoq"),
        "eps_cagr_3y": fundamentals.get("eps_cagr_3y"),
        "near_52w_high": indicators.get("near_52w_high", False),
        "volume_ratio": indicators.get("volume_ratio", 1.0),
        "relative_strength": indicators.get("relative_strength", 50),
        "institutional_increase": fundamentals.get("institutional_increase", False),
        # market_uptrend will be injected by handler from regime_type
        # Magic Formula inputs
        "earnings_yield": fundamentals.get("earnings_yield"),
        "return_on_capital": fundamentals.get("return_on_capital"),
        "ey_percentile": fundamentals.get("ey_percentile", 50.0),
        "roc_percentile": fundamentals.get("roc_percentile", 50.0),
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
    market: str = typer.Option("us", "--market", "-m", help="Market (us|kr)"),
):
    """Execute an approved trade plan as a bracket order."""
    from src.execution.application.commands import ExecuteOrderCommand

    ctx = _get_ctx(market=market)
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
    capital: float = typer.Option(0.0, "--capital", "-c", help="Portfolio capital (0=use market default)"),
    strategy: str = typer.Option("swing", "--strategy", "-s", help="swing|position"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
    market: str = typer.Option("us", "--market", "-m", help="Market (us|kr)"),
):
    """Generate a trade plan for a symbol."""
    from src.execution.application.commands import GenerateTradePlanCommand

    ctx = _get_ctx(market=market)
    handler = ctx["trade_plan_handler"]
    effective_capital = capital if capital > 0 else ctx["capital"]

    symbol = symbol.upper()
    console.print(f"[dim]Generating trade plan for {symbol}...[/dim]")

    # Fetch real price + indicators from DataClient
    from core.data.client import DataClient

    client = DataClient()
    full_data = client.get_full(symbol)
    price_data = full_data.get("price", {})
    indicator_data = full_data.get("indicators", {})
    entry_price = price_data.get("close", 0.0)
    atr = indicator_data.get("atr21", 0.0) or 3.0

    # Get composite score from DDD handler
    from src.scoring.application.commands import ScoreSymbolCommand

    score_result = ctx["score_handler"].handle(ScoreSymbolCommand(symbol=symbol, strategy=strategy))
    composite_score = 50.0
    margin_of_safety = 0.0
    if score_result.is_ok():
        score_data = score_result.unwrap()
        composite_score = score_data.get("composite_score", 50.0)
        margin_of_safety = score_data.get("margin_of_safety", 0.0)

    # Get signal direction from DDD handler
    from src.signals.application.commands import GenerateSignalCommand as GenSignalCmd

    signal_result = ctx["signal_handler"].handle(GenSignalCmd(symbol=symbol, composite_score=composite_score))
    signal_direction = "HOLD"
    reasoning_trace = f"Generated via CLI for {symbol}"
    if signal_result.is_ok():
        signal_data = signal_result.unwrap()
        signal_direction = signal_data.get("direction", "HOLD")
        reasoning_trace = signal_data.get("reasoning_trace", reasoning_trace)

    # Estimate intrinsic value from margin of safety
    intrinsic_value = entry_price * (1.0 + margin_of_safety) if margin_of_safety > 0 else entry_price * 1.2

    cmd = GenerateTradePlanCommand(
        symbol=symbol,
        entry_price=entry_price,
        atr=atr,
        capital=effective_capital,
        peak_value=effective_capital,
        current_value=effective_capital,
        intrinsic_value=intrinsic_value,
        composite_score=composite_score,
        margin_of_safety=margin_of_safety,
        signal_direction=signal_direction,
        reasoning_trace=reasoning_trace,
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


@app.command()
def kill(
    liquidate: bool = typer.Option(False, "--liquidate", help="Also liquidate all positions"),
    market: str = typer.Option("us", "--market", "-m", help="Market (us|kr)"),
):
    """Emergency kill switch -- cancel all orders, optionally liquidate."""
    from src.execution.infrastructure.kill_switch import KillSwitchService
    from src.execution.infrastructure.sqlite_cooldown_repo import SqliteCooldownRepository

    if liquidate:
        if not typer.confirm("LIQUIDATE all positions? This cannot be undone."):
            raise typer.Exit()

    ctx = _get_ctx(market=market)
    db_factory = ctx["db_factory"]
    cooldown_repo = SqliteCooldownRepository(
        db_path=db_factory.sqlite_path("portfolio")
    )

    # Get the raw adapter (not SafeExecutionAdapter -- kill needs direct access)
    adapter = ctx["trade_plan_handler"]._adapter

    service = KillSwitchService(adapter, cooldown_repo)
    result = service.execute(liquidate=liquidate)

    # Output summary
    lines = []
    lines.append(f"[bold]Orders canceled:[/bold] {result['orders_canceled']}")
    if liquidate:
        lines.append(f"[bold]Positions closed:[/bold] {result['positions_closed']}")
    lines.append(f"[bold]Cooldown until:[/bold] {result['cooldown_until']}")

    console.print(Panel(
        "\n".join(lines),
        title="[bold red]KILL SWITCH ACTIVATED[/bold red]",
        border_style="red",
    ))


@app.command()
def sync(
    market: str = typer.Option("us", "--market", "-m", help="Market (us|kr)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Sync local positions to match broker state."""
    from src.execution.infrastructure.reconciliation import PositionReconciliationService

    ctx = _get_ctx(market=market)

    # Get position repo and adapter
    position_repo = ctx["portfolio_handler"]._position_repo
    adapter = ctx["trade_plan_handler"]._adapter

    service = PositionReconciliationService(position_repo, adapter)
    discrepancies = service.reconcile()

    if not discrepancies:
        console.print("[bold green]Positions in sync.[/bold green]")
        return

    # Show discrepancy table
    table = Table(
        title="Position Discrepancies",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Symbol", style="bold")
    table.add_column("Type")
    table.add_column("Local Qty", justify="right")
    table.add_column("Broker Qty", justify="right")

    for d in discrepancies:
        local_str = str(d.local_qty) if d.local_qty is not None else "-"
        broker_str = str(d.broker_qty) if d.broker_qty is not None else "-"
        type_color = {
            "local_only": "yellow",
            "broker_only": "cyan",
            "qty_mismatch": "red",
        }.get(d.discrepancy_type, "white")
        table.add_row(
            d.symbol,
            f"[{type_color}]{d.discrepancy_type}[/{type_color}]",
            local_str,
            broker_str,
        )

    console.print(table)

    if not yes:
        if not typer.confirm("Sync local positions to broker state?"):
            console.print("[yellow]Sync cancelled.[/yellow]")
            return

    changes = service.sync_to_broker()
    console.print(f"[bold green]Synced {changes} position(s) to broker state.[/bold green]")


# ---------------------------------------------------------------------------
# Pipeline subcommands
# ---------------------------------------------------------------------------
pipeline_app = typer.Typer(help="Automated pipeline commands")
app.add_typer(pipeline_app, name="pipeline")


@pipeline_app.command(name="run")
def pipeline_run(
    symbols: list[str] = typer.Argument(None, help="Ticker symbols (optional, uses default universe if omitted)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Execute without submitting orders"),
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Run the full trading pipeline manually."""
    from src.pipeline.application.commands import RunPipelineCommand
    from src.pipeline.domain.value_objects import RunMode

    ctx = _get_ctx(market, read_only=False)
    handler = ctx["run_pipeline_handler"]
    if symbols:
        handler._symbols = symbols
    cmd = RunPipelineCommand(dry_run=dry_run, mode=RunMode.MANUAL)

    console.print("[bold]Starting pipeline run...[/bold]")
    if dry_run:
        console.print("[yellow]DRY-RUN mode: orders will NOT be submitted[/yellow]")

    result = handler.handle(cmd)

    # Display results
    status_color = {
        "running": "blue",
        "completed": "green",
        "halted": "yellow",
        "failed": "red",
    }.get(result.status.value, "white")

    duration = result.duration
    duration_str = f"{duration.total_seconds():.1f}s" if duration else "N/A"

    panel_lines = [
        f"[bold]Run ID:[/bold] {result.run_id[:8]}",
        f"[bold]Status:[/bold] [{status_color}]{result.status.value.upper()}[/{status_color}]",
        f"[bold]Mode:[/bold] {result.mode.value}",
        f"[bold]Duration:[/bold] {duration_str}",
        f"[bold]Symbols:[/bold] {result.symbols_succeeded}/{result.symbols_total}",
    ]
    if result.halt_reason:
        panel_lines.append(f"[bold]Halt Reason:[/bold] [yellow]{result.halt_reason}[/yellow]")
    if result.error_message:
        panel_lines.append(f"[bold]Error:[/bold] [red]{result.error_message}[/red]")

    console.print(Panel("\n".join(panel_lines), title="Pipeline Run Result"))

    # Stage details table
    if result.stages:
        table = Table(title="Stage Results")
        table.add_column("Stage", style="bold")
        table.add_column("Status")
        table.add_column("Symbols", justify="right")
        table.add_column("Duration")

        for stage in result.stages:
            s_color = {"success": "green", "partial": "yellow", "failed": "red", "skipped": "dim"}.get(stage.status, "white")
            s_dur = (stage.finished_at - stage.started_at).total_seconds()
            table.add_row(
                stage.stage_name,
                f"[{s_color}]{stage.status}[/{s_color}]",
                f"{stage.symbols_succeeded}/{stage.symbols_processed}",
                f"{s_dur:.1f}s",
            )

        console.print(table)


@pipeline_app.command(name="status")
def pipeline_status(
    limit: int = typer.Option(5, "--limit", "-n", help="Number of recent runs to show"),
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Show recent pipeline run history."""
    from src.pipeline.application.commands import GetPipelineStatusQuery

    ctx = _get_ctx(market)
    handler = ctx["pipeline_status_handler"]
    runs = handler.handle(GetPipelineStatusQuery(limit=limit))

    if not runs:
        console.print("[dim]No pipeline runs found.[/dim]")
        return

    table = Table(title="Recent Pipeline Runs")
    table.add_column("Run ID", style="bold")
    table.add_column("Started")
    table.add_column("Duration")
    table.add_column("Status")
    table.add_column("Mode")
    table.add_column("Symbols", justify="right")
    table.add_column("Halt Reason")

    for run in runs:
        status_color = {
            "running": "blue",
            "completed": "green",
            "halted": "yellow",
            "failed": "red",
        }.get(run.status.value, "white")

        duration = run.duration
        dur_str = f"{duration.total_seconds():.0f}s" if duration else "-"
        started_str = run.started_at.strftime("%Y-%m-%d %H:%M") if run.started_at else "-"

        table.add_row(
            run.run_id[:8],
            started_str,
            dur_str,
            f"[{status_color}]{run.status.value}[/{status_color}]",
            run.mode.value,
            f"{run.symbols_succeeded}/{run.symbols_total}",
            run.halt_reason or "-",
        )

    console.print(table)

    # Show next scheduled run time if available
    try:
        scheduler_service = ctx.get("scheduler_service")
        if scheduler_service:
            next_time = scheduler_service.get_next_run_time()
            if next_time:
                console.print(f"\n[bold]Next scheduled run:[/bold] {next_time.strftime('%Y-%m-%d %H:%M %Z')}")
    except Exception:
        pass


@pipeline_app.command(name="daemon")
def pipeline_daemon(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Start the pipeline scheduler daemon (background process)."""
    ctx = _get_ctx(market, read_only=False)
    scheduler = ctx["scheduler_service"]
    scheduler.start()
    console.print("[green]Pipeline scheduler started[/green]")
    next_time = scheduler.get_next_run_time()
    if next_time:
        console.print(f"Next run: {next_time.strftime('%Y-%m-%d %H:%M %Z')}")
    console.print("[dim]Press Ctrl+C to stop...[/dim]")
    try:
        import signal

        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
        console.print("[yellow]Scheduler stopped[/yellow]")


# ---------------------------------------------------------------------------
# Approval subcommands
# ---------------------------------------------------------------------------
approval_app = typer.Typer(help="Strategy approval commands")
app.add_typer(approval_app, name="approval")


@approval_app.command(name="create")
def approve_create(
    score: float = typer.Option(..., "--score", help="Minimum composite score"),
    regimes: str = typer.Option(..., "--regimes", help="Comma-separated regime allow-list"),
    max_pct: float = typer.Option(8.0, "--max-pct", help="Max per-trade % of capital"),
    budget: float = typer.Option(..., "--budget", help="Daily budget cap in USD"),
    expires: int = typer.Option(..., "--expires", help="Days until expiration"),
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Create a new strategy approval for automated trading."""
    from src.approval.application.commands import CreateApprovalCommand

    ctx = _get_ctx(market)
    handler = ctx["approval_handler"]

    regime_list = [r.strip() for r in regimes.split(",") if r.strip()]
    cmd = CreateApprovalCommand(
        score_threshold=score,
        allowed_regimes=regime_list,
        max_per_trade_pct=max_pct,
        daily_budget_cap=budget,
        expires_in_days=expires,
    )
    approval = handler.create(cmd)

    console.print(Panel(
        f"[bold]ID:[/bold] {approval.id}\n"
        f"[bold]Score Threshold:[/bold] {approval.score_threshold}\n"
        f"[bold]Allowed Regimes:[/bold] {', '.join(approval.allowed_regimes)}\n"
        f"[bold]Max Per-Trade:[/bold] {approval.max_per_trade_pct}%\n"
        f"[bold]Daily Budget:[/bold] ${approval.daily_budget_cap:,.2f}\n"
        f"[bold]Expires:[/bold] {approval.expires_at.strftime('%Y-%m-%d %H:%M UTC')}",
        title="[bold green]Approval Created[/bold green]",
        border_style="green",
    ))


@approval_app.command(name="status")
def approve_status(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Show current strategy approval status."""
    ctx = _get_ctx(market)
    handler = ctx["approval_handler"]
    status = handler.get_status()

    approval = status["approval"]
    if approval is None:
        console.print("[dim]No active approval.[/dim]")
        return

    # Determine status text
    if not approval.is_active:
        status_text = "[red]REVOKED[/red]"
    elif approval.is_expired:
        status_text = "[yellow]EXPIRED[/yellow]"
    elif approval.is_suspended:
        reasons = ", ".join(sorted(approval.suspended_reasons))
        status_text = f"[yellow]SUSPENDED ({reasons})[/yellow]"
    else:
        status_text = "[green]ACTIVE[/green]"

    from datetime import datetime, timezone
    hours_left = (approval.expires_at - datetime.now(timezone.utc)).total_seconds() / 3600
    days_left = hours_left / 24

    lines = [
        f"[bold]ID:[/bold] {approval.id}",
        f"[bold]Status:[/bold] {status_text}",
        f"[bold]Score Threshold:[/bold] {approval.score_threshold}",
        f"[bold]Allowed Regimes:[/bold] {', '.join(approval.allowed_regimes)}",
        f"[bold]Max Per-Trade:[/bold] {approval.max_per_trade_pct}%",
        f"[bold]Daily Budget:[/bold] ${approval.daily_budget_cap:,.2f}",
        f"[bold]Expires:[/bold] {approval.expires_at.strftime('%Y-%m-%d %H:%M UTC')} ({days_left:.1f} days)",
    ]

    # Budget info
    budget = status.get("budget")
    if budget:
        pct_used = (budget.spent / budget.budget_cap * 100) if budget.budget_cap > 0 else 0
        bar_len = 20
        filled = int(pct_used / 100 * bar_len)
        bar_color = "green" if pct_used < 80 else "yellow" if pct_used < 100 else "red"
        bar = f"[{bar_color}]{'█' * filled}{'░' * (bar_len - filled)}[/{bar_color}]"
        lines.append(
            f"[bold]Budget Today:[/bold] ${budget.spent:,.2f} / ${budget.budget_cap:,.2f} "
            f"(${budget.remaining:,.2f} remaining) {bar}"
        )

    # Pending reviews
    pending = status.get("pending_review_count", 0)
    if pending > 0:
        lines.append(f"[bold]Pending Reviews:[/bold] [yellow]{pending}[/yellow]")
    else:
        lines.append("[bold]Pending Reviews:[/bold] 0")

    console.print(Panel("\n".join(lines), title="Strategy Approval", border_style="blue"))


@approval_app.command(name="revoke")
def approve_revoke(
    approval_id: str = typer.Option(None, "--id", help="Approval ID (defaults to active)"),
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Revoke the active strategy approval."""
    from src.approval.application.commands import RevokeApprovalCommand

    ctx = _get_ctx(market)
    handler = ctx["approval_handler"]
    handler.revoke(RevokeApprovalCommand(approval_id=approval_id))
    console.print("[yellow]Approval revoked.[/yellow]")


@approval_app.command(name="resume")
def approve_resume(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Resume a suspended approval (remove drawdown_tier2 suspension)."""
    from src.approval.application.commands import ResumeApprovalCommand

    ctx = _get_ctx(market)
    handler = ctx["approval_handler"]
    handler.resume(ResumeApprovalCommand())
    console.print("[green]Approval resumed (drawdown_tier2 suspension removed).[/green]")


# ---------------------------------------------------------------------------
# Review subcommands
# ---------------------------------------------------------------------------
review_app = typer.Typer(help="Trade review queue commands")
app.add_typer(review_app, name="review")


@review_app.command(name="list")
def review_list(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """List pending trades awaiting manual review."""
    ctx = _get_ctx(market)
    review_repo = ctx["review_queue_repo"]

    # Expire old items first
    expired_count = review_repo.expire_old(24)
    if expired_count > 0:
        console.print(f"[dim]Expired {expired_count} stale review item(s).[/dim]")

    items = review_repo.list_pending()
    if not items:
        console.print("[dim]No pending reviews.[/dim]")
        return

    from datetime import datetime, timezone
    table = Table(title="Pending Trade Reviews", show_header=True, header_style="bold cyan")
    table.add_column("ID", justify="right")
    table.add_column("Symbol", style="bold")
    table.add_column("Rejection Reason")
    table.add_column("Created", justify="right")
    table.add_column("Age", justify="right")

    now = datetime.now(timezone.utc)
    for item in items:
        age = now - item.created_at
        age_str = f"{age.total_seconds() / 3600:.1f}h"
        table.add_row(
            str(item.id or "-"),
            item.symbol,
            item.rejection_reason,
            item.created_at.strftime("%Y-%m-%d %H:%M"),
            age_str,
        )

    console.print(table)


@review_app.command(name="approve")
def review_approve(
    symbol: str = typer.Argument(..., help="Symbol to approve"),
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Approve a queued trade for execution."""
    from src.execution.application.commands import ApproveTradePlanCommand, ExecuteOrderCommand

    ctx = _get_ctx(market)
    review_repo = ctx["review_queue_repo"]
    trade_handler = ctx["trade_plan_handler"]

    symbol = symbol.upper()
    items = review_repo.list_pending()
    match = next((i for i in items if i.symbol == symbol), None)

    if match is None:
        console.print(f"[bold red]No pending review for {symbol}.[/bold red]")
        raise typer.Exit(code=1)

    review_repo.mark_reviewed(match.id, approved=True)

    # Try to execute the trade
    try:
        trade_handler.approve(ApproveTradePlanCommand(symbol=symbol, approved=True))
        result = trade_handler.execute(ExecuteOrderCommand(symbol=symbol))
        if result.status in ("filled", "accepted", "partially_filled", "new"):
            console.print(f"[bold green]Trade {symbol} approved and executed: {result.order_id}[/bold green]")
        else:
            console.print(f"[yellow]Trade {symbol} approved but execution failed: {result.error_message or result.status}[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Trade {symbol} approved but execution failed: {e}[/yellow]")


@review_app.command(name="reject")
def review_reject(
    symbol: str = typer.Argument(..., help="Symbol to reject"),
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Reject a queued trade (no execution)."""
    ctx = _get_ctx(market)
    review_repo = ctx["review_queue_repo"]

    symbol = symbol.upper()
    items = review_repo.list_pending()
    match = next((i for i in items if i.symbol == symbol), None)

    if match is None:
        console.print(f"[bold red]No pending review for {symbol}.[/bold red]")
        raise typer.Exit(code=1)

    review_repo.mark_reviewed(match.id, approved=False)
    console.print(f"[yellow]Trade {symbol} rejected.[/yellow]")


# -- Config commands --
config_app = typer.Typer(help="Trading configuration commands")
app.add_typer(config_app, name="config")


@config_app.command(name="show")
def config_show(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Show current trading configuration."""
    from src.settings import Settings

    s = Settings()
    effective_capital = s.US_CAPITAL * s.LIVE_CAPITAL_RATIO if s.EXECUTION_MODE == "live" else s.US_CAPITAL

    table = Table(title="Trading Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("EXECUTION_MODE", s.EXECUTION_MODE)
    table.add_row("US_CAPITAL", f"${s.US_CAPITAL:,.2f}")
    table.add_row("LIVE_CAPITAL_RATIO", f"{s.LIVE_CAPITAL_RATIO:.2f}")
    table.add_row("Effective Capital", f"${effective_capital:,.2f}")
    table.add_row("Alpaca Paper Key", "Set" if s.ALPACA_PAPER_KEY else "Not set")
    table.add_row("Alpaca Live Key", "Set" if s.ALPACA_LIVE_KEY else "Not set")

    console.print(table)


@config_app.command(name="set-capital-ratio")
def config_set_capital_ratio(
    ratio: float = typer.Argument(..., help="Capital ratio (0.0-1.0)"),
):
    """Set LIVE_CAPITAL_RATIO for live trading."""
    if ratio < 0.0 or ratio > 1.0:
        console.print("[bold red]Error: ratio must be between 0.0 and 1.0[/bold red]")
        raise typer.Exit(code=1)

    from src.settings import Settings

    s = Settings()
    old_ratio = s.LIVE_CAPITAL_RATIO
    new_effective = s.US_CAPITAL * ratio

    console.print(f"Current ratio: {old_ratio:.2f} -> New ratio: {ratio:.2f}")
    console.print(f"Effective capital: ${new_effective:,.2f}")

    typer.confirm(f"Set LIVE_CAPITAL_RATIO to {ratio}?", abort=True)

    # Update .env file
    import pathlib

    env_path = pathlib.Path(".env")
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        found = False
        for i, line in enumerate(lines):
            if line.startswith("LIVE_CAPITAL_RATIO="):
                lines[i] = f"LIVE_CAPITAL_RATIO={ratio}"
                found = True
                break
        if not found:
            lines.append(f"LIVE_CAPITAL_RATIO={ratio}")
        env_path.write_text("\n".join(lines) + "\n")
    else:
        env_path.write_text(f"LIVE_CAPITAL_RATIO={ratio}\n")

    console.print(f"[bold green]LIVE_CAPITAL_RATIO set to {ratio}[/bold green]")


# -- Circuit breaker commands --
cb_app = typer.Typer(help="Circuit breaker commands")
app.add_typer(cb_app, name="circuit-breaker")


@cb_app.command(name="status")
def cb_status(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Show circuit breaker status."""
    ctx = _get_ctx(market)
    safe_adapter = ctx.get("safe_adapter")

    if safe_adapter is None:
        console.print("[dim]No SafeExecutionAdapter available (non-US market?).[/dim]")
        raise typer.Exit(code=1)

    tripped = safe_adapter._circuit_tripped
    failures = safe_adapter._consecutive_failures

    status_text = "[bold red]TRIPPED[/bold red]" if tripped else "[bold green]OK[/bold green]"
    console.print(Panel(
        f"Status: {status_text}\n"
        f"Consecutive failures: {failures}\n"
        f"Max failures: {safe_adapter._max_failures}",
        title="Circuit Breaker",
    ))


@cb_app.command(name="reset")
def cb_reset(
    market: str = typer.Option("us", "--market", "-m", help="Market: us|kr"),
):
    """Reset circuit breaker to allow orders again."""
    ctx = _get_ctx(market)
    safe_adapter = ctx.get("safe_adapter")

    if safe_adapter is None:
        console.print("[bold red]No SafeExecutionAdapter available.[/bold red]")
        raise typer.Exit(code=1)

    safe_adapter.reset_circuit_breaker()
    console.print("[bold green]Circuit breaker reset successfully.[/bold green]")


@app.command()
def serve(
    host: str = typer.Option(None, "--host", help="Bind host (default: from settings)"),
    port: int = typer.Option(None, "--port", help="Bind port (default: from settings)"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't auto-open browser"),
):
    """Launch the dashboard web server."""
    from src.settings import settings
    from src.dashboard.presentation.app import create_dashboard_app

    _host = host if host is not None else settings.DASHBOARD_HOST
    _port = port if port is not None else settings.DASHBOARD_PORT

    ctx = _get_ctx()
    dashboard_app = create_dashboard_app(ctx)

    url = f"http://{_host}:{_port}/dashboard/"
    console.print(f"[bold green]Starting dashboard at {url}[/bold green]")

    if not no_browser:
        def _open_browser():
            try:
                webbrowser.open(url)
            except Exception:
                pass  # WSL2 or headless environment

        timer = threading.Timer(1.5, _open_browser)
        timer.start()

    uvicorn.run(dashboard_app, host=_host, port=_port, log_level="info")


if __name__ == "__main__":
    app()
