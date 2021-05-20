from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from datetime import datetime
from time import time
import re
import logging
import sys
import collections
import json
import csv
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestCentroid
import numpy as np


NUMBER_OF_CLUSTERS = 9
FIRST_DC = f"results_{NUMBER_OF_CLUSTERS}.json"
SAMPLE_SIZE = 10000

def mahalanobis_distance(v1, v2, var_vector):
    return np.sqrt(np.sum(np.square((v1 - v2)/var_vector)))

if __name__ == "__main__":
    sc = SparkContext(appName="Assignment1")
    spark = SparkSession(sc)
    sc.setLogLevel("WARN")

    DATA_LOCATION = sys.argv[1]

    TRACKS = DATA_LOCATION + "tracks.csv"
    FEATURES = DATA_LOCATION + "features.csv"
    
    textfile = sc.textFile(TRACKS)
    data_small_ids = textfile.zipWithIndex().\
                    filter(lambda x: x[1] > 2).\
                    map(lambda x: x[0]).\
                    mapPartitions(lambda x: csv.reader(x, delimiter=',', quotechar='"')).\
                    filter(lambda x: len(x) == 53).\
                    filter(lambda x: x[32] == 'small').\
                    map(lambda x: x[0]).collect()
    
    data_small_ids = set(data_small_ids)

    mask = [ 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191]
    
    data_features = sc.textFile(FEATURES).zipWithIndex().\
                    filter(lambda x: x[1] > 3).\
                    map(lambda x: x[0].split(',')).\
                    filter(lambda x: x[0] not in data_small_ids)
    
    kmeans = KMeans(n_clusters=NUMBER_OF_CLUSTERS)

    threshold = 2*np.sqrt(len(data_features.take(1)[0]))

    with open(FIRST_DC, "r") as r:
        discard_set = json.load(r)
    
    for ind in range(len(discard_set)):
        discard_set[ind][1] = np.array(discard_set[ind][1]).astype(np.float)
        discard_set[ind][2] = np.array(discard_set[ind][2]).astype(np.float)
    compression_set = []
    retained_set = []

    iterations = 0
    data_sample_id = set()

    while not data_features.isEmpty():
        iterations += 1
        print("Number of iterations", iterations, "\nMissing", data_features.count(), "docs")
        data_features = data_features.filter(lambda x: x[0] not in data_sample_id)
        data_sample = data_features.takeSample(False, SAMPLE_SIZE)
        data_sample_id |= set([x[0] for x in data_sample])

        data_sample = np.array([k[1:] for k in data_sample])

        data_sample = np.delete(data_sample, mask, 1)
        data_sample = np.array(data_sample.tolist() + retained_set)

        min_distance_per_sample = [(-1, -1) for i in range(len(data_sample))]
        points_to_remove = []
        
        for i in range(NUMBER_OF_CLUSTERS):
            ds = discard_set[i]
            centroid = ds[1]/ds[0]
            variance = ds[2]/ds[0] - np.square(centroid) 
            std_deviation = np.sqrt(variance)

            for ind in range(len(data_sample)):
                point = data_sample[ind].astype(np.float)
                md = mahalanobis_distance(point, centroid, std_deviation)
                curr_min_dist, curr_min_ind = min_distance_per_sample[ind]
                if (curr_min_dist < 0 or curr_min_dist > md) and md < threshold:
                    min_distance_per_sample[ind] = (md, i)
                    points_to_remove.append(ind)

        for ind in points_to_remove:
            curr_min_dist, curr_min_ind = min_distance_per_sample[ind]
            ds = discard_set[curr_min_ind]
            ds[0] += 1
            ds[1] += data_sample[ind].astype(np.float)
            ds[2] += np.square(data_sample[ind].astype(np.float))
        
        data_sample = [data_sample[n].astype(np.float) for n in range(len(data_sample)) if n not in points_to_remove]

        new_cs = [[0, 0, 0] for i in range(NUMBER_OF_CLUSTERS)]
        kmeans.fit(data_sample)
        for ind in range(len(data_sample)):
            cluster = kmeans.labels_[ind]
            new_cs[cluster][0] += 1
            new_cs[cluster][1] += data_sample[ind]
            new_cs[cluster][2] += np.square(data_sample[ind])

        # get the outlier points and add them to the retained set       
        for ind in range(len(data_sample)):
            cluster = kmeans.labels_[ind]
            cs = new_cs[cluster]
            centroid = cs[1]/cs[0]
            variance = cs[2]/cs[0] + np.square(centroid)
            std_deviation = np.sqrt(variance)

            md = mahalanobis_distance(data_sample[ind], centroid, std_deviation)
            if md > threshold:
                # Point is an outlier and doesn't belong in this cluster
                cs[0] -= 1
                cs[1] -= data_sample[ind]
                cs[2] -= np.square(data_sample[ind])
                retained_set.append(data_sample[ind])

        # Join the newly formed CS to old CS if possible, if not it becomes a new cluster in CS
        # We consider it possible if the cluster is within MD range
        for new_cluster in new_cs:
            found_match = False
            for cs in compression_set:
                old_centroid = cs[1]/cs[0]
                old_variance = cs[2]/cs[0] + np.square(old_centroid)
                old_std_dev = np.sqrt(old_variance)

                new_centroid = new_cluster[1]/new_cluster[0]
                md = mahalanobis_distance(new_centroid, old_centroid, old_std_dev)
                if md > threshold:
                    found_match = True
                    cs[0] += new_cluster[0]
                    cs[1] += new_cluster[1]
                    cs[2] += new_cluster[2]
                    break
            if not found_match:
                compression_set.append(new_cluster)

        # Now see if it's possible to join any CS to the DS
        min_distance_per_cluster = [(-1, -1) for i in range(len(compression_set))]
        cs_to_remove = []
        
        for i in range(NUMBER_OF_CLUSTERS):
            ds = discard_set[i]
            centroid = ds[1]/ds[0]
            variance = ds[2]/ds[0] - np.square(centroid) 
            std_deviation = np.sqrt(variance)

            for ind in range(len(compression_set)):
                comp = compression_set[ind]
                point = comp[1]/comp[0]
                md = mahalanobis_distance(point, centroid, std_deviation)
                curr_min_dist, curr_min_ind = min_distance_per_cluster[ind]
                if (curr_min_dist < 0 or curr_min_dist > md) and md < threshold:
                    min_distance_per_cluster[ind] = (md, i)
                    cs_to_remove.append(ind)

        for ind in cs_to_remove:
            curr_min_dist, curr_min_ind = min_distance_per_cluster[ind]
            ds = discard_set[curr_min_ind]
            ds[0] += compression_set[ind][0]
            ds[1] += compression_set[ind][1]
            ds[2] += compression_set[ind][2]

    #Finally get the new centroids from the CS and the RS and join them to the neares centroid in DS
    cs_centroids = [cs[1]/cs[0] for cs in compression_set]
    retained_set += cs_centroids

    min_distance_per_point = [(-1, -1) for i in range(len(retained_set))]
    for i in range(NUMBER_OF_CLUSTERS):
        ds = discard_set[i]
        centroid = ds[1]/ds[0]
        variance = ds[2]/ds[0] - np.square(centroid) 
        std_deviation = np.sqrt(variance)
        for ind in range(len(retained_set)):
            point = retained_set[ind]

            md = mahalanobis_distance(point, centroid, std_deviation)
            curr_min_dist, curr_min_ind = min_distance_per_point[ind]
            if curr_min_dist < 0 or curr_min_dist > md:
                min_distance_per_point[ind] = (md, i)
    
    for i in range(len(min_distance_per_point)):
        point = cs_centroids[i]
        _, centroid = min_distance_per_point[i]
        ds = discard_set[centroid]
        ds[0] += 1
        ds[1] += point
        ds[2] += np.square(point)

    with open("bfr_results.json", "w") as r:
        json.dump(discard_set, r)

    sc.stop()