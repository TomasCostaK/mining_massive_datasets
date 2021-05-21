from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from datetime import datetime
from time import time
import logging
import collections
import math
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
    v1 = np.nan_to_num(vector1)
    v1[1 != np.nan] -= mean1
    
    mean2 = np.nanmean(vector2)
    v2 = np.nan_to_num(vector2)
    v2[v2 != np.nan] -= mean2
    #
    cosine_sim = np.dot(v1, v2) / np.sqrt(np.dot(v1, v1) * np.dot(v2, v2))
    # The similarity has no direction, so we define it in both movies
    return cosine_sim

def recommend_movies(users, matrix, target_movie, target_user):
    # Iteratve over every user and find k most similar pairs
    target_user = str(target_user)
    target_movie = str(target_movie)
    user_flag = -1
    try:
        for user, ratings in users.collect():
            if user == target_user:
                user_flag = 1
                most_similar = []
                movies_watched = [movie for movie, rating in ratings]
                # only evaluate the movies he's seen
                movie_vector = matrix[target_movie]
                for second_movie, second_vector in matrix.items():
                    if second_movie != target_movie and second_movie in movies_watched:
                        most_similar.append((target_movie,second_movie,calculate_similarity(movie_vector, second_vector)))
                
                most_similar = sorted(most_similar, key=lambda x:x[2], reverse=True)[:NEIGHBOUR_SIZE]
                break
    except:
        print("Error, recommendation not possible")
        sys.exit(1)
    
    """ # Example run for movie 1, user 1
    [('1', '2054', 0.8144142372372292), ('1', '2018', 0.8097298933985878), ('1', '596', 0.8093382199015737)]
    Matrix:  [4.0, 5.0, 5.0]
    Recommended rating for movie 1 by user 1 == 4.7
    """
    if user_flag == 1:
        return float(sum([ sim*matrix[id2][int(target_user)-1] for id1, id2, sim in most_similar]) / sum([sim for id1, id2, sim in most_similar]))

    return 

def evaluate_model(data, users, matrix):
    # evaluate one by one and check if the rating is equal to
    ratings_list = []
    rec_ratings_list = []
    for line in data:
        usr, movie_id, rating, unused = line
        rec_rating = recommend_movies(users, matrix, movie_id, usr)
        ratings_list.append(float(rating))
        rec_ratings_list.append(rec_rating)

    rmse = math.sqrt(sum([(rec_ratings_list[i]-ratings_list[i])**2 for i in range(len(ratings_list))])/sum([rec_ratings_list[i] for i in range(len(rec_ratings_list))]))
    print("RMSE ==", rmse)
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

    evaluate_model(ratings_data.take(100), users, movies_matrix)
    #recommendations = recommend_movies(users, movies_matrix,1,1)

    sc.stop()