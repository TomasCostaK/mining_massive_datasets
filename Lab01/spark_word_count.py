from pyspark import SparkContext
from datetime import datetime
import re
import sys

def parse_bigrams(line):
    bigrams = []
    unigrams = re.split(r'[^\w]+', line.lower())
    for i in range(len(unigrams) - 1):
        if len(unigrams[i])<3 or len(unigrams[i+1])<3:
            continue     
        bigram = unigrams[i] + "," + unigrams[i+1]
        bigrams.append(bigram)
    return bigrams

if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(-1)
        
    sc = SparkContext(appName="SparkIntro_WordCount")

    textfile = sc.textFile(sys.argv[1])
    bigrams = textfile.flatMap(parse_bigrams) \
                            .filter(lambda w: len(w)>3) \
                            .map(lambda bigram : (bigram, 1)) \
                            .reduceByKey(lambda a,b: a+b) \
                            .sortBy(lambda p: p[1], False)
    """
    bigrams.map(lambda word : (word, 1)) \
                .reduceByKey(lambda a,b: a+b) \
                .sortBy(lambda p: p[1], False)
    """

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    bigrams.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()