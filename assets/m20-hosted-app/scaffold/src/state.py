"""Bounded conversation state. The model API remembers nothing between
requests; whatever context the next turn needs, the app sends again. This
class is the whole answer to "then what do we keep?": a hard-bounded list,
oldest turns dropped first, and a count of what was dropped so the bound
is visible instead of silent.

Durable memory, summaries, and retrieval are real tools with a real
module (m12). At one-application scale, a bound you can explain beats a
memory you cannot.
"""


class BoundedHistory:
    def __init__(self, max_turns):
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        self.max_turns = max_turns
        self._turns = []          # each turn: {"role": ..., "content": ...}
        self.dropped = 0

    def add(self, role, content):
        self._turns.append({"role": role, "content": content})
        while len(self._turns) > self.max_turns:
            self._turns.pop(0)
            self.dropped += 1

    def to_payload(self):
        """Exactly what gets SENT. Nothing else exists as far as the
        provider is concerned."""
        return list(self._turns)

    def __len__(self):
        return len(self._turns)
