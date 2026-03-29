"""Panops Sample App - Generates test errors for integration testing."""

import os
import logging
import random
import time

import sentry_sdk
from fastapi import FastAPI, HTTPException

SENTRY_DSN = os.getenv("SENTRY_DSN", "")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        environment="development",
    )

app = FastAPI(title="Panops Sample App")
logger = logging.getLogger(__name__)


def get_user_email(user_id: int) -> str:
    """Simulate fetching a user - returns None for odd IDs."""
    users = {2: "alice@example.com", 4: "bob@example.com"}
    return users.get(user_id)


def calculate_discount(price: float, discount_pct: float) -> float:
    """Calculate discounted price - division by zero when discount is 100."""
    return price / (1 - discount_pct / 100)


def process_order(items: list[dict]) -> dict:
    """Process an order - KeyError when item missing 'price'."""
    total = sum(item["price"] * item["quantity"] for item in items)
    return {"total": total, "item_count": len(items)}


def parse_config(config_str: str) -> dict:
    """Parse a config string - raises ValueError on bad format."""
    parts = config_str.split("=")
    if len(parts) != 2:
        raise ValueError(f"Invalid config format: expected 'key=value', got '{config_str}'")
    return {"key": parts[0], "value": parts[1]}


def connect_to_service(host: str, port: int) -> dict:
    """Simulate connecting to a service - raises ConnectionError."""
    if port < 1 or port > 65535:
        raise ConnectionError(f"Cannot connect to {host}:{port} - port out of range")
    raise ConnectionError(f"Connection refused by {host}:{port} after 3 retries")


def validate_payload(data: dict) -> None:
    """Validate an API payload - raises on missing fields."""
    required = ["user_id", "action", "timestamp"]
    missing = [f for f in required if f not in data]
    if missing:
        raise KeyError(f"Missing required fields: {', '.join(missing)}")


@app.get("/")
async def root():
    return {"app": "panops-sample-app", "status": "running"}


@app.get("/error/attribute")
async def trigger_attribute_error():
    """NoneType attribute error - user not found."""
    email = get_user_email(1)
    return {"upper_email": email.upper()}


@app.get("/error/division")
async def trigger_division_error():
    """ZeroDivisionError - 100% discount."""
    result = calculate_discount(50.0, 100.0)
    return {"result": result}


@app.get("/error/key")
async def trigger_key_error():
    """KeyError - missing price field."""
    items = [
        {"name": "Widget", "price": 9.99, "quantity": 2},
        {"name": "Gadget", "quantity": 1},
    ]
    result = process_order(items)
    return result


@app.get("/error/index")
async def trigger_index_error():
    """IndexError - accessing beyond list bounds."""
    data = [1, 2, 3]
    return {"value": data[10]}


@app.get("/error/type")
async def trigger_type_error():
    """TypeError - concatenating str and int."""
    result = "Order #" + 42
    return {"result": result}


@app.get("/error/config")
async def trigger_config_error():
    """ValueError - bad config parsing."""
    result = parse_config("invalid-config-no-equals")
    return result


@app.get("/error/connection")
async def trigger_connection_error():
    """ConnectionError - service unreachable."""
    result = connect_to_service("payment-api.internal", 8443)
    return result


@app.get("/error/validation")
async def trigger_validation_error():
    """KeyError - missing required fields in payload."""
    validate_payload({"user_id": 42})
    return {"valid": True}


@app.get("/error/runtime")
async def trigger_runtime_error():
    """RuntimeError - unexpected state."""
    state = random.choice(["active", "suspended", "deleted"])
    if state != "active":
        raise RuntimeError(f"Cannot process request: account is {state}")
    return {"state": state}


@app.get("/error/overflow")
async def trigger_overflow_error():
    """RecursionError - infinite recursion."""
    def fibonacci(n):
        return fibonacci(n - 1) + fibonacci(n - 2)
    return {"result": fibonacci(100)}


@app.get("/error/custom")
async def trigger_custom_error():
    """Raise an HTTPException after logging to Sentry."""
    try:
        raise ValueError("Payment processing failed: invalid card token")
    except ValueError:
        sentry_sdk.capture_exception()
        raise HTTPException(status_code=500, detail="Internal payment error")


@app.get("/healthy")
async def healthy():
    """Endpoint that works fine - for comparison."""
    return {"message": "Everything is fine!", "users_count": 42}
