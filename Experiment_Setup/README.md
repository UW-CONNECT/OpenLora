# OpenLoRa_Tests

## Random_Network:
	Same setup as Random_Offset experiment, but nodes now will follow a poisson distribution without
	a beacon between each transmission. This will most similarly demonstrate an open network with truly
	random traffic.

Need to also mention how to install Radiohead library

DONE:

## Precise_Offset:
	Experiment requires three nodes, the sync_main node will periodically trigger an interrupt
	on two sync_nodes. One sync_node must have its incr and offset parameters set to 0, this node will
	not delay transmission on receiving an inturrupt. Incr and offset can then be set to any desired
	offset on the other sync_node. Transmit times from our tests can be derrived by the SF, BW and data
	being transmitted in the Tx_times.txt file. From here desired delays can be inferred as some
	fraction of the total transmit time (we used 1/10th offsets).

![Alt text](Data/Wiring.png?raw=true "Title")

## Random_Offset:
	Experiment requires N-Nodes and one beacon node. A beacon will periodically trigger all nodes
	to transmit a message. Each node will have a dedicated ID, and this ID will seed a random offset
	to within one message length. This uniformly distributed, random offset will force random colisions
	between the N nodes.