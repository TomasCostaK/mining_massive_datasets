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

# This function receives a set of Shingles and should return a signature matrix
# This was we generate the 100 hash functions, a clever way
def minhash(document, k=100):
    x = document[1]
    signature_matrix = []
    for i in range(0,k):
        h = h1(x) + i * h2(x)
        signature_matrix.append(h)
    return document[0],signature_matrix

def shingling(document,k=9):
    shingles = set()
    plot_shingles = re.split('',document[1].lower())
    for idx in range(len(plot_shingles)-k):
        shingle = ''.join(plot_shingles[idx:idx+k])
        shingles.add(shingle)
    
    return document[0],shingles

if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(-1)
    sc = SparkContext(appName="MovieRecommendation")

    textfile = sc.textFile(sys.argv[1])
    occurences = textfile.map(lambda line: re.split('\t', line.lower())) \
                            .map(shingling) \
                            .map(minhash)

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
    occurences.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()