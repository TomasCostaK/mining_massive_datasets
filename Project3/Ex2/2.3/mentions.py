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
def decayingWindow(incoming_stream, prev_stream):
    # First iterations, we add the whole stream as an empty array and a count of 0 elements
    if prev_stream == None:
        prev_stream = [[], []]

    # Sample is the array of the previous stream
    distinct_elems = set(incoming_stream)

    sample_values = []
    sample_weights = []

    # Iterate every new user on the stream, calculate weights for each
    for elem in distinct_elems:
        count = 1 if incoming_stream[0] == elem else 0

        # According to: https://www.youtube.com/watch?v=Erw-Mi1AlXk&t=766s
        # We only add the 0 or 1 in the posterior results
        for inc_elem_idx in range(len(incoming_stream)):
            if inc_elem_idx == 0: 
                count = (count) * (1-C_VAR)
                continue
        
            count = (count) * (1-C_VAR) + (1 if elem == incoming_stream[inc_elem_idx] else 0)

        if elem not in sample_values:
            sample_values.append(elem)
            sample_weights.append(count)
        else:
            idx = sample_values.index(elem)
            sample_weights[idx] += count
    
    return [sample_values,sample_weights]

def getOrderedCounts(rdd):
    # We grab the two lists, and then map them into a better struct (value, weight)
    counts_dict = rdd.map(lambda x: x[1]) \
            .map(lambda x: [(x[0][i], x[1][i]) for i in range(len(x[0]))]) \
            .flatMap(lambda x: x)
    
    ordered_dict = counts_dict.sortBy(lambda x: x[1],ascending=False)
    return ordered_dict

# Examples taken from: http://spark.apache.org/docs/latest/streaming-programming-guide.html
if __name__ == "__main__":
    # Most popular N

    quiet_logging(sc)

    # Create a DStream that will connect to the data file given
    # We need to run the program and only then, insert the files we want to count locations into this directory
    lines = ssc.socketTextStream("localhost", 9999)

    # Split each line into pairs (Timestamp, location)
    pairs = lines.map(lambda line: line.split("\t"))

    # We always use the same key so we can update by key
    pre_sampled_data = pairs.map(lambda location: (0,location[1])) \

    sampled_data = pre_sampled_data.updateStateByKey(decayingWindow)

    ordered_counts = sampled_data.transform(getOrderedCounts)

    ordered_counts.pprint(N_MOST)

    ssc.start()             # Start the computation
    ssc.awaitTermination()  # Wait for the computation to terminate
