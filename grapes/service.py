class Service:
    def __init__(self, ctx, name):
        self.ctx = ctx
        self.name = name

        ctx.set(name, self)
