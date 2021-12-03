from abc import abstractmethod, ABC
from typing import Dict

from .pearls import PearlId
from .workers import WorkerId


class Command(ABC):
    def __init__(self, worker_id: WorkerId, pearl_id: PearlId):
        self.worker_id = worker_id
        self.pearl_id = pearl_id

    @abstractmethod
    def to_json(self) -> Dict:
        pass


class PassCommand(Command):
    def __init__(
        self, worker_id: WorkerId, pearl_id: PearlId, target_worker_id: WorkerId
    ):
        super().__init__(worker_id, pearl_id)
        self.target_worker_id = target_worker_id

    def to_json(self) -> Dict:
        return {
            self.worker_id: {
                "Pass": {"pearl_id": self.pearl_id, "to_worker": self.target_worker_id}
            }
        }


class NomCommand(Command):
    def __init__(self, worker_id: WorkerId, pearl_id: PearlId):
        super().__init__(worker_id, pearl_id)

    def to_json(self) -> Dict:
        return {self.worker_id: {"Nom": self.pearl_id}}
