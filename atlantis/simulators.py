import heapq
import logging

from math import inf
from collections import defaultdict, OrderedDict

from abc import abstractmethod, ABC
from typing import Collection, Dict, Set, List, Tuple

from .commands import Command, PassCommand, NomCommand
from .pearls import Pearl, PearlId
from .workers import Worker, WorkerId
from .world import World


class Simulator(ABC):
    @abstractmethod
    def step(self, world: World) -> Collection[Command]:
        pass


class TestSimulator(Simulator):
    """
    A simple simulator where the Gatekeeper does all the woprk
    """

    def step(self, world: World) -> Collection[Command]:
        gatekeeper = world.workers[0]
        pending_pearls = gatekeeper.pending_pearls()
        if pending_pearls:
            cmd = NomCommand(gatekeeper.id, pending_pearls[0].id)
            return [cmd]
        return []


"""
Algorithm
For a world with n nodes, visit each node breath first (top down)
For the ones with pearls, select the pearl with most layers, p and determine the best processing path.

We do this by evaluating the processing cost p(p) + travel cost t(p) for each worker and selecting the one with the lowest cost
So for each pearl p we are visting up to n nodes

Alternately, we could keep track of pearls - ordered list of most expensive pearls
Each pearl is a job - when we get a job we want to route to the least cost spot

Settings
Order pearls by FIFO rather than most layers
Cost pearls by all layers rather than just the top one

Can we prioritize moves over processing?

"""


class AtlantisSimulator(Simulator):
    def __init__(self):

        self.logger = logging.getLogger(__name__)
        # maps a pearl id to a list of commands
        self.execution_plans: Dict[PearlId, List[Command]] = {}
        # maps a worker id to the sum of costs of currently booked commands
        self.worker_costs: Dict[WorkerId, int] = defaultdict(int)

    def find_shortest_path(
        self, start: Worker, end: Worker, world: World
    ) -> List[WorkerId]:

        # find path from start to end
        # there isn't an intuitive
        # we do not have a heuristic here
        move_costs: Dict[Worker, int] = {start: 0}
        move_paths: Dict[Worker, Worker] = {}

        visited: Set[WorkerId] = set()
        queue = [(0, start.id)]
        while queue:
            cost, worker_id = heapq.heappop(queue)
            if worker_id not in visited:
                visited.add(worker_id)
                if worker_id == end.id:
                    break

                worker = world.workers[worker_id]
                neighbors = world.neighbors[worker]
                for n in neighbors:
                    if n.id in visited:
                        continue
                    move_cost = cost + self.worker_costs.get(n.id, 0) + 1
                    last_move_cost = move_costs.get(n.id, inf)
                    if move_cost < last_move_cost:
                        move_costs[n] = move_cost
                        move_paths[n] = worker
                        heapq.heappush(queue, (move_cost, n.id))

        # now build a path from the map
        route = AtlantisSimulator.build_route(start, end, move_paths)
        return route

    @staticmethod
    def build_route(
        start: Worker, end: Worker, paths: Dict[Worker, Worker]
    ) -> List[Worker]:
        route = [end]
        iterator = end
        while iterator != start:
            worker = paths[iterator]
            route.insert(0, worker)
            iterator = worker
        return route

    def build_commands_from_route(
        self, pearl: Pearl, route: List[Worker]
    ) -> List[Command]:
        cmds = []
        current = route[0]
        for w in route[1:]:
            cmd = PassCommand(current.id, pearl.id, w.id)
            cmds.append(cmd)
            current = w
        if not pearl.digested:
            # add nom commands
            nom_steps = current.cost_pearl(pearl)
            for _ in range(nom_steps):
                cmd = NomCommand(current.id, pearl.id)
                cmds.append(cmd)
        return cmds

    def create_execution_plan(
        self, pearl: Pearl, worker: Worker, world: World
    ) -> List[Command]:
        self.logger.debug(
            f"create_execution_plan: Pearl: ({pearl}), Worker: ({worker})"
        )

        current_worker = worker
        route = []

        if pearl.digested:
            # Find the way back to the gatekeeper
            gatekeeper = world.workers[0]
            route = self.find_shortest_path(
                current_worker,
                gatekeeper,
                world,
            )
        else:
            # Select a worker to process the pearl
            # Evaluate cost to process pearl at the current worker
            # Consider costs of commands which have already been assigned

            processing_cost = worker.cost_pearl(pearl)
            if worker.id == 0:
                # use the depth of the tree here
                processing_cost += len(world.workers) * 2

            move_cost = self.worker_costs.get(worker.id, 0)
            move_costs: Dict[Worker, int] = {worker: 0}
            move_paths = {}

            best_cost = move_cost + processing_cost
            best_worker = worker

            self.logger.debug(
                f"create_execution_plan: Initial Cost: {move_cost}+{processing_cost}"
            )

            queue = [(move_cost, worker)]
            while queue:
                move_cost, worker = queue.pop(0)
                self.logger.debug(
                    f"create_execution_plan: Consider Worker: ({worker}), MoveCost: {move_cost}"
                )

                # skip this path if it is already exceeding the min cost we already have
                if move_cost >= best_cost:
                    continue

                neighbors = world.neighbors[worker]
                move_cost = move_cost + 1

                for n in neighbors:
                    # if we previously found a cheaper path to this worker then skip this path
                    old_move_cost = move_costs.get(n, inf)
                    new_move_cost = move_cost + self.worker_costs.get(n.id, 0)

                    if old_move_cost <= new_move_cost:
                        continue

                    # save the best path to this worker
                    move_paths[n] = worker
                    move_costs[n] = new_move_cost
                    queue.append((new_move_cost, n))

                    processing_cost = n.cost_pearl(pearl)

                    total_cost = processing_cost + new_move_cost
                    self.logger.debug(
                        f"create_execution_plan: Evaluate Neighbor: ({n}), Cost: {new_move_cost}+{processing_cost}"
                    )

                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_worker = n
                        self.logger.debug(
                            f"create_execution_plan: Found Best: ({best_worker}), Cost: {best_cost}"
                        )

            self.logger.debug(
                f"create_execution_plan: Selected Best: ({best_worker}), Cost: {best_cost}"
            )
            route = AtlantisSimulator.build_route(
                current_worker, best_worker, move_paths
            )

        commands = self.build_commands_from_route(pearl, route)
        # book commands
        for c in commands:
            self.worker_costs[c.worker_id] += 1
        self.logger.debug(f"create_execution_plan: Worker costs {self.worker_costs}")

        return commands

    def get_ordered_pearls_with_workers(self, world):

        # Order pearls by least to most thickness
        ordered_pearls: Tuple[int, int, Pearl, Worker] = []
        for w in world.workers.values():
            for p in w.pearls.values():
                ordered_pearls.append((p.remaining_thickness, p.id, p, w))
        heapq.heapify(ordered_pearls)

        ordered_pearls_with_workers: Dict[Pearl, Worker] = OrderedDict()
        for o in ordered_pearls:
            ordered_pearls_with_workers[o[2]] = o[3]
        return ordered_pearls_with_workers

    def step(self, world: World) -> Collection[Command]:

        pearls_with_workers = self.get_ordered_pearls_with_workers(world)
        self.logger.debug(
            f"step: {len(pearls_with_workers)} pearls, {len(self.execution_plans)} execution plans"
        )

        for i, p in enumerate(pearls_with_workers.items()):
            self.logger.debug(f"step: {i} Pearl: {p[0]}, Worker: {p[1]}")

        cmds: Dict[int, Command] = {}

        for pearl, worker in pearls_with_workers.items():
            if pearl.id not in self.execution_plans:
                self.execution_plans[pearl.id] = self.create_execution_plan(
                    pearl, worker, world
                )

            plan = self.execution_plans[pearl.id]
            command = plan[0]

            # Execute this command if the worker hasn't already been booked
            if command.worker_id in cmds:
                self.logger.debug(
                    f"step: Pearl: {pearl}, Worker: {command.worker_id}: Skipped: {command.to_json()}"
                )
                continue

            cmds[command.worker_id] = command

            # Pop the command the subtract its cost from the worker
            self.worker_costs[command.worker_id] = max(
                0, self.worker_costs[command.worker_id] - 1
            )

            plan.pop(0)

            self.logger.debug(
                f"step: Pearl: {pearl}, Worker: {command.worker_id}, Executing: {command.to_json()}, updated cost: {self.worker_costs[command.worker_id]}, steps remaining: {len(plan)}"
            )

            # Pop the plan if there there are no more steps remaining
            if not plan:
                self.execution_plans.pop(pearl.id)
                self.logger.debug(f"step: Pearl: {pearl}, execution plan completed")

        return cmds.values()
