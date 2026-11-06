class A:
    def handle(self, ctx, message):
        return {"type": "message", "content": "from-a"}


def create():
    return A()
