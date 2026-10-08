class Room: 

    def __init__(self, name, description): 
        self.name = name
        self.description = description

    def move(self):
        raise NotImplementedError()


    def inspect(self):
        raise NotImplementedError()


    def solve(self): 
        raise NotImplementedError()