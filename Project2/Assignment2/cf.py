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
    movies_matrix = {}
    ratings = movies_ratings.collect()

    for movie_idx, ratings_movie in ratings:
        # Less calculations if it's placed here, calculate the needed mean and ratings vector
        vector1 = np.full(num_users, np.nan)
        for idx, rating in ratings_movie: vector1[int(idx)-1] = rating
        #vector1 = np.subtract(vector1, vector1.nanmean())
        movies_matrix[movie_idx] = vector1

    return movies_matrix

def calculate_similarity(vector1, vector2):
    # only calculate means here, so we dont lose actual ratings on movies for next step
    mean1 = np.nanmean(vector1)
    vector1[vector1 != np.nan] -= mean1
    vector1 = np.nan_to_num(vector1)
    
    mean2 = np.nanmean(vector2)
    vector2[vector2 != np.nan] -= mean2
    vector2 = np.nan_to_num(vector2)

    #
    cosine_sim = np.dot(vector1, vector2) / np.sqrt(np.dot(vector1, vector1) * np.dot(vector2, vector2))
    # The similarity has no direction, so we define it in both movies
    return cosine_sim,mean1,mean2

def recommend_movies(users, matrix, target_movie, target_user):
    # Iteratve over every user and find k most similar pairs
    target_user = str(target_user)
    target_movie = str(target_movie)
    user_flag = -1
    for user, ratings in users.collect():
        if user == target_user:
            user_flag = 1
            most_similar = []
            movies_watched = [movie for movie, rating in ratings]
            for movie_id, movie_vector in matrix.items():
                # only evaluate the movies he's seen
                if movie_id == target_movie:
                    for second_movie, second_vector in matrix.items():
                        if second_movie != movie_id and second_movie in movies_watched:
                            most_similar.append((movie_id,second_movie,calculate_similarity(movie_vector, second_vector)))
            
            most_similar = sorted(most_similar, key=lambda x:x[2][0], reverse=True)[:NEIGHBOUR_SIZE]
    
    # Calculate weighted average
    # [('1', '500', 0.21971312123163245), ('1', '3671', 0.20316307157814495), ('1', '1270', 0.18870086378261838)]
    if user_flag == 1:
        print("Matrix: ", [ matrix[id2][int(target_user)-1] for id1, id2, sim in most_similar])
        soma = 0
        recommended_rating = float(sum([ sim*matrix[id2][int(target_user)-1] for id1, id2, sim in most_similar]) / sum([sim for id1, id2, sim in most_similar]))
        print("Recommended rating for movie %s by user %s == %.1f" % (target_movie, target_user, recommended_rating))
    else:
        print("User not found, cant recommend him movies")

"""
def recommend_movies(users, matrix):
    # Iteratve over every user and find k most similar pairs
    user_recommendations = collections.defaultdict(lambda: [])
    for user, ratings in users.collect():
        most_similar = []
        movies_watched = [movie for movie, rating in ratings]
        for movie_id, movie_vector in matrix.items():
            # only evaluate the movies he's seen
            if movie_id not in movies_watched:
                for second_movie, second_vector in matrix.items():
                    if second_movie != movie_id and second_movie in movies_watched:
                        most_similar.append((movie_id,second_movie,calculate_similarity(movie_vector, second_vector)))
        
        most_similar = sorted(most_similar, key=lambda x:x[2], reverse=True)[:NEIGHBOUR_SIZE]
        print(most_similar)
"""

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
    num_users = users.distinct().count()

    #print("-----------------------------------------\n Num of users is: %d" % (num_users))

    ratings = ratings_data.map(lambda tokens: (tokens[1],(tokens[0],tokens[2]))) \
                                    .groupByKey() \
                                    .mapValues(list) \
                                    .cache()

    movies_matrix = similar_pairs(ratings, num_users)

    recommendations = recommend_movies(users, movies_matrix,1,1)

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    similar.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()