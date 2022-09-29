import numpy as np
import FTrack.config as config

def preamb_cluster(pre_edges, pre_trks, ftrack_pwr):

    SF = config.LORA_SF
    PREAMB_CLUSTER_WIDTH = int(2)**(SF-6)
    
    #[predges_sorted, pre_index] = sortrows(pre_edges, 2)
    pre_index = pre_edges[:,1].argsort()
    predges_sorted = pre_edges[pre_index,]
    
    sz = pre_edges.shape
    pre_num = sz[0]
    edge_dist = predges_sorted[1:, 1] - predges_sorted[0:pre_num-1, 1]
    
    # tags indicating preamble clusters
    cluster_tags = (edge_dist <= PREAMB_CLUSTER_WIDTH)
    cluster_tags = np.concatenate(([1], cluster_tags))
    
    pre_clusters = np.zeros(pre_edges.shape)
    pre_tracks = np.zeros(pre_trks.shape)
    cl_num = 0     # # of clusters
    
    cl_pwr_max = 0     # the max track power in the current cluster
    cl_pre_max = []    # the preamble edge info with the max power
    cl_trk_max = []    # the preamble track info with the max power
    for p in range(pre_num):
        tag = cluster_tags[p]
        
        if (tag == 0):
            # add the current cluster into the records
            pre_clusters[cl_num,] = cl_pre_max
            pre_tracks[cl_num,] = cl_trk_max
            cl_num = cl_num + 1
            
            # start of a new cluster           
            cl_pwr_max = 0
            cl_pre_max = []
            cl_trk_max = []

        # record the max track power
        pre_idx = pre_index[p]
        pre_trk = pre_trks[pre_idx,]
        trk_pwr = sum(ftrack_pwr[pre_trk[0], pre_trk[1]:pre_trk[2]])
        if (trk_pwr > cl_pwr_max):
            cl_pwr_max = trk_pwr
            cl_pre_max = pre_edges[pre_idx,]
            cl_trk_max = pre_trk
        
        if (p >= pre_num-1):
            # add the last cluster into the records
            pre_clusters[cl_num,] = cl_pre_max
            pre_tracks[cl_num,] = cl_trk_max
            cl_num = cl_num + 1
    
    pre_edges = pre_clusters[0:cl_num,]
    pre_tracks = pre_tracks[0:cl_num, :]
	
    return pre_edges, pre_tracks
