from pyspark import SparkContext
from datetime import datetime
import re
import sys

def preprocess_data(line):
    # here we reorder the data that came in csv format
    fields = re.split(',' ,line.lower())
    #for i in range(len(fields) - 1):
    single_case = (fields[2], fields[4])# code for the patient
    return single_case

if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(-1)
        
    sc = SparkContext(appName="Assignment1")

    textfile = sc.textFile(sys.argv[1])
    bigrams = textfile.map(preprocess_data) \
                            .reduceByKey(lambda a,b: a+","+b) \
                            .sortBy(lambda p: p[1], False)
    """
    bigrams.map(lambda word : (word, 1)) \
                .reduceByKey(lambda a,b: a+b) \
                .sortBy(lambda p: p[1], False)
    """

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    bigrams.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()