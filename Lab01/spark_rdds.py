from pyspark import SparkContext
from datetime import datetime
import re
import sys

def print_parallel_data(sc):
    data = [1, 2, 3, 4, 5]
    distData = sc.parallelize(data)
    new_data = distData.take(100)
    for string in new_data:
        print("Element: %d" % (string))

def more_rdd(sc):
    accum = sc.accumulator(0)
    sc.parallelize([1, 2, 3, 4]).foreach(lambda x: accum.add(x))
    print(accum.value) # should be 10

if __name__ == "__main__":        
    sc = SparkContext(appName="SparkIntro_WordCount")

    #print_parallel_data(sc)
    more_rdd(sc)

    sc.stop()