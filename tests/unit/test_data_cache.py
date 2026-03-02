"""Unit tests for core/data/cache.py"""
import time
import pytest
from core.data import cache as c


def test_set_and_get():
    c.set("test:key", {"value": 42}, ttl=60)
    result = c.get("test:key")
    assert result == {"value": 42}


def test_expired_key_returns_none():
    c.set("test:expire", "data", ttl=1)
    time.sleep(1.1)
    assert c.get("test:expire") is None


def test_missing_key_returns_none():
    assert c.get("test:nonexistent_xyz") is None


def test_delete():
    c.set("test:delete_me", 123, ttl=60)
    c.delete("test:delete_me")
    assert c.get("test:delete_me") is None


def test_purge_expired():
    c.set("test:purge1", "a", ttl=1)
    c.set("test:purge2", "b", ttl=60)
    time.sleep(1.1)
    removed = c.purge_expired()
    assert removed >= 1
    assert c.get("test:purge2") == "b"
