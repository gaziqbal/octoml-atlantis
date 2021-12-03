from abc import abstractmethod, ABC
from math import ceil
from typing import Collection, Dict, List, Set

from .pearls import Pearl, PearlColor, PearlLayer


WorkerId = int


class Worker(ABC):
    def __init__(self, id: WorkerId, pearls: Collection[Pearl]):
        self.id = id
        self.pearls: Dict[int, Pearl] = {p.id: p for p in pearls}
        # self.assigned: Set[Pearl] = set()

    def __str__(self):
        return f"{self.__class__.__name__}: {self.id}, Pearls: {len(self.pearls)}"

    @property
    @abstractmethod
    def processing_rate(self) -> Dict[PearlColor, int]:
        pass

    def pending_pearls(self) -> List[Pearl]:
        return [p for p in self.pearls.values() if not p.digested]

    def digested_pearls(self) -> List[Pearl]:
        return [p for p in self.pearls.values() if p.digested]

    def pending_cost(self) -> int:
        return sum(self.cost_pearl(p) for p in self.pearls.values())

    def cost_layer(self, pearl_layer: PearlLayer) -> int:
        processing_cost = ceil(
            (pearl_layer.thickness * 1.0) / self.processing_rate[pearl_layer.color]
        )
        return processing_cost

    def cost_pearl(self, pearl: Pearl) -> int:
        return sum(self.cost_layer(l) for l in pearl.layers)


class GeneralWorker(Worker):
    @property
    def processing_rate(self) -> Dict[PearlColor, int]:
        return {
            PearlColor.Red: 1,
            PearlColor.Green: 1,
            PearlColor.Blue: 1,
        }


class VectorWorker(Worker):
    @property
    def processing_rate(self) -> Dict[PearlColor, int]:
        return {
            PearlColor.Red: 1,
            PearlColor.Green: 5,
            PearlColor.Blue: 2,
        }


class MatrixWorker(Worker):
    @property
    def processing_rate(self) -> Dict[PearlColor, int]:
        return {
            PearlColor.Red: 1,
            PearlColor.Green: 2,
            PearlColor.Blue: 10,
        }
