from pyspark import SparkContext
from pyspark.sql import SparkSession
from datetime import datetime
import re
import logging
import sys
import collections

# Este support deve ser 1000, mas
SUPPORT_THRESHOLD = 6

STD_LIFT_THRESHOLD = 0.2

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

def get_support(disease, confidence_df):
    x = disease.rfind(",")
    key = disease[:x]
    return confidence_df.filter(confidence_df.Disease == key).collect()[0].Count

def get_probability(disease, baskets_df):
    from pyspark.sql.functions import array_contains
    x = disease.rfind(",")
    key = disease[x+1:]
    return baskets_df.filter(array_contains(baskets_df.DeseasesList, key)).count()/baskets_df.count()

def get_std_lift(disease, dlift, baskets_df, diseases_df):
    p_group = get_support(disease, diseases_df)
    p_d = get_probability(disease, baskets_df)
    max_val = max(p_group + p_d - 1, 1/baskets_df.count())
    numerator = dlift - max_val/(p_group*p_d)
    denominator = 1/(p_group*p_d) - max_val/(p_group*p_d)
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

    baskets_df = baskets.toDF(["User", "DeseasesList"])

    diseases_support = baskets.flatMap(lambda line: [(code, 1) for code in line[1]]) \
                                .reduceByKey(lambda a, b: a+b).filter(lambda line: line[1] > SUPPORT_THRESHOLD)

    diseases_support_df = diseases_support.toDF(["Disease", "Count"])
    
    filtered_diseases = diseases_support.map(lambda line: line[0]).collect()

    bigrams_support = baskets.flatMap(lambda line: build_bigram(line, filtered_diseases))\
                    .reduceByKey(lambda a, b: a+b)\
                    .filter(lambda line: line[1] > SUPPORT_THRESHOLD)

    # Results formatting
    if k == 2:
        association_rules = {key:[value] for key, value in bigrams_support.collect()}
        print(len(association_rules))

        for key in association_rules:
            #Confidence level
            association_rules[key][0] /= get_support(key, diseases_support_df)
            
            #Interest level
            association_rules[key].append(association_rules[key][0] - get_probability(key, baskets_df))

            #Lift
            association_rules[key].append(association_rules[key][0]/get_probability(key, baskets_df))

            #Std lift
            association_rules[key].append(get_std_lift(key, association_rules[key][2], baskets_df, diseases_support_df))
            print(key)
        
        association_rules = association_rules.parallelize().filter(lambda line: line[4] > STD_LIFT_THRESHOLD)\
                                        .sortBy(lambda line: line[4])\
                                        .toDF(["Pair", "Confidence", "Interest", "Lift", "Standard Lift"])
        association_rules.write.format("csv").save("{0}/{1}".format(sys.argv[3], "Association_Rules.csv"))
        sc.stop()
        exit(0)
        
    filtered_bigrams = bigrams.map(lambda line: line[0]).collect()

    trigrams = baskets.flatMap(lambda line: build_trigram(line, filtered_diseases, filtered_bigrams))\
                        .reduceByKey(lambda a, b: a+b) \
                        .filter(lambda line: line[1] > SUPPORT_THRESHOLD)

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    trigrams.saveAsTextFile("{0}/{1}".format(sys.argv[3], format_time))
    sc.stop()