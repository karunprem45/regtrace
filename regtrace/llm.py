"""Claude wrapper that always returns parsed JSON. Tests swap in a fake with the same method."""
import json
import os
import re


class ClaudeJSON:
    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("REGTRACE_MODEL", "claude-sonnet-5-5")

    def complete_json(self, system: str, user: str) -> dict:
        msg = self.client.messages.create(
            model=self.model, max_tokens=2000, system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        return parse_json(text)


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)
