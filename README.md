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

The average score is 14.5 at the moment.

## Architecture

The **key concepts** are as follows
- **Pearls** have **PearlLayers**, each with a **PearlColor** and thickness
- **Worker** is an abstract class which provides method to evaluate pearl costs. 
	- Workers have pearls
	- **GeneralWorker**, **VectorWorker** and **MatrixWorker** are subclasses.
- **World** maintains workers and their layout.
- **Simulator** provides a step() method which creates a set of commands based on the state of the World.
	- This where the heavy lifting occurs
- The harness in **atlantis.py** creates the world from stdin, asks the simulator to generate the commands and emits them to stdout

## Algorithm
There were two approaches examined. The first one was to have a stateless algorithm which determineed next best step for each pearl based on current state of the simulation. This felt promising would be debug-friendly, the work being done was feeling redundant and my initial implementation got more complicated then I was happy with.

The approach I landed on was to create execution plans at two instances - when the pearl is first seen, and when the pearl is fully digested. These execution plans are then dispatched at each step of the simulation. There is some prioritization necessary to handle conflicting commands for workers. The strategy is shared in the simulator notes.

## Tests
There are some simple tests in the /tests folder. 
Given my own time constraints, most of the development occured via the test enviromment provided by the fixtures.py file. These were used to verify the path finding algorithm as well as general diagnosis for when things went wrong.
It would very reasonable to promote these to be integration tests given that the work assignment algorithsm are deterministic.
It would also be very reasonable to create a few unit tests for path finding and pearl prioritization.