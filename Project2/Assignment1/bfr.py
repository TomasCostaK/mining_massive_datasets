from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from datetime import datetime
from time import time
import re
import logging
import sys
import collections
import csv
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestCentroid
import numpy as np

DATA_LOCATION = "../../fma_metadata/"
TRACKS = DATA_LOCATION + "tracks.csv"
FEATURES = DATA_LOCATION + "features.csv"

NUMBER_OF_CLUSTERS = 11
SAMPLE_SIZE = 2000

def mahalanobis_distance(v1, v2, var_vector):
    return np.sqrt(np.sum(np.square((v1 - v2)/var_vector)))

if __name__ == "__main__":
    sc = SparkContext(appName="Assignment1")
    spark = SparkSession(sc)
    sc.setLogLevel("WARN")

    textfile = sc.textFile(FEATURES)

    data_features = textfile.zipWithIndex().\
                    filter(lambda x: x[1] > 3).\
                    map(lambda x: x[0].split(','))
    
    kmeans = KMeans(n_clusters=NUMBER_OF_CLUSTERS)

    k_clusters = data_features.takeSample(False, NUMBER_OF_CLUSTERS)
    data_features = data_features.filter(lambda x: x[0] not in [k[0] for k in k_clusters])
    k_clusters = np.array([k[1:] for k in k_clusters]).astype(np.float)

    threshold = 2*np.sqrt(k_clusters.shape[1])

    discard_set = [[1, k_clusters[i], np.square(k_clusters[i])] for i in range(NUMBER_OF_CLUSTERS)]
    compression_set = [set() for i in range(NUMBER_OF_CLUSTERS)]
    retained_set = [set() for i in range(NUMBER_OF_CLUSTERS)]

    cluster_points = k_clusters.copy()

    while not data_features.isEmpty():
        data_sample = data_features.takeSample(False, SAMPLE_SIZE)
        data_features = data_features.filter(lambda x: x[0] not in [k[0] for k in data_sample])
        data_sample = np.array([k[1:] for k in data_sample]).astype(np.float)

        min_distance_per_sample = [(-1, -1) for i in range(SAMPLE_SIZE)]
        points_to_remove = []
        
        for i in range(NUMBER_OF_CLUSTERS):
            ds = discard_set[i]
            centroid = ds[1]/ds[0]
            variance = ds[2]/ds[0] - np.square(centroid) 
            std_deviation = np.sqrt(variance)

            for ind in range(SAMPLE_SIZE):
                point = data_sample[ind]
                md = mahalanobis_distance(point, centroid, std_deviation)
                curr_min_dist, curr_min_ind = min_distance_per_sample[ind]
                if curr_min_dist > 0 and curr_min_dist > md and curr_min_dist < threshold:
                    min_distance_per_sample[ind] = (md, i)
                    points_to_remove.append(ind)

        for ind in points_to_remove:
            curr_min_dist, curr_min_ind = min_distance_per_sample[ind]
            ds = discard_set[curr_min_ind]
            ds[0] += 1
            ds[1] += data_sample[ind]
            ds[2] += np.square(data_sample[ind])
        
        data_sample = [n for n in data_sample if n not in points_to_remove]

        kmeans.fit(data_sample)
        CS = kmeans.cluster_centers_

        print(CS)
        break

    sc.stop()