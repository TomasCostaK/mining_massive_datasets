from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from datetime import datetime
from time import time
import re
import logging
import sys
import collections

# Este support deve ser 1000, mas
SUPPORT_THRESHOLD = 1000

STD_LIFT_THRESHOLD = 0.2

def build_bigram(basket, filtered_diseases):
    """ Function to build a bigram based on the basket and the diseases with more than the supported threshold
    """
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
    """ Function to build a trigram based on the basket and the diseases with more than the supported threshold
    """
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

def get_support(disease, confidence_df):
    """Function to get the number of occurences the group I occurs in the dataset"""
    x = disease.rfind(",")
    key = disease[:x]
    return confidence_df.filter(confidence_df.Disease == key).collect()[0].Count

def get_probability(disease, baskets_df):
    """Function to get the probability of a disease j in the baskets"""
    from pyspark.sql.functions import array_contains
    x = disease.rfind(",")
    key = disease[x+1:]
    return baskets_df.filter(array_contains(baskets_df.DeseasesList, key)).count()/baskets_df.count()

def get_std_lift(dsupp, dprob, dlift, basketscount):
    """Function to get calculate the standard lift based on the support and probability calculated previously"""
    max_val = max(dsupp + dprob - 1, 1/basketscount)
    numerator = dlift - max_val/(dsupp*dprob)
    denominator = 1/(dsupp*dprob) - max_val/(dsupp*dprob)
    return numerator/denominator

if __name__ == "__main__":
    if len(sys.argv) != 4:
        exit(-1)

    k = int(sys.argv[1])

    if k != 2 and k != 3: exit(-1)
    
    # Starting context and opening file in command line
    sc = SparkContext(appName="Assignment1")
    spark = SparkSession(sc)
    sc.setLogLevel("ERROR")
    textfile = sc.textFile(sys.argv[2])
    
    # Mapping patient as bucket to several diseases
    baskets = textfile.map(lambda line: line.split(",")) \
                        .map(lambda pair: (pair[2],[pair[4]])) \
                        .reduceByKey(lambda a,b: a+b)

    # Converting the baskets RDD to a Dataframe and saving it to RAM storage for easier access
    baskets_df = baskets.toDF(["User", "DeseasesList"]).cache().persist(StorageLevel.MEMORY_ONLY)

    # Considering th baskets RDD, we filter to only get diseases with a support above the defined threshold, in this case 1000
    diseases_support = baskets.flatMap(lambda line: [(code, 1) for code in line[1]]) \
                                .reduceByKey(lambda a, b: a+b).filter(lambda line: line[1] > SUPPORT_THRESHOLD)

    # Again converting the RDD to a Dataframe and saving it to cache
    diseases_support_df = diseases_support.toDF(["Disease", "Count"]).cache().persist(StorageLevel.MEMORY_ONLY)
    
    # Get the list of diseases from the Diseases RDD
    filtered_diseases = diseases_support.map(lambda line: line[0]).collect()

    # Build the collection of Bigrams from the baskets, and filtering again to the support threshold
    bigrams_support = baskets.flatMap(lambda line: build_bigram(line, filtered_diseases))\
                    .reduceByKey(lambda a, b: a+b)\
                    .filter(lambda line: line[1] > SUPPORT_THRESHOLD)

    # If k=2 our job is done, we get the association rules and write them down to files
    if k == 2:
        association_rules = {key:[value] for key, value in bigrams_support.collect()}
        list_assoc_rules = []

        for key in association_rules:
            #Confidence level
            supp = get_support(key, diseases_support_df)
            prob = get_probability(key, baskets_df)
            association_rules[key][0] /= supp
            #Interest level
            association_rules[key].append(association_rules[key][0] - prob)
            #Lift
            association_rules[key].append(association_rules[key][0]/prob)
            #Std lift
            association_rules[key].append(get_std_lift(supp, prob, association_rules[key][2], baskets_df.count()))
            list_assoc_rules.append([key] + association_rules[key])
        
        association_rules = sc.parallelize(list_assoc_rules)
        association_rules = association_rules.filter(lambda line: line[4] > STD_LIFT_THRESHOLD)\
                                        .sortBy(lambda line: line[4])

        bigrams_support_top10 = bigrams_support.sortBy(lambda line: line[1], False).take(10)

        with open("{0}/Top 10 Bigrams.csv".format(sys.argv[3]), "w") as filewrite:
            filewrite.write("\n".join([b[0] for b in bigrams_support_top10]))

        format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        association_rules.saveAsTextFile("{0}/Association Rules {1}".format(sys.argv[3], format_time))
        sc.stop()
        exit(0)
   
    # Following the same logic as before, we get the filtered bigrams and save them in a list, build the trigrams out of those
    # and create check the association rules before writing
    
    filtered_bigrams = bigrams_support.map(lambda line: line[0]).collect()

    trigrams_support = baskets.flatMap(lambda line: build_trigram(line, filtered_diseases, filtered_bigrams))\
                        .reduceByKey(lambda a, b: a+b) \
                        .filter(lambda line: line[1] > SUPPORT_THRESHOLD)
    
    bigrams_support_df = bigrams_support.toDF(["Disease", "Count"]).cache().persist(StorageLevel.MEMORY_ONLY)

    association_rules = {key:[value] for key, value in trigrams_support.collect()}
    list_assoc_rules = []

    for key in association_rules:
        #Confidence level
        supp = get_support(key, bigrams_support_df)
        prob = get_probability(key, baskets_df)
        association_rules[key][0] /= supp
        #Interest level
        association_rules[key].append(association_rules[key][0] - prob)
        #Lift
        association_rules[key].append(association_rules[key][0]/prob)
        #Std lift
        association_rules[key].append(get_std_lift(supp, prob, association_rules[key][2], baskets_df.count()))
        list_assoc_rules.append([key] + association_rules[key])
    
    association_rules = sc.parallelize(list_assoc_rules)
    association_rules = association_rules.filter(lambda line: line[4] > STD_LIFT_THRESHOLD)\
                                    .sortBy(lambda line: line[4])

    trigrams_support_top10 = trigrams_support.sortBy(lambda line: line[1], False).take(10)

    with open("{0}/Top 10 Trigrams.csv".format(sys.argv[3]), "w") as filewrite:
        filewrite.write("\n".join([t[0] for t in trigrams_support_top10]))

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    association_rules.saveAsTextFile("{0}/Association Rules {1}".format(sys.argv[3], format_time))
    sc.stop()
