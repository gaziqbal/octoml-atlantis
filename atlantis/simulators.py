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
    """
    A simulator returns a list of commands to execute given the provided state of the world
    """

    @abstractmethod
    def step(self, world: World) -> Collection[Command]:
        pass


class TestSimulator(Simulator):
    """
    A simple simulator where the gatekeeper does all the work
    """

    def step(self, world: World) -> Collection[Command]:
        gatekeeper = world.workers[0]
        pending_pearls = gatekeeper.pending_pearls()
        if pending_pearls:
            cmd = NomCommand(gatekeeper.id, pending_pearls[0].id)
            return [cmd]
        return []


class AtlantisSimulator(Simulator):
    """
    This is a stateful simulator which can handle being initialized from any snapshot of the world.
    Pearls are treated as jobs and are assigned execution plans which are evaluted based on
        1. The worker layouts and distances
        2. Workload of existing execution plans

    Once execution plans are assigned then their commands are dispatched each step and costs are updated
    There can be contention here and we have a few options to prioritize pearls
        1. By cost
        2. By age

    We can also decide to prioritize Pass over Nom commands
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # maps a pearl id to a list of commands
        self.execution_plans: Dict[PearlId, List[Command]] = {}
        # maps a worker id to the number of pending commands
        self.worker_costs: Dict[WorkerId, int] = defaultdict(int)

    def step(self, world: World) -> Collection[Command]:

        pearls_with_workers = self.get_ordered_pearls_with_workers(world)
        self.logger.debug(
            f"step: {len(pearls_with_workers)} pearls, {len(self.execution_plans)} execution plans"
        )
        for i, p in enumerate(pearls_with_workers.items()):
            self.logger.debug(f"step: {i} Pearl: {p[0]}, Worker: {p[1]}")

        cmds: Dict[int, Command] = {}

        for pearl, worker in pearls_with_workers.items():

            # Get or create the execution plan
            plan = self.execution_plans.get(pearl.id, None)
            if plan is None:
                plan = self.create_execution_plan(pearl, worker, world)
                # Book worker costs
                for command in plan:
                    self.worker_costs[command.worker_id] += 1
                self.logger.debug(
                    f"create_execution_plan: Worker costs {self.worker_costs}"
                )
                self.execution_plans[pearl.id] = plan

            plan = self.execution_plans[pearl.id]
            command = plan[0]

            # Execute this command if the worker hasn't already been booked
            if command.worker_id in cmds:
                self.logger.debug(
                    f"step: Pearl: {pearl}, Worker: {command.worker_id}: skip: {command.to_json()}"
                )
                continue

            cmds[command.worker_id] = command

            # Pop the command the subtract its cost from the worker
            self.worker_costs[command.worker_id] = max(
                0, self.worker_costs[command.worker_id] - 1
            )
            plan.pop(0)

            self.logger.debug(
                f"step: Pearl: {pearl}, Worker: {command.worker_id}, execute: {command.to_json()}, remaining cost: {self.worker_costs[command.worker_id]}, remaining steps: {len(plan)}"
            )

            # Pop the plan if there there are no more steps remaining
            if not plan:
                self.execution_plans.pop(pearl.id)
                self.logger.debug(f"step: Pearl: {pearl}, execution plan completed")

        return cmds.values()

    def get_ordered_pearls_with_workers(self, world):
        """
        Return pearls in order
        """
        ordered_pearls: Tuple[int, int, Pearl, Worker] = []
        for w in world.workers.values():
            for p in w.pearls.values():
                ordered_pearls.append((p.remaining_thickness, p.id, p, w))
        heapq.heapify(ordered_pearls)

        ordered_pearls_with_workers: Dict[Pearl, Worker] = OrderedDict()
        for o in ordered_pearls:
            ordered_pearls_with_workers[o[2]] = o[3]
        return ordered_pearls_with_workers

    def create_execution_plan(
        self, pearl: Pearl, worker: Worker, world: World
    ) -> List[Command]:
        """
        Returns an execution plan (a list of commands) for the given pearl at the given worker
        """
        self.logger.debug(
            f"create_execution_plan: Pearl: ({pearl}), Worker: ({worker})"
        )

        route: List[Worker] = []
        if pearl.digested:
            # Find the way back to the gatekeeper
            gatekeeper = world.workers[0]
            route = self.find_shortest_path(
                worker,
                gatekeeper,
                world,
            )
        else:
            # Find the route to the best worker
            route = self.select_best_worker_route(pearl, worker, world)

        # Build the list of commands
        commands = self.build_commands_from_route(pearl, route)
        return commands

    def select_best_worker_route(
        self, pearl: Pearl, worker: Worker, world: World
    ) -> List[WorkerId]:
        """
        Returns the best worker and a route to it
        """
        current_worker = worker

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
        route = AtlantisSimulator.build_route(current_worker, best_worker, move_paths)
        return route

    def find_shortest_path(
        self, start: Worker, end: Worker, world: World
    ) -> List[WorkerId]:

        # find path from start to end using Dijsktra
        # A*star doesn't feel like a candidate because there isn't an intuitive heuristic
        move_costs: Dict[Worker, int] = {start: 0}
        move_paths: Dict[Worker, Worker] = {}

        visited: Set[WorkerId] = set()
        # Use the cost and integer id for the priority q
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

        # now build a route from the paths
        route = AtlantisSimulator.build_route(start, end, move_paths)
        return route

    @staticmethod
    def build_route(
        start: Worker, end: Worker, paths: Dict[Worker, Worker]
    ) -> List[Worker]:
        # build a route from start to end from the provided backtracked path mappings
        route = [end]
        iterator = end
        while iterator != start:
            worker = paths[iterator]
            route.insert(0, worker)
            iterator = worker
        return route

    @staticmethod
    def build_commands_from_route(pearl: Pearl, route: List[Worker]) -> List[Command]:
        cmds = []
        current = route[0]
        for w in route[1:]:
            cmd = PassCommand(current.id, pearl.id, w.id)
            cmds.append(cmd)
            current = w
        if not pearl.digested:
            # queue required number of nom commands at destination worker
            nom_steps = current.cost_pearl(pearl)
            for _ in range(nom_steps):
                cmd = NomCommand(current.id, pearl.id)
                cmds.append(cmd)
        return cmds
