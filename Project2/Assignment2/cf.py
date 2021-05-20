from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from datetime import datetime
from time import time
import logging
import collections
import numpy as np
import sys
import os

import csv

DATA_LOCATION = sys.argv[1] # this is the ratings csv
RATINGS_LOCATION = DATA_LOCATION + "/ratings.csv"
MOVIES_LOCATION = DATA_LOCATION + "/movies.csv"

NEIGHBOUR_SIZE = 3

def similar_pairs(movies_ratings, num_users):
    similar_pairs = []
    ratings = movies_ratings.collect()

    for movie1_idx in range(len(ratings)-1):
        # Less calculations if it's placed here, calculate the needed mean and ratings vector
        movie1, ratings1 = ratings[movie1_idx]
        vector1 = np.zeros(num_users)
        for idx, rating in ratings1: vector1[int(idx)] = rating
        vector1 = np.subtract(vector1, vector1.mean())
        
        for movie2_idx in range(movie1_idx, len(ratings)):
            # Pair we are currently analysing
            # Repeat previous steps for vector2
            movie2, ratings2 = ratings[movie2_idx]
            vector2 = np.zeros(num_users)
            for idx, rating in ratings2: vector2[int(idx)] = rating

            # using this for centered cosine/ pearson
            vector2 = np.subtract(vector2, vector2.mean())
            
            cosine_sim = np.dot(vector1, vector2) / np.sqrt(np.dot(vector1, vector1) * np.dot(vector2, vector2))
            # The similarity has no direction, so we define it in both movies
            similar_pairs.append((movie1,movie2,cosine_sim))

    return similar_pairs

def recommend_movies(users, pairs):
    # Iteratve over every user and find k most similar pairs
    for user, ratings in users.collect():
        most_similar = [movie_idx for movie_idx, movie_idx2, sim in sorted(pairs) if movie_idx1 in ratingsdouser and movie_idx2 in ratingsdouser][NEIGHBOUR_SIZE]

if __name__ == "__main__":
    sc = SparkContext(appName="CF_Recommendation")
    spark = SparkSession(sc)
    sc.setLogLevel("WARN")

    ratings_raw_data = sc.textFile(RATINGS_LOCATION)
    ratings_header = ratings_raw_data.take(1)[0]

    ratings_data = ratings_raw_data.filter(lambda line: line!=ratings_header)   \
                                    .map(lambda line: line.split(","))         

    users = ratings_data.map(lambda tokens: (tokens[0],(tokens[1], tokens[2]))) \
                                    .groupByKey()
    num_users = users.distinct() \
                                    .count()

    #print("-----------------------------------------\n Num of users is: %d" % (num_users))

    ratings = ratings_data.map(lambda tokens: (tokens[1],(tokens[0],tokens[2]))) \
                                    .groupByKey() \
                                    .mapValues(list) \
                                    .cache()

    similar = similar_pairs(ratings, num_users+1)

    recommendations = recommend_movies(users, similar)

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    similar.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()