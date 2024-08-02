from typing import Protocol

class CompartmentDimension(Protocol):
    def length1(self, epsilon):
        raise NotImplementedError
    
    def length2(self, epsilon):
        raise NotImplementedError
    
    def height(self, epsilon):
        raise NotImplementedError
    

class RoomDimension(CompartmentDimension):
    def __init__(self, length1, length2, height) -> None:
        super().__init__()
        self.dimension1 = length1
        self.dimension2 = length2
        self.dimension3 = height

    def length1(self, epsilon=0):
        return self.dimension1
    
    def length2(self, epsilon=0):
        return self.dimension2
     
    def height(self, epsilon=0):
        return self.dimension3