from pyspark import SparkContext
from datetime import datetime
import re
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(-1)
        
    sc = SparkContext(appName="SparkIntro_WordCount")

    textfile = sc.textFile(sys.argv[1])
    bigrams = textfile.flatMap(lambda line: re.split(r'[^\w]+', line.lower())) \
                            .filter(lambda w: len(w)>3) \
                            .map(lambda tup: (tuple(x) for x in zip(tup[1],tup[1:]))) \
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