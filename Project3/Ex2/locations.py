from pyspark import SparkContext
from pyspark.streaming import StreamingContext
import sys

# Visual improvement for development
def quiet_logging(context):
    logger = sc._jvm.org.apache.log4j
    logger.LogManager.getLogger("org"). setLevel( logger.Level.ERROR )
    logger.LogManager.getLogger("akka").setLevel( logger.Level.ERROR )

# Examples taken from: http://spark.apache.org/docs/latest/streaming-programming-guide.html
if __name__ == "__main__":
    # Create a local StreamingContext with two working thread and batch interval of user given seconds
    sc = SparkContext(appName="LocationsStream")
    ssc = StreamingContext(sc, int(sys.argv[2]))
    quiet_logging(sc)

    # Create a DStream that will connect to the data file given
    # We need to run the program and only then, insert the files we want to count locations into this directory
    lines = ssc.textFileStream(sys.argv[1])

    # Split each line into pairs (Timestamp, location)
    pairs = lines.map(lambda line: line.split("\t"))

    counts = pairs.map(lambda location: (location[1], 1))\
                    .reduceByKey(lambda a, b: a+b)\

    counts.transform(
        lambda x: sc.parallelize(x.take(5))
    )

    counts.pprint()

    ssc.start()             # Start the computation
    ssc.awaitTermination()  # Wait for the computation to terminate