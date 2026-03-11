"""Unit tests for PaperTradingClient mock mode."""
import pytest
from unittest.mock import patch

from personal.execution.paper_trading import PaperTradingClient, Order, Position


@pytest.fixture
def client():
    """Return a PaperTradingClient in mock mode (no env credentials)."""
    with patch.dict("os.environ", {}, clear=True):
        return PaperTradingClient()


# --- Test 1 ---


def test_mock_mode_when_no_credentials(client):
    """API key not set -> client operates in mock mode."""
    assert client._use_mock is True


# --- Test 2 ---


def test_submit_buy_order(client):
    """Buy order submitted in mock mode -> status 'filled'."""
    order = client.submit_order("AAPL", 10, "buy")

    assert isinstance(order, Order)
    assert order.symbol == "AAPL"
    assert order.qty == 10
    assert order.side == "buy"
    assert order.status == "filled"
    assert order.filled_price is not None
    assert order.order_id.startswith("MOCK-AAPL-buy-")


# --- Test 3 ---


def test_submit_sell_order(client):
    """Sell order submitted in mock mode -> status 'filled'."""
    # Buy first so there is a position to sell
    client.submit_order("MSFT", 5, "buy")
    order = client.submit_order("MSFT", 3, "sell")

    assert isinstance(order, Order)
    assert order.symbol == "MSFT"
    assert order.side == "sell"
    assert order.status == "filled"


# --- Test 4 ---


def test_get_positions_empty_initially(client):
    """No orders placed -> positions list is empty."""
    positions = client.get_positions()
    assert positions == []


# --- Test 5 ---


def test_position_added_after_buy(client):
    """After a buy, get_positions returns the new position."""
    client.submit_order("AAPL", 10, "buy")

    positions = client.get_positions()
    assert len(positions) == 1

    pos = positions[0]
    assert isinstance(pos, Position)
    assert pos.symbol == "AAPL"
    assert pos.qty == 10
    assert pos.avg_entry_price > 0


# --- Test 6 ---


def test_cancel_order(client):
    """cancel_order sets status to 'cancelled'."""
    order = client.submit_order("GOOG", 2, "buy")
    result = client.cancel_order(order.order_id)

    assert result is True
    assert client._mock_orders[order.order_id].status == "cancelled"


# --- Test 7 ---


def test_get_portfolio_value(client):
    """After a buy, portfolio value includes position market value."""
    initial_value = client.get_portfolio_value()
    assert initial_value == 100_000.0

    client.submit_order("AAPL", 10, "buy")
    value_after = client.get_portfolio_value()

    # Cash decreased but position adds market value, so total > 0
    assert value_after > 0
    # With 1% mock gain, total should exceed initial cash minus cost plus market value
    assert value_after != initial_value


# --- Test 8 ---


def test_get_account_keys(client):
    """get_account returns dict with required keys."""
    account = client.get_account()

    assert "cash" in account
    assert "portfolio_value" in account
    assert "status" in account
    assert account["status"] == "ACTIVE"
    assert isinstance(account["cash"], float)
    assert isinstance(account["portfolio_value"], float)
