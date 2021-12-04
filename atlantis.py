import logging
import json
import sys

from atlantis.config import Config
from atlantis.simulators import AtlantisSimulator
from atlantis.util import render_world
from atlantis.world import World

"""
.\bin\atlantis.windows.exe single-run -n 20 -s 0 -- python atlantis.py --log-level DEBUG --enable-render
.\bin\atlantis.windows.exe average-run -- python atlantis.py --log-level WARNING
"""

if __name__ == "__main__":
    """
    Entry point for the Atlantis pearl processing simulator
    """

    config = Config.initialize()
    logger = logging.getLogger()

    sim = AtlantisSimulator()

    for i, line in enumerate(sys.stdin):

        # Read from stdin and create the world
        input = json.loads(line)
        logger.info(f"Step: {i}: Input: {json.dumps(input)}")

        world = World.create_from(input)
        if config.enable_render:
            render_world(world, f"./{config.output_path}/atlantis-{i:02d}.png")

        # Run the simulation
        commands = sim.step(world)
        # Dump commands to json
        output = {}
        for c in commands:
            output.update(c.to_json())
        json_output = json.dumps(output)
        logger.info(f"Step: {i}: Output: " + json_output.replace("'", '"'))

        # Write to stdout
        print(json_output, flush=True)
