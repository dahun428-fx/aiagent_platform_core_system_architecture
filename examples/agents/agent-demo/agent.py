"""Built-in reference Agent: forwards the message to the model route."""


class EchoAgent:
    def handle(self, ctx, message):
        return {"type": "message", "content": ctx.generate(message["content"])}


def create():
    return EchoAgent()
