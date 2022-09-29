# OpenLoRa Implementation

config.py: Set up the configuration for LoRa.
RX_Sampl_Rate: Sampling rate for the input data
LORA_BW: Bandwidth
LORA_SF: Spreading factor
Packet_Time: Total duration of the input dataset in seconds
Packets_Num: Total number of packets in the input data (= Transmission rate of one node * Number of nodes in network * Packet_Time)
input_file: Path to the input data file
true_sym: Ground truth for the demodulated symbols transmitted by the LoRa node
true_msg: Ground truth for the decoded bits transmitted by the LoRa node

master.py: Call the demodulators to process input data
Std-LoRa: demod.std_lora()
CoLoRa: demod.colora()
FTrack: demod.ftrack()
NScale: demod.nscale()
CIC: demod.cic()

demod.py: Includes the 'main' file from each demodulator implementation to be called in the master file

decode.py: LoRa decoder implementation to input demodulated symbols and output decoded bits.

metrics.py: Takes the demodulated symbols as input and calls the decoder to find out various metrics. Prints out Symbols Error Rate (SER), Bit Error Rate (BER), Packet Detection Rate (PDR) and Throughtput (in bits/s)

Docker Configuration:
After changing the configuration within the pulled Docker image, it needs to be rebuilt for the changes to take effect. 
This can be done with the following command from the image directory:
>> docker build --tag open-lora .

For example, to run the framework with a different dataset. This new data file needs to be accessible inside the docker image.
To do this, open the file named 'Dockerfile', and add 'COPY <New dataset file path> .' after line 14.
Then, open 'config.py' file, change the 'input_file' parameter to point to your new data set file. 
Now, run "docker build --tag open-lora ." to rebuild the docker image. Finally, run "docker run open-lora" to run the frmaework with the new data set.


