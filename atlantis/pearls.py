from enum import Enum
from typing import Collection, Iterator, Optional


class PearlColor(Enum):
    Red = "Red"
    Green = "Green"
    Blue = "Blue"


class PearlLayer:
    def __init__(self, color: PearlColor, thickness: int):
        self.color = color
        self.thickness = thickness

    def __str__(self):
        return f"{self.color.name[0]}:{self.thickness}"


PearlId = int


class Pearl:
    def __init__(self, id: PearlId, layers: Collection[PearlLayer]):
        self.id = id
        self.layers = layers

    def __str__(self):
        layers = " ".join(f"({l})" for l in self.layers)
        return f"{self.id}, {layers}"

    def remaining_layers(self) -> Iterator[PearlLayer]:
        for l in self.layers:
            if l.thickness:
                yield l

    @property
    def remaining_thickness(self, color: Optional[PearlColor] = None) -> int:
        t = 0
        for l in self.layers:
            if not color or l.color == color:
                t += l.thickness
        return t

    @property
    def digested(self) -> bool:
        for _ in self.remaining_layers():
            return False
        return True
