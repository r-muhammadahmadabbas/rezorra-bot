"""Outbound message senders.

`get_sender()` returns MockSender or CloudAPISender depending on WHATSAPP_MODE,
so nothing else in the codebase cares whether Meta is reachable.
"""
from app.config import settings
from app.senders.base import Button, Row, Sender
from app.senders.cloud_api import CloudAPISender
from app.senders.mock import MockSender

_sender: Sender | None = None


def get_sender() -> Sender:
    """Process-wide sender, chosen once from config."""
    global _sender
    if _sender is None:
        _sender = CloudAPISender() if settings.is_cloud else MockSender()
    return _sender


__all__ = ["Button", "Row", "Sender", "MockSender", "CloudAPISender", "get_sender"]
