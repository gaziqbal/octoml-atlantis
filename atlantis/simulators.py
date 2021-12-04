import heapq
import logging

from math import inf
from collections import defaultdict

from abc import abstractmethod, ABC
from typing import Collection, Dict, Optional, Set, List, Tuple

from .commands import Command, PassCommand, NomCommand
from .pearls import Pearl, PearlId
from .workers import Worker, WorkerId
from .world import World


class Simulator(ABC):
    """
    The simulator provides a step method which returns a list of commands given the provided state of the world
    """

    @abstractmethod
    def step(self, world: World) -> Collection[Command]:
        pass


class TestSimulator(Simulator):
    """
    A simple simulator pearls are nom'ed where they are
    """

    def step(self, world: World) -> Collection[Command]:
        cmds: Dict[WorkerId, Command] = {}
        for p in world.pearls.values():
            if p.digested:
                continue
            worker = world.pearl_workers[p]
            cmds[worker.id] = NomCommand(worker.id, p.id)
        return cmds.values()


class AtlantisSimulator(Simulator):
    """
    This is a stateful simulator which can handle being initialized from any snapshot of the world.
    Pearls are treated as jobs and are assigned execution plans which are evaluted based on
        1. The fastest workers for the job
        2. The distances to the fastest workers
        3. Workload of existing execution plans
        4. Affinities to encourage more work on the edges than at the gate

    Once execution plans are assigned then their commands are dispatched each step and costs are updated
    There can be more than one potential command for each worker and we have a few options to prioritize the pearls
        1. Command type (i.e Pass over Nom)
        2. Pearl's remaining thickness
        3. Pearl's age
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # maps a pearl id to a list of commands
        self.execution_plans: Dict[PearlId, List[Command]] = {}
        # maps a worker id to the number of pending commands
        self.worker_costs: Dict[WorkerId, int] = defaultdict(int)
        # worker affinities considered during assignment
        self.worker_affinities: Dict[WorkerId, int] = None

    def step(self, world: World) -> Collection[Command]:

        pearl_workers = world.get_pearls_with_workers()
        self.logger.debug(
            f"step: {len(pearl_workers)} pearls, {len(self.execution_plans)} execution plans"
        )
        for i, item in enumerate(pearl_workers.items()):
            self.logger.debug(f"step: {i} Pearl: {item[0]}, Worker: {item[1]}")

        # It's a bit wonky do this here.
        # Longer term it may be useful to restructure things so that the world is updated rather than recreated each step.
        # Thhe simulator could then have a reference to the world provided at initialization and do this work then.
        if self.worker_affinities is None:
            self.worker_affinities = self.create_worker_affinities(world)

        # Build proposed commands for each worker based on state of their execution plans
        proposed_cmds: Dict[WorkerId, List[Tuple(int, PearlId, Command)]] = defaultdict(
            list
        )
        for pearl, worker in pearl_workers.items():
            # Get or create the execution plan
            plan = self.execution_plans.get(pearl.id, None)
            if plan is None:
                plan = self.create_execution_plan(pearl, worker, world)
                # Book worker costs
                for cmd in plan:
                    self.worker_costs[cmd.worker_id] += 1
                self.logger.debug(
                    f"create_execution_plan: Worker costs {self.worker_costs}"
                )
                self.execution_plans[pearl.id] = plan

            plan = self.execution_plans[pearl.id]
            cmd = plan[0]

            # Generate command priority
            priority = self.prioritize_command(cmd, pearl)
            worker_cmds = proposed_cmds[cmd.worker_id]
            heapq.heappush(worker_cmds, (priority, pearl.id, cmd))

            self.logger.debug(
                f"step: Pearl: {pearl}, Worker: {cmd.worker_id}, proposed: {cmd.to_json()}, priority: {priority}"
            )

        # Select top commands for each worker
        selected_cmds: Dict[WorkerId, Command] = dict()
        for worker_id, worker_cmds in proposed_cmds.items():
            (priority, pearl_id, cmd) = heapq.heappop(worker_cmds)
            selected_cmds[worker_id] = cmd

            # For each selected command, substract its cost from the woker
            self.worker_costs[worker_id] = max(0, self.worker_costs[worker_id] - 1)

            # Remove the command from the plan
            plan = self.execution_plans[pearl_id]
            plan.pop(0)

            self.logger.debug(
                f"step: Pearl: {pearl_id}, Worker: {worker_id}, selected: {cmd.to_json()}, remaining cost: {self.worker_costs[worker_id]}, remaining steps: {len(plan)}"
            )

            # Pop the plan if when there are no more steps remaining
            if not plan:
                self.execution_plans.pop(pearl_id)
                self.logger.debug(f"step: Pearl: {pearl_id}, execution plan completed")

        return selected_cmds.values()

    def prioritize_command(self, cmd: Command, pearl: Pearl) -> float:
        """
        We always prioritize PassCommands over NomCommands
            There are many more options we can try out here but this appears to work well at the moment
            Any changes to this would also require changes to select_best_worker_route as that currently assumes
            no additional costs for moves
        NomCommands are ranked based on pearl thickness
        """
        if isinstance(cmd, PassCommand):
            priority = (
                1.0 / pearl.remaining_thickness if pearl.remaining_thickness else 0
            )
        else:
            priority = pearl.remaining_thickness
        return priority

    def create_worker_affinities(self, world: World) -> Dict[WorkerId, int]:
        """
        We use the distances from the root/gatekeeper to determine affinities
        The gatekeeper get a penalty equal to the distance to the furthest worker
        The furthest worker gets a penalty of 0
        """
        _, move_costs = self.find_shortest_path(world, world.workers[0])
        max_cost = max(move_costs.values())
        worker_affinities = defaultdict(int)
        for worker, cost in move_costs.items():
            affinity = max_cost - cost
            worker_affinities[worker.id] = affinity
            self.logger.debug(f"Worker affinities: {worker.id} = {affinity}")
        return worker_affinities

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
            route = self.find_route(
                worker,
                gatekeeper,
                world,
            )
        else:
            # Find the route to the best worker
            route = self.select_best_worker_route(pearl, worker, world)

        # Build the list of commands
        commands = self.create_commands_from_route(pearl, route)
        return commands

    def select_best_worker_route(
        self, pearl: Pearl, worker: Worker, world: World
    ) -> List[WorkerId]:
        """
        Returns the best worker and a route to it
        """
        current_worker = worker

        move_cost = 0
        move_costs: Dict[Worker, int] = {worker: 0}
        move_paths = {}

        processing_cost = worker.cost_pearl(pearl)
        booking_cost = self.worker_costs[worker.id] + self.worker_affinities[worker.id]

        best_cost = move_cost + processing_cost + booking_cost
        best_worker = worker

        self.logger.debug(
            f"create_execution_plan: Initial Cost: {best_cost}={move_cost}+{processing_cost}+{booking_cost}"
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

            neighbors = world.worker_neighbors[worker]
            move_cost = move_cost + 1

            for n in neighbors:
                # if we previously found a cheaper path to this worker then skip this path
                old_move_cost = move_costs.get(n, inf)
                if old_move_cost <= move_cost:
                    continue

                # save the best path to this worker
                move_paths[n] = worker
                move_costs[n] = move_cost
                queue.append((move_cost, n))

                processing_cost = n.cost_pearl(pearl)
                booking_cost = self.worker_costs[n.id] + self.worker_affinities[n.id]

                total_cost = processing_cost + move_cost + booking_cost
                self.logger.debug(
                    f"create_execution_plan: Evaluate Neighbor: ({n}), Cost: {total_cost}={move_cost}+{processing_cost}+{booking_cost}"
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
        route = AtlantisSimulator.create_route(current_worker, best_worker, move_paths)
        return route

    def find_route(self, start: Worker, end: Worker, world: World) -> List[WorkerId]:
        move_paths, _ = self.find_shortest_path(world, start, end)
        route = AtlantisSimulator.create_route(start, end, move_paths)
        return route

    def find_shortest_path(
        self,
        world: World,
        start: Worker,
        end: Optional[Worker] = None,
    ) -> Tuple[Dict[Worker, Worker], Dict[Worker, int]]:

        # find path from start to end using a simple heapq based Dijsktra implementation
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
                if end and worker_id == end.id:
                    break
                worker = world.workers[worker_id]
                neighbors = world.worker_neighbors[worker]
                for n in neighbors:
                    if n.id in visited:
                        continue
                    move_cost = cost + self.worker_costs.get(n.id, 0) + 1
                    last_move_cost = move_costs.get(n.id, inf)
                    if move_cost < last_move_cost:
                        move_costs[n] = move_cost
                        move_paths[n] = worker
                        heapq.heappush(queue, (move_cost, n.id))

        return move_paths, move_costs

    @staticmethod
    def create_route(
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
    def create_commands_from_route(pearl: Pearl, route: List[Worker]) -> List[Command]:
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
