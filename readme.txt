

architecture overview of atlantis economy simulator

the simulator will take each step as input and emit work steps


we'll represent workers as nodes which have state and helper methods

pearls are pearls


the economic engine will build costed routes for each pearl from each worker to its neighbours
this will be built via a depth first search which will examine each worker's capabilities and link it to its neighbours

during runtime, the engine will also be aware of the existing workloads for each worker and add that into the cost consideration before deciding what to do

the work distribution algorithm takes the following into account

- for a given pearl, examine its outermost layer and then find which neighbour will take the least steps to process it

abstractions

worker
	general
	vector
	matrix
	- has a desk
		which has pearls - pending or digested

pearl
- isDigested
- total layers
- ordered layers

dispatching logic should be in the economic engine
which should be abstractable

world representation should be standalone

world.create_from(json)
engine(world)
json = engine.step()
emit(json)

tests
world creation
worker ranking
engine dispatching - is the pearl going to the appropriate place

