from pyspark import SparkContext
from datetime import datetime
import operator
import hashlib
import time
import re
import sys
import random

# Picking the biggest prime that coems after N shingles (used function to calculate for the given dataset) 
# https://www.calculatorsoup.com/calculators/math/prime-number-calculator.php
LARGE_PRIME = 75874811
RANDOM_ARRAY = [(random.randint(0,500), random.randint(0,500)) for i in range(0,100)]

# Hashing of the string into an int, so we maintain order in shingles
def str_to_hashint(string):
    return abs(hash(string)) % (10 ** 8)

# Definition of hash functions, a and b are random in both functions
def h1(x,a,b): 
    h1_array = []
    for value in x:
        h1_array.append((a*str_to_hashint(value) + b) % LARGE_PRIME)
    return min(h1_array)

# Turn document plot into set of shingles
def shingling(document,k=9):
    shingles = set()
    plot_shingles = re.split('',document[1].lower())
    for idx in range(len(plot_shingles)-k):
        shingle = ''.join(plot_shingles[idx:idx+k])
        shingles.add(shingle)
    
    return document[0],shingles

# This function receives a set of Shingles and should return a signature matrix
# This was we generate the 100 hash functions, a clever way
def minhash(document, k=100):
    x = document[1]
    signature_matrix = []
    for i in range(0,k):
        a,b = RANDOM_ARRAY[i]
        h = h1(x,a,b)
        signature_matrix.append(h)
    return document[0],signature_matrix

# Function used to Hash a given band into a bucket
def hash_lsh(band): 
    h1_array = []
    for value in band:
        h1_array.append((421*value + 16) % 1013)
    return min(h1_array)

# LSH, receives signature_matrix, devolves candidate pairs
def lsh(documents, r=5, b=20):
    buckets = []
    signature = documents[1]
    # iterate over each column (movie) and calculate the hash based on a given band portion
    # This band portion is given by the rows in each band
    for idx in range(0,b):
        if idx*r > len(signature): break 
        max_id = min(idx * r + r, len(signature))
        bucket = hash_lsh(signature[idx*r:max_id])
        buckets.append(bucket)

    return documents[0],buckets

def test_lsh(signature_matrix, r=5, b=20):
    buckets = {}
    candidate_pairs = []
    # iterate over each column (movie) and calculate the hash based on a given band portion
    # This band portion is given by the rows in each band
    for signature in signature_matrix.items():
        doc, bucket = lsh(signature, r, b)
        for doc2, bucket_list in buckets.items():
            for i in range(len(bucket)):
                if bucket_list[i] == bucket[i]: # This means its a candidate pair
                    similar_pair = similarity(signature[1], signature_matrix[doc2])
                    candidate_pairs.append((doc,doc2,similar_pair))
                    break  
        buckets[doc] = bucket

    # This returns candidate_pairs
    return candidate_pairs

# Given a pair, return its similarity, calculated with 1-jaccard distance
def similarity(sig1, sig2): 
    intersection = len(list(set(sig1).intersection(sig2)))
    union = (len(sig1) + len(sig2)) - intersection
    jacc = float(intersection) / union
    return jacc

def calculate_fp_rate(matrix, similar_pairs):
    fp = 0
    fn = 0
    for pair in similar_pairs:
        doc1, doc2, sim1 = pair
        shingles1 = matrix[doc1]
        shingles2 = matrix[doc2]
        sm = similarity(shingles1,shingles2)
        if sim1 > 0.8:
            print("Doc1: %s Doc2: %s Sim1: %f, CalcSim: %f" % (doc1, doc2, sim1, sm))

        if sim1 > 0.8 and sm < 0.8: fp+=1
        if sim1 < 0.8 and sm > 0.8: fn+=1

    return (fp/len(similar_pairs), fn/len(similar_pairs))


# This function evaluates
def return_similar(target_movie, movies):
    similar_movies = []
    for movie in movies:
        if (target_movie == movie[0]) and movie[2]>0.8 and movie[2]<0.98:
            similar_movies.append(movie[0])
        if (target_movie == movie[1]) and movie[2]>0.8 and movie[2]<0.98:
            similar_movies.append(movie[1])
    return similar_movies

if __name__ == "__main__":
    if len(sys.argv) != 5:
        exit(-1)

    try:
        r = int(sys.argv[1])
        b = int(sys.argv[2])
    except:
        print("Usage: movies.py <int:rows> <int:bands>")

    # Usando esta funçao: https://www.wolframalpha.com/input/?i=%281-0.8%5Ex%29%5E%28100%2Fx%29
    # Chegamos à conclusao que a melhor escolha para o b=5 e r=20, dado que b x r = 100

    sc = SparkContext(appName="MovieRecommendation")
    log4jLogger = sc._jvm.org.apache.log4j
    LOGGER = log4jLogger.LogManager.getLogger("RESULTS")
    LOGGER.info("pyspark script logger initialized")

    time_start = time.time()
    # Initial pipeline of shingling, minhashing and then performing LSH
    textfile = sc.textFile(sys.argv[3])
    signatures = textfile.map(lambda line: re.split('\t', line.lower())) \
                            .map(shingling)

    min_hashes = signatures.map(minhash)
    time_end = time.time()
    LOGGER.info("Time Elapsed for Signatures: %fs\n" % (time_end-time_start))

    time_start = time.time()
    signatures_matrix = { doc:buckets for doc,buckets in min_hashes.collect() }
    time_end = time.time()
    LOGGER.info("Time Elapsed for Creating Matrix: %fs\n" % (time_end-time_start))

    time_start = time.time()
    similar_pairs = test_lsh(signatures_matrix, r, b)
    similar_pairs_rdd = sc.parallelize(similar_pairs) \
                            .sortBy(lambda line: -line[2])
                            
    time_end = time.time()
    LOGGER.info("Time Elapsed for Similar Pairs: %fs\n" % (time_end-time_start))

    # Function calling Ex 2.2, returning similar movies but not copies to a given movie
    time_start = time.time()
    similar = return_similar('23890098', similar_pairs)
    LOGGER.info("Movies Similar to %s found in %fs: %s\n" % ('23890098', time.time()- time_start, similar))

    fp_rate, fn_rate = calculate_fp_rate(signatures_matrix,similar_pairs)
    LOGGER.info("\tFP Rate: %f \n\tFN Rate: %f\n" % (fp_rate, fn_rate))

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    similar_pairs_rdd.saveAsTextFile("{0}/{1}".format(sys.argv[4], format_time))
    sc.stop()