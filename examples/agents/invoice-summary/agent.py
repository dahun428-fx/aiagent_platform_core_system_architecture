"""Guide example: the invoice summary Agent from the developer guide, on the local mock.

Reads through the mock tool `tool-search` 0.1.0 (the guide's `tool-erp-read` stands in for it) and asks the mock model.
The mock model returns "mock:" + prompt, so the answer is not a real summary.
"""


class InvoiceSummaryAgent:
    def handle(self, ctx, message):
        # The address and credentials of the tool never reach this code: only the tool id, version and arguments.
        found = ctx.call_tool("tool-search", "0.1.0", {"query": message["content"]})
        summary = ctx.generate("Summarize the invoice: " + found)
        return {"type": "message", "content": summary}


def create():
    return InvoiceSummaryAgent()
