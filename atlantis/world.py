from collections import OrderedDict, defaultdict
from typing import Collection, Dict, List, Set, Tuple
from operator import attrgetter

from .pearls import PearlColor, PearlId, PearlLayer, Pearl
from .workers import Worker, GeneralWorker, MatrixWorker, VectorWorker, WorkerId


class World:
    """
    Represents the current state of the world
    This includes the workers, their layout/configuration and the pearls in play
    """

    def __init__(
        self,
        workers: Dict[WorkerId, Worker],
        pearls: Dict[PearlId, Pearl],
        worker_neighbor_map: Collection[Tuple[WorkerId, WorkerId]],
        score: int,
    ):
        self.workers = workers
        self.pearls = pearls
        self.score = score
        self.worker_neighbor_map = worker_neighbor_map

        worker_neighbors: Dict[Worker, Set[Worker]] = defaultdict(set)
        for worker_id, neighbor_worker_id in worker_neighbor_map:
            worker = workers[worker_id]
            neighbor = workers[neighbor_worker_id]
            worker_neighbors[worker].add(neighbor)
            worker_neighbors[neighbor].add(worker)

        # build a sorted list of neighbors for each worker
        # the intent is to ensure that we iterate deterministically
        self.worker_neighbors = OrderedDict(
            {
                w: sorted(neighbors, key=attrgetter("id"))
                for w, neighbors in worker_neighbors.items()
            }
        )

    def get_pearls_with_workers(self):
        pearl_workers: Dict[Pearl, Worker] = {}
        for worker in self.workers.values():
            for p in worker.pearls:
                pearl_workers[p] = worker
        return pearl_workers

    @classmethod
    def create_from(cls, json: Dict) -> "World":
        """
        Create the world from the provided json payload
        """
        # for each worker, get the flavor, create the appropriate type, then for each pearl, create the layer
        workers: Dict[int, Worker] = OrderedDict()
        pearls: Dict[int, Pearl] = OrderedDict()
        for worker in json["workers"]:
            desk: List[Pearl] = []
            for pearl in worker["desk"]:
                layers: List[PearlLayer] = []
                for layer in pearl["layers"]:
                    l = PearlLayer(PearlColor[layer["color"]], layer["thickness"])
                    layers.append(l)
                p = Pearl(pearl["id"], layers)
                pearls[p.id] = p
                desk.append(p)
            w: Worker = None
            worker_flavor = worker["flavor"]
            if worker_flavor == "Vector":
                w = VectorWorker(worker["id"], desk)
            elif worker_flavor == "Matrix":
                w = MatrixWorker(worker["id"], desk)
            else:
                w = GeneralWorker(worker["id"], desk)
            workers[w.id] = w
        sim = cls(workers, pearls, json["neighbor_map"], json["score"])
        return sim
