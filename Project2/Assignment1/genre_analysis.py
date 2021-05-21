from datetime import datetime
from time import time
import re
import logging
import sys
import collections
import csv
import numpy as np
import json
import pandas as pd

DATA_LOCATION = "../../fma_metadata/"
TRACKS = DATA_LOCATION + "tracks.csv"
FEATURES = DATA_LOCATION + "features.csv"

BFR_RESULTS = "bfr_results.json"


def mahalanobis_distance(v1, v2, var_vector):
    return np.linalg.norm(v1 - v2)

if __name__ == "__main__":

    centroid_and_var = []

    with open(BFR_RESULTS, "r") as r:
        discard_set = json.load(r)
    
    for ind in range(len(discard_set)):
        centroid = np.array(discard_set[ind][1]).astype(np.float)/discard_set[ind][0]
        var = np.sqrt(np.array(discard_set[ind][1]).astype(np.float)/discard_set[ind][0] - np.square(centroid))
        centroid_and_var.append((centroid, var)) 

    genres_df = pd.read_csv(TRACKS, header=1, skiprows=[2])
    
    genre_by_centroid = {i:{} for i in range(len(centroid_and_var))}

    with open(FEATURES, "r") as filereader:
        counter = 0

        for line in filereader:
            counter += 1
            if counter < 5: continue
            
            point_features = line.split(",")

            point_id = int(point_features.pop(0))
            point_features = np.array(point_features).astype(np.float)
            mask = [ 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191]
            point_features = np.delete(point_features, mask)

            genre = genres_df[genres_df.iloc[:,0] == point_id]['genre_top'].item()

            min_cluster_dist = mahalanobis_distance(point_features, centroid_and_var[0][0],centroid_and_var[0][1])

            min_cluster_ind = 0

            for i in range(1, len(centroid_and_var)):
                cent, var = centroid_and_var[i]
                md = mahalanobis_distance(point_features, cent, var)
                if min_cluster_dist == np.nan or md < min_cluster_dist:
                    min_cluster_dist = md
                    min_cluster_ind = i
            
            if min_cluster_dist == np.nan: continue

            if genre not in genre_by_centroid[min_cluster_ind]:
                genre_by_centroid[min_cluster_ind][genre] = 0
            
            genre_by_centroid[min_cluster_ind][genre] += 1
    
    with open("genre_results.json", "w") as r:
        json.dump(genre_by_centroid, r)
            




    