from pyspark import SparkContext
from datetime import datetime
import re
import logging
import sys
import collections

# Este support deve ser 1000, mas
SUPPORT_THRESHOLD = 6

def build_bigram(basket, filtered_diseases):
    diseases = list(basket[1])
    list_of_bigrams = []
    for i in range(len(diseases)):
        d1 = diseases[i]
        if d1 not in filtered_diseases: continue
        for j in range(i+1, len(diseases)):
            d2 = diseases[j]
            if d2 not in filtered_diseases: continue
            list_of_bigrams.append((d1 + "," + d2, 1))
    return list_of_bigrams



def build_trigram(basket, filtered_diseases, filtered_bigrams):
    diseases = list(basket[1])
    list_of_trigrams = []
    for i in range(len(diseases)):
        d1 = diseases[i]
        if d1 not in filtered_diseases: continue
        for j in range(i+1, len(diseases)):
            d2 = diseases[j]
            if d2 not in filtered_diseases: continue
            if d1 + "," + d2 not in filtered_bigrams: continue
            for k in range(j+1, len(diseases)):
                d3 = diseases[k]
                if d3 not in filtered_diseases: continue
                if d1 + "," + d3 not in filtered_bigrams or d2 + "," + d3 not in filtered_bigrams: continue
                list_of_trigrams.append((d1 + "," + d2 + "," + d3, 1))
    return list_of_trigrams            

if __name__ == "__main__":
    if len(sys.argv) != 4:
        exit(-1)

    k = int(sys.argv[1])

    if k != 2 and k != 3: exit(-1)
    
    # Starting context and opening file in command line
    sc = SparkContext(appName="Assignment1")
    textfile = sc.textFile(sys.argv[2])
    
    # Mapping patient as bucket to several diseases
    baskets = textfile.map(lambda line: line.split(",")) \
                        .map(lambda pair: (pair[2],pair[4])) \
                        .groupByKey()

    filtered_diseases = baskets.flatMap(lambda line: [(code, 1) for code in line[1]]) \
                                .reduceByKey(lambda a, b: a+b) \
                                .filter(lambda line: line[1] > SUPPORT_THRESHOLD) \
                                .map(lambda line: line[0]).collect()

    bigrams = baskets.flatMap(lambda line: build_bigram(line, filtered_diseases))\
                    .reduceByKey(lambda a, b: a+b)

    # Results formatting
    if k == 2:
        format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        bigrams.saveAsTextFile("{0}/{1}".format(sys.argv[3], format_time))
        sc.stop()
        exit(0)
        
    filtered_bigrams = bigrams.filter(lambda line: line[1] > SUPPORT_THRESHOLD).map(lambda line: line[0]).collect()

    trigrams = baskets.flatMap(lambda line: build_trigram(line, filtered_diseases, filtered_bigrams))\
                        .reduceByKey(lambda a, b: a+b)

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    trigrams.saveAsTextFile("{0}/{1}".format(sys.argv[3], format_time))
    sc.stop()