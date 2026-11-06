"""Template: tool Agent. Uses the local mock tool `tool-search` 0.1.0 (arguments: {"query": str}).

Declare every tool in agent-manifest.json capabilities.tools; undeclared tools are denied (403).
"""


class ToolAgent:
    def handle(self, ctx, message):
        found = ctx.call_tool("tool-search", "0.1.0", {"query": message["content"]})
        summary = ctx.generate("Summarize: " + found)
        return {"type": "message", "content": summary}


def create():
    return ToolAgent()
