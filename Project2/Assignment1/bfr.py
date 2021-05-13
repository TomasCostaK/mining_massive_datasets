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

if __name__ == "__main__":
    sc = SparkContext(appName="Assignment1")
    spark = SparkSession(sc)
    sc.setLogLevel("WARN")

    textfile = sc.textFile(FEATURES)

    data_features = textfile.zipWithIndex().\
                    filter(lambda x: x[1] > 3).\
                    map(lambda x: x[0].split(','))
    kmeans = KMeans(n_clusters=NUMBER_OF_CLUSTERS)

    discard_set = []
    compression_set = set()
    retained_set = set()

    k_clusters = data_features.takeSample(False, NUMBER_OF_CLUSTERS)
    data_features = data_features.filter(lambda x: x[0] not in [k[0] for k in k_clusters)
    k_clusters = [k[1:] for k in k_clusters]

    while not data_features.empty():
        data_sample = data_features.takeSample(False, SAMPLE_SIZE)
        data_features = data_features.filter(lambda x: x[0] not in [k[0] for k in data_sample)
        data_sample = np.array([k[1:] for k in data_sample]).astype(np.float)
        
        N=100
        SUM = np.sum(data_sample, axis=0)
        SUMSQ = np.sum(np.square(data_sample), axis=0)

        cluster_size = 2*len(data_sample[0]) + 1
        centroid = SUM/N
        variance = SUMSQ/N - np.square(SUM/N)
        std_deviation = np.sqrt(variance)


    sc.stop()