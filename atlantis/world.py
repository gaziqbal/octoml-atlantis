from collections import OrderedDict, defaultdict
from typing import Collection, Dict, List, Set, Tuple
from operator import attrgetter

from .pearls import PearlColor, PearlLayer, Pearl
from .workers import Worker, GeneralWorker, MatrixWorker, VectorWorker, WorkerId


class World:
    """
    Represents the current state of the world
    This includes the workers, their layout/configuration and the pearls in play
    """

    def __init__(
        self,
        workers: Dict[WorkerId, Worker],
        neighbor_map: Collection[Tuple[WorkerId, WorkerId]],
        score: int,
    ):
        self.workers = workers
        self.score = score
        self.neighbor_map = neighbor_map

        worker_neighbors: Dict[Worker, Set[Worker]] = defaultdict(set)
        for worker_id, neighbor_worker_id in neighbor_map:
            worker = workers[worker_id]
            neighbor = workers[neighbor_worker_id]
            worker_neighbors[worker].add(neighbor)
            worker_neighbors[neighbor].add(worker)

        # build a sorted list of neighbors for each worker
        # the intent is to ensure that we iterate deterministically
        self.neighbors = OrderedDict(
            {
                w: sorted(neighbors, key=attrgetter("id"))
                for w, neighbors in worker_neighbors.items()
            }
        )

    @classmethod
    def create_from(cls, json: Dict) -> "World":
        """
        Create the world from the provided json payload
        """
        # for each worker, get the flavor, create the appropriate type, then for each pearl, create the layer
        workers: Dict[int, Worker] = OrderedDict()
        for worker in json["workers"]:
            pearls: List[Pearl] = []
            for pearl in worker["desk"]:
                layers: List[PearlLayer] = []
                for layer in pearl["layers"]:
                    l = PearlLayer(PearlColor[layer["color"]], layer["thickness"])
                    layers.append(l)
                p = Pearl(pearl["id"], layers)
                pearls.append(p)
            w: Worker = None
            worker_flavor = worker["flavor"]
            if worker_flavor == "Vector":
                w = VectorWorker(worker["id"], pearls)
            elif worker_flavor == "Matrix":
                w = MatrixWorker(worker["id"], pearls)
            else:
                w = GeneralWorker(worker["id"], pearls)
            workers[w.id] = w
        sim = cls(workers, json["neighbor_map"], json["score"])
        return sim
