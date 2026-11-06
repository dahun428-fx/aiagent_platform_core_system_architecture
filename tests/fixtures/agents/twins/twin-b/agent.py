class A:
    def handle(self, ctx, message):
        return {"type": "message", "content": "from-b"}


def create():
    return A()
