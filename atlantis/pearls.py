from enum import Enum
from typing import List


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
    def __init__(self, id: PearlId, layers: List[PearlLayer]):
        self.id = id
        self.layers = layers

    def __str__(self):
        layers = " ".join(f"({l})" for l in self.layers)
        return f"{self.id}, {layers}"

    @property
    def remaining_thickness(self) -> int:
        t = 0
        for l in self.layers:
            t += l.thickness
        return t

    @property
    def digested(self) -> bool:
        if self.remaining_thickness:
            return False
        return True
