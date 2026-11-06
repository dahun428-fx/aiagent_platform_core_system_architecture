class A:
    def handle(self, ctx, message):
        return {"type": "message", "content": "credentialRef=lease-0123456789abcdef"}


def create():
    return A()
