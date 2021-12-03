import pydot

from .world import World

# Render the world as a png - Used for debugging
def render_world(world: World, path: str):
    g = pydot.Dot("Atlantis", graph_type="graph")
    for w in world.workers.values():
        label = f"{w.id} - {type(w).__name__}"
        if w.pearls:
            label += "\n"
            label += "\n".join([str(p) for p in w.pearls.values()])
        g.add_node(pydot.Node(w.id, label=label, shape="oval"))
    for edge in world.neighbor_map:
        g.add_edge(pydot.Edge(edge[0], edge[1]))
    g.write(path, format="png")
