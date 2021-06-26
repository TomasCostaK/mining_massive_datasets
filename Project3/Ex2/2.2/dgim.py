from pyspark import SparkContext
from pyspark.streaming import StreamingContext
import sys

# Most popular N
N_MOST = 10
C_VAR = 10**-6

# Create a local StreamingContext with two working thread and batch interval of user given seconds
sc = SparkContext(appName="LocationsStream")
ssc = StreamingContext(sc, int(sys.argv[1]))
ssc.checkpoint("mentions")

# Visual improvement for development
def quiet_logging(context):
    logger = sc._jvm.org.apache.log4j
    logger.LogManager.getLogger("org"). setLevel( logger.Level.ERROR )
    logger.LogManager.getLogger("akka").setLevel( logger.Level.ERROR )

# http://spark.apache.org/docs/latest/api/python/reference/api/pyspark.streaming.DStream.updateStateByKey.html
def dgim(incoming_stream, prev_stream):
    # First iterations, we add the whole stream as an empty array and a count of 0 elements
    if prev_stream == None:
        prev_stream = ('1',0)

    for elem in incoming_stream:
        print(elem)

    return ('1', 100)

def getOrderedCounts(rdd):
    # We grab the two lists, and then map them into a better struct (value, weight)
    counts_dict = rdd.map(lambda x: x[1])\
                    .filter(lambda x: x[0]=='1')
    
    return counts_dict

# Examples taken from: http://spark.apache.org/docs/latest/streaming-programming-guide.html
if __name__ == "__main__":
    # Most popular N

    quiet_logging(sc)

    # Create a DStream that will connect to the data file given
    # We need to run the program and only then, insert the files we want to count locations into this directory
    lines = ssc.socketTextStream("localhost", 9999)

    # Split each line into pairs (Timestamp, location)
    pairs = lines.map(lambda line: line)

    # We always use the same key so we can update by key
    pre_sampled_data = pairs.map(lambda bit: (0,bit)) \

    sampled_data = pre_sampled_data.updateStateByKey(dgim)

    ordered_counts = sampled_data.transform(getOrderedCounts)

    ordered_counts.pprint(1)

    ssc.start()             # Start the computation
    ssc.awaitTermination()  # Wait for the computation to terminate
