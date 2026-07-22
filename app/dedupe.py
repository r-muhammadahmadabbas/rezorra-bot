"""Message de-duplication.

Meta retries a webhook if we do not answer 200 fast enough. Without this the bot
replies twice to the same message. Keyed on Meta's wamid, which is stable per message.

In-memory is fine for the prototype; this moves to Redis when we deploy.
"""
from collections import OrderedDict

MAX_TRACKED = 5000


class SeenMessages:
    def __init__(self, capacity: int = MAX_TRACKED) -> None:
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._capacity = capacity

    def already_handled(self, message_id: str) -> bool:
        """True if we have processed this id before. Records it either way."""
        if message_id in self._seen:
            return True

        self._seen[message_id] = None
        if len(self._seen) > self._capacity:
            self._seen.popitem(last=False)  # drop oldest
        return False


seen_messages = SeenMessages()
