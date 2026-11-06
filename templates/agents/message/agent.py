"""Template: message Agent. Replace the body of handle() with your own logic.

ctx.generate(prompt) -> str        calls the Agent Gateway model route (classification-based routing)
ctx.call_tool(id, version, args)   calls a tool declared in agent-manifest.json capabilities.tools
ctx.log(event, **fields)           writes an audit event (only allow-listed fields are kept)
Return {"type": "message", "content": "<non-empty text>"}.
"""


class MessageAgent:
    def handle(self, ctx, message):
        answer = ctx.generate("Answer briefly: " + message["content"])
        return {"type": "message", "content": answer}


def create():
    return MessageAgent()
