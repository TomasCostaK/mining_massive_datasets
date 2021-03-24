from pyspark import SparkContext
from datetime import datetime
import re
import logging
import sys
import collections

# Este support deve ser 1000, mas
SUPPORT_THRESHOLD = 6

def preprocess_data(line):
    # here we reorder the data that came in csv format
    fields = re.split(',' ,line.lower())
    #for i in range(len(fields) - 1):
    single_case = (fields[2], fields[4])# code for the patient
    return single_case

def filter_baskets(baskets):
    code_map = collections.defaultdict(lambda: 0)

    for bucket in baskets.collect():
        patient, codes = bucket
        codes_array = re.split(',', codes)
        for code in codes_array:
            code_map[code] += 1

    filtered_diseases = [ code for code,value in code_map.items() if value > SUPPORT_THRESHOLD ]
    return filtered_diseases

def frequent_items(baskets, filtered_diseases, k=2):
    baskets = baskets.collect()
    pair_items = collections.defaultdict(lambda: 0)

    # iterating over all baskets
    for basket in baskets:
        # iterate over one item in basket: "basket"
        baskets_array = re.split(",",basket[1])
        for disease1 in baskets_array:
            if disease1 not in filtered_diseases:
                print("%s is not frequent monotonicity" % (disease1))
                continue
            for disease2 in baskets_array:
                if disease1 != disease2 and disease2 in filtered_diseases: 
                    pair_items[disease1,disease2] += 1
    
    # case where k = 2 and the problem is solved
    if k == 2:
        return sorted(pair_items.items(), key=lambda x: x[1])
            

if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(-1)
    
    # Starting context and opening file in command line
    sc = SparkContext(appName="Assignment1")
    textfile = sc.textFile(sys.argv[1])
    
    # Mapping patient as bucket to several diseases
    baskets = textfile.map(preprocess_data) \
                            .reduceByKey(lambda a,b: a+","+b) 

    # Filter the baskets, 1st step of the A-Priori algorithm
    filtered_diseases = filter_baskets(baskets)

    # 2nd step of A-Priori Algorithm
    frequent_items = frequent_items(baskets, filtered_diseases)
    for item in frequent_items:
        print(item)

    baskets.filter(lambda a: len(re.split(',', a[1]))>SUPPORT_THRESHOLD) \
                            .sortBy(lambda p: p[1], False)

    # Results formatting
    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    baskets.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()