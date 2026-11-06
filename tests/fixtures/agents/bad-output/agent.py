class A:
    def handle(self, ctx, message):
        return {"type": "message", "content": ""}


def create():
    return A()
