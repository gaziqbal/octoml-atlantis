import json
import logging

from atlantis.config import Config
from atlantis.simulators import TestSimulator, AtlantisSimulator
from atlantis.world import World
from atlantis.util import render_world

if __name__ == "__main__":

    config = Config.initialize(
        default_log_file="debug.log",
        default_log_level=logging.DEBUG,
        default_enable_render=True,
    )
    logger = logging.getLogger()

    test_fixture_with_no_pearls = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[]},{"id":1,"flavor":"Vector","desk":[]},{"id":2,"flavor":"Matrix","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Vector","desk":[]},{"id":5,"flavor":"General","desk":[]},{"id":6,"flavor":"General","desk":[]},{"id":7,"flavor":"Matrix","desk":[]},{"id":8,"flavor":"Vector","desk":[]},{"id":9,"flavor":"Matrix","desk":[]},{"id":10,"flavor":"General","desk":[]}],"neighbor_map":[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[0,2],[0,4],[0,6],[0,8]],"score":0}
    """
    test_fixture_with_pearl = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":14},{"color":"Red","thickness":12}]}]},{"id":1,"flavor":"Vector","desk":[]},{"id":2,"flavor":"Matrix","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Vector","desk":[]},{"id":5,"flavor":"General","desk":[]},{"id":6,"flavor":"General","desk":[]},{"id":7,"flavor":"Matrix","desk":[]},{"id":8,"flavor":"Vector","desk":[]},{"id":9,"flavor":"Matrix","desk":[]},{"id":10,"flavor":"General","desk":[]}],"neighbor_map":[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[0,2],[0,4],[0,6],[0,8]],"score":0}
    """
    test_fixture_two_paths_to_node = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":14},{"color":"Red","thickness":12}]}]},{"id":1,"flavor":"General","desk":[]},{"id":2,"flavor":"General","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Matrix","desk":[]}],"neighbor_map":[[0,1],[1,3],[3,4],[0,2],[2,4]],"score":0}
    """
    test_fixture_two_paths_to_node_s1 = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[]},{"id":1,"flavor":"General","desk":[]},{"id":2,"flavor":"General","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":14},{"color":"Red","thickness":12}]}]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Matrix","desk":[]}],"neighbor_map":[[0,1],[1,3],[3,4],[0,2],[2,4]],"score":0}
    """
    test_fixture_two_paths_to_node_s2 = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[]},{"id":1,"flavor":"General","desk":[]},{"id":2,"flavor":"General","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Matrix","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":14},{"color":"Red","thickness":12}]}]}],"neighbor_map":[[0,1],[1,3],[3,4],[0,2],[2,4]],"score":0}
    """
    # nearly digested blue
    test_fixture_two_paths_to_node_s3 = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[]},{"id":1,"flavor":"General","desk":[]},{"id":2,"flavor":"General","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Matrix","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":1},{"color":"Red","thickness":12}]}]}],"neighbor_map":[[0,1],[1,3],[3,4],[0,2],[2,4]],"score":0}
    """
    # nearly digested red
    test_fixture_two_paths_to_node_s4 = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[]},{"id":1,"flavor":"General","desk":[]},{"id":2,"flavor":"General","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Matrix","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":0},{"color":"Red","thickness":1}]}]}],"neighbor_map":[[0,1],[1,3],[3,4],[0,2],[2,4]],"score":0}
    """
    # fully digested
    test_fixture_two_paths_to_node_s4 = """
    {"workers":[{"id":0,"flavor":"Vector","desk":[]},{"id":1,"flavor":"General","desk":[]},{"id":2,"flavor":"General","desk":[]},{"id":3,"flavor":"Vector","desk":[]},{"id":4,"flavor":"Matrix","desk":[{"id":1246714994,"layers":[{"color":"Blue","thickness":0},{"color":"Red","thickness":0}]}]}],"neighbor_map":[[0,1],[1,3],[3,4],[0,2],[2,4]],"score":0}
    """

    test_scripts = [
        """{"workers": [{"id": 0, "flavor": "General", "desk": [{"id": 1074154026, "layers": [{"color": "Red", "thickness": 14}, {"color": "Blue", "thickness": 11}]}]}, {"id": 1, "flavor": "Vector", "desk": [{"id": 921899037, "layers": [{"color": "Green", "thickness": 12}]}, {"id": 4060079315, "layers": [{"color": "Green", "thickness": 14}, {"color": "Blue", "thickness": 13}]}, {"id": 2875482560, "layers": [{"color": "Blue", "thickness": 13}, {"color": "Green", "thickness": 12}]}]}, {"id": 2, "flavor": "General", "desk": []}, {"id": 3, "flavor": "General", "desk": [{"id": 3199881777, "layers": [{"color": "Red", "thickness": 12}, {"color": "Red", "thickness": 6}]}]}, {"id": 4, "flavor": "General", "desk": []}, {"id": 5, "flavor": "Vector", "desk": [{"id": 1335664435, "layers": []}]}, {"id": 6, "flavor": "General", "desk": []}, {"id": 7, "flavor": "Matrix", "desk": [{"id": 3858911313, "layers": [{"color": "Blue", "thickness": 13}]}, {"id": 1991973039, "layers": [{"color": "Red", "thickness": 3}]}, {"id": 1452949821, "layers": [{"color": "Green", "thickness": 11}, {"color": "Blue", "thickness": 11}]}, {"id": 3781486031, "layers": [{"color": "Blue", "thickness": 13}, {"color": "Blue", "thickness": 13}]}, {"id": 2123912444, "layers": [{"color": "Blue", "thickness": 14}, {"color": "Blue", "thickness": 14}]}]}, {"id": 8, "flavor": "Vector", "desk": [{"id": 3994712159, "layers": [{"color": "Green", "thickness": 3}]}, {"id": 829228016, "layers": [{"color": "Green", "thickness": 10}, {"color": "Green", "thickness": 14}]}, {"id": 4188836683, "layers": [{"color": "Red", "thickness": 14}, {"color": "Green", "thickness": 13}]}]}, {"id": 9, "flavor": "General", "desk": []}, {"id": 10, "flavor": "General", "desk": []}], "neighbor_map": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [0, 3], [0, 7], [0, 8], [0, 10]], "score": 2}"""
        # """{"workers": [{"id": 0, "flavor": "Vector", "desk": [{"id": 1246714994, "layers": [{"color": "Blue", "thickness": 14}, {"color": "Red", "thickness": 12}]}]}, {"id": 1, "flavor": "Vector", "desk": []}, {"id": 2, "flavor": "Matrix", "desk": []}, {"id": 3, "flavor": "Vector", "desk": []}, {"id": 4, "flavor": "Vector", "desk": []}, {"id": 5, "flavor": "General", "desk": []}, {"id": 6, "flavor": "General", "desk": []}, {"id": 7, "flavor": "Matrix", "desk": []}, {"id": 8, "flavor": "Vector", "desk": []}, {"id": 9, "flavor": "Matrix", "desk": []}, {"id": 10, "flavor": "General", "desk": []}], "neighbor_map": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [0, 2], [0, 4], [0, 6], [0, 8]], "score": 0}""",
        # """{"workers": [{"id": 0, "flavor": "Vector", "desk": [{"id": 2056472878, "layers": [{"color": "Green", "thickness": 11}, {"color": "Blue", "thickness": 12}]}]}, {"id": 1, "flavor": "Vector", "desk": []}, {"id": 2, "flavor": "Matrix", "desk": [{"id": 1246714994, "layers": [{"color": "Blue", "thickness": 14}, {"color": "Red", "thickness": 12}]}]}, {"id": 3, "flavor": "Vector", "desk": []}, {"id": 4, "flavor": "Vector", "desk": []}, {"id": 5, "flavor": "General", "desk": []}, {"id": 6, "flavor": "General", "desk": []}, {"id": 7, "flavor": "Matrix", "desk": []}, {"id": 8, "flavor": "Vector", "desk": []}, {"id": 9, "flavor": "Matrix", "desk": []}, {"id": 10, "flavor": "General", "desk": []}], "neighbor_map": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10], [0, 2], [0, 4], [0, 6], [0, 8]], "score": 0}""",
    ]

    s = AtlantisSimulator()
    for i, script in enumerate(test_scripts):
        j = json.loads(script)
        w = World.create_from(j)
        if config.enable_render:
            render_world(w, f"./{config.output_path}/debug-{i}.png")

        commands = s.step(w)
        output = {}
        for c in commands:
            output.update(c.to_json())
        output = json.dumps(output)
        logger.info(output)
