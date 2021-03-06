from pyspark import SparkContext
from datetime import datetime
import operator
import re
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(-1)
    sc = SparkContext(appName="SparkIntro_WordCount")

    textfile = sc.textFile(sys.argv[1])
    occurences = textfile.flatMap(lambda line: re.split(r'[^\w]+', line.lower())) \
                            .filter(lambda w: len(w)>3) \
                            .map(lambda word : (word[0], word)) \
                            .distinct() \
                            .aggregateByKey(0,lambda v1,v2: v1+1,operator.add) \
                            .sortBy(lambda p: p[1], False)

    format_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    occurences.saveAsTextFile("{0}/{1}".format(sys.argv[2], format_time))
    sc.stop()