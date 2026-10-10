class Room:
    def __init__(self, name, description, items=None):
        self.name = name
        self.description = description
        self.items = items or []

    def move(self):
        return self.name, self.description

    def inspect(self):
        raise NotImplementedError("inspect() must be implemented by the room subclass")

    def solve(self):
        raise NotImplementedError("solve() must be implemented by the room subclass")

    def hint(self):
        return ("Look closely at the items in your inventory.")