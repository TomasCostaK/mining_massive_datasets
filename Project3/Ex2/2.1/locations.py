from pyspark import SparkContext
from pyspark.streaming import StreamingContext
import sys
from random import random, randint

# Most popular N
N_MOST = 5
SAMPLE_SIZE = 1000

# Create a local StreamingContext with two working thread and batch interval of user given seconds
sc = SparkContext(appName="LocationsStream")
ssc = StreamingContext(sc, int(sys.argv[1]))
ssc.checkpoint("locations")

# Visual improvement for development
def quiet_logging(context):
    logger = sc._jvm.org.apache.log4j
    logger.LogManager.getLogger("org"). setLevel( logger.Level.ERROR )
    logger.LogManager.getLogger("akka").setLevel( logger.Level.ERROR )

# http://spark.apache.org/docs/latest/api/python/reference/api/pyspark.streaming.DStream.updateStateByKey.html
def reservoirSampling(incoming_stream, prev_stream):
    # First iterations, we add the whole stream as an empty array and a count of 0 elements
    if prev_stream == None:
        prev_stream = ([], 0)

    # Sample is the array of the previous stream
    sample = prev_stream[0]
    n = prev_stream[1]

    for i in range(len(incoming_stream)):
        n_value = incoming_stream[i]
        if len(sample) < SAMPLE_SIZE:
            sample.append(n_value)
        else:
            # New size will be the count of previous stream + the index of the given value
            n += i
            # Reservoir sampling formula
            p = len(sample) * 1.0 / n
            r = random()
            if r <= p:
                # Replace an old value in the sample by the new one, uniform probability
                replaced_idx = randint(0, len(sample)-1)
                sample[replaced_idx] = n_value
                print("Replacing [%d] --> %s" % (replaced_idx, n_value))
    return (sample, n)

def getOrderedCounts(rdd):

    try:  
        counts = rdd.flatMap(lambda location: (location[1][0]))\
                    .map(lambda x: (x,1))\
                    .reduceByKey(lambda a, b: a+b)

        batch_counts = counts.sortBy(lambda x:x[1],ascending=False)
        
        return batch_counts

    except:
        return rdd

# Examples taken from: http://spark.apache.org/docs/latest/streaming-programming-guide.html
if __name__ == "__main__":
    quiet_logging(sc)

    # Create a DStream that will connect to the data file given
    # We need to run the program and only then, insert the files we want to count locations into this directory
    lines = ssc.socketTextStream("localhost", 9999)

    # Split each line into pairs (Timestamp, location)
    pairs = lines.map(lambda line: line.split("\t"))

    # We always use the same key so we can update by key
    pre_sampled_data = pairs.map(lambda location: (0,location[1]))

    sampled_data = pre_sampled_data.updateStateByKey(reservoirSampling)

    ordered_counts = sampled_data.transform(getOrderedCounts)

    ordered_counts.pprint(N_MOST)

    ssc.start()             # Start the computation
    ssc.awaitTermination()  # Wait for the computation to terminate
