# octo-atlantis

This Python module server as the user profram for the Atlantis Pearl processing command terminal in the OctoML coding exercise.
The atlantis.py file is the entrypoint and can be executed as follows

```
.\bin\atlantis.windows.exe single-run -s 0 -- python atlantis.py --log-level DEBUG
.\bin\atlantis.windows.exe average-run -- python atlantis.py --log-level WARNING
```

The following command line arguments can be used for atlantis.py
- log-level can be set to the Python logging levels
- enable-render can be added as a switch and will render a representation of the world 
	- You will need the pydot package installed (as per the requirements.txt) 
	- You will also need to have the the [GraphVis](https://www.graphviz.org/) package installed locally.

## Architecture

The **key concepts** are as follows
- **Pearls** have **PearlLayers**, each with a **PearlColor** and thickness
- **Worker** is an abstract class which provides method to evaluate pearl costs. 
	- Workers have pearls
	- **GeneralWorker**, **VectorWorker** and **MatrixWorker** are subclasses.
- **World** maintains workers and their layout.
- **Simulator** provides a step() method which creates a set of commands based on the state of the World.
- The harness in **atlantis.py** creates the world from stdin, asks the simulator to generate the commands and emits them to stdout

The heavy lifting happens in the simulator.

the economic engine will build costed routes for each pearl from each worker to its neighbours
this will be built via a depth first search which will examine each worker's capabilities and link it to its neighbours
during runtime, the engine will also be aware of the existing workloads for each worker and add that into the cost consideration before deciding what to do
the work distribution algorithm takes the following into account
- for a given pearl, examine its outermost layer and then find which neighbour will take the least steps to process it
abstractions
dispatching logic should be in the economic engine
which should be abstractable


## Tests
There are some very simple tests in the /tests folder. 
Given my own time constraints, most of the development occured via the test enviromment provided by the fixtures.py file. These were used to verify the path finding algorithm as well as general diagnosis for when things went wrong.
It would very reasonable to promote these to be integration tests given that the work assignment algorithsm are deterministic.
It would also be very reasonable to create a few unit tests for path finding and pearl prioritization.