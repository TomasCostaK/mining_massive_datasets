from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from datetime import datetime
from time import time
import re
import logging
import sys
import collections
import csv
from sklearn.cluster import AgglomerativeClustering
from sklearn.neighbors import NearestCentroid
import numpy as np
import json

DATA_LOCATION = "../../fma_metadata/"
TRACKS = DATA_LOCATION + "tracks.csv"
FEATURES = DATA_LOCATION + "features.csv"

def avg(l):
    return sum(list(l))/len(l)

if __name__ == "__main__":
    sc = SparkContext(appName="Assignment1")
    spark = SparkSession(sc)
    sc.setLogLevel("WARN")

    textfile = sc.textFile(TRACKS)
    data_small_ids = textfile.zipWithIndex().\
                    filter(lambda x: x[1] > 2).\
                    map(lambda x: x[0]).\
                    mapPartitions(lambda x: csv.reader(x, delimiter=',', quotechar='"')).\
                    filter(lambda x: len(x) == 53).\
                    filter(lambda x: x[32] == 'small').\
                    map(lambda x: x[0]).collect()
    
    data_small_ids = set(data_small_ids)

    features_to_remove = [ 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191]
    
    data_small_features = sc.textFile(FEATURES).zipWithIndex().\
                    filter(lambda x: x[1] > 3).\
                    map(lambda x: x[0].split(',')).\
                    filter(lambda x: x[0] in data_small_ids).\
                    map(lambda x: x[1:])

    X = np.array(data_small_features.collect())
    X = np.delete(X, features_to_remove, 1)

    print("Start training")

    data_per_cluster = {}

    for i in range(8, 17):
        node_per_label = {}
        radius_per_label = {}
        diameter_per_label = {}
        clustering = AgglomerativeClustering(n_clusters=i, compute_distances=True).fit(X)
        clf = NearestCentroid()
        clf.fit(X, clustering.labels_)
        
        for l in range(len(X)):
            label = clustering.labels_[l]
            if label not in node_per_label: 
                node_per_label[label] = []
                diameter_per_label[label] = 0
                radius_per_label[label] = 0
            node_per_label[label].append(X[l])

        # Calculate diameter
        for label in node_per_label:
            node_per_label[label] = np.array(node_per_label[label]).astype(np.float)
            for n1 in range(len(node_per_label[label])):
                for n2 in range(n1+1, len(node_per_label[label])):
                    d = np.linalg.norm(node_per_label[label][n1] - node_per_label[label][n2])
                    if d > diameter_per_label[label]: diameter_per_label[label] = d

        # Calculate radius
        for label in node_per_label:
            for n1 in node_per_label[label]:
                r = np.linalg.norm(n1 - clf.centroids_[label])
                if r > radius_per_label[label]: radius_per_label[label] = r

        density_per_label = {label: len(node_per_label[label])/(radius_per_label[label]**2) for label in node_per_label}

        dc_results = [0] * i
        for label in node_per_label:
            dc_results[label] = [len(node_per_label[label]), np.sum(node_per_label[label], axis=0).tolist(), np.sum(np.square(node_per_label[label]), axis=0).tolist()  ]
        
        with open(f"results_{i}.json", "w") as r:
            json.dump(dc_results, r)

        data_per_cluster[i] = [
            min(radius_per_label.values()), max(radius_per_label.values()), avg(radius_per_label.values()),
            min(diameter_per_label.values()), max(diameter_per_label.values()), avg(diameter_per_label.values()),
            min(density_per_label.values()), max(density_per_label.values()), avg(density_per_label.values())
        ]

    with open(f"results.json", "w") as r:
        json.dump(data_per_cluster, r)
    sc.stop()