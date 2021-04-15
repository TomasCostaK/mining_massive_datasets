from pyspark import SparkContext
from datetime import datetime
import operator
import hashlib
import re
import sys

# Picking the biggest prime that coems after N shingles (used function to calculate for the given dataset) 
# https://www.calculatorsoup.com/calculators/math/prime-number-calculator.php
LARGE_PRIME = 75874811

# Hashing of the string into an int, so we maintain order in shingles
def str_to_hashint(string):
    return abs(hash(string)) % (10 ** 8)

# Definition of hash functions, a and b are random in both functions
def h1(x): 
    h1_array = []
    for value in x:
        h1_array.append((521*str_to_hashint(value)) % LARGE_PRIME)
    return min(h1_array)

def h2(x):
    h2_array = []
    for value in x:
        h2_array.append((225*str_to_hashint(value )+ 623) % LARGE_PRIME)
    return min(h2_array)

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
        h = h1(x) + i * h2(x)
        signature_matrix.append(h)
    return document[0],signature_matrix

# Function used to Hash a given band into a bucket
def hash_lsh(band): 
    h1_array = []
    for value in band:
        h1_array.append((421*value + 16) % LARGE_PRIME)
    return min(h1_array)

# LSH, receives signature_matrix, devolves candidate pairs
def lsh(documents, r=5, b=20):
    buckets = []
    signature = documents[1]
    # iterate over each column (movie) and calculate the hash based on a given band portion
    # This band portion is given by the rows in each band
    for band in range(0,len(signature),r):
        bucket = hash_lsh(signature[band:band+r])
        buckets.append(bucket)

    return documents[0],buckets

# Given a list of documents in the same bucket, yield pairwise tuples
def evaluate_candidates(documents):
    docs = list(documents[1])
    candidates = set()
    for i in range(len(docs)):
        for j in range(i+1, len(docs)):
            if docs[i] != docs[j]:
                candidates.add((docs[i], docs[j]))
    return candidates

# Given a pair, return its similarity, calculated with 1-jaccard distance
def similarity(pairs):
    for pair in pairs:
        print("pair: ", pair)
    return pairs

if __name__ == "__main__":
    if len(sys.argv) != 5:
        exit(-1)

    try:
        r = int(sys.argv[1])
        b = int(sys.argv[2])
    except:
        print("Usage: movies.py <int:rows> <int:bands>")

    sc = SparkContext(appName="MovieRecommendation")

    # Initial pipeline of shingling, minhashing and then performing LSH
    textfile = sc.textFile(sys.argv[3])
    signatures = textfile.map(lambda line: re.split('\t', line.lower())) \
                            .map(shingling) \
                            .map(minhash)
    
    lsh = signatures.map(lambda j: lsh(j, r, b))
    
    # This way we will have Buckets - > list of movies that hit that bucket
    candidate_pairs = lsh.flatMap(lambda line: [(code, line[0]) for code in line[1]]) \
                                .groupByKey() \

    print(candidate_pairs.take(10))

    # Since we now have the candidate pairs, which only appear in similar buckets, we will perform pairwise comparisons with their respective signature matrix 
    # filter to remove all empty tuples and duplicates 
    similar_pairs = candidate_pairs.map(evaluate_candidates) \
                                    .filter(lambda l: len(l)>0) \
                                    .map(similarity)
    
    """
    min1 = minhash(['joao ','joana','robot','cao q'])
    min2 = minhash(['joana','raqet','morde'])
    print("Minhash1: ", min1)
    print("Minhash2: ", min2)

    intersection = len(list(set(min1).intersection(min2)))
    union = (len(min1) + len(min2)) - intersection

    jacc = float(intersection) / union

    print("Similarity: ",jacc)
    """

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    similar_pairs.saveAsTextFile("{0}/{1}".format(sys.argv[4], format_time))
    sc.stop()