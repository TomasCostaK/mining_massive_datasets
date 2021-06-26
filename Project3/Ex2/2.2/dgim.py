from pyspark import SparkContext
from pyspark.streaming import StreamingContext
import sys
import math

# Create a local StreamingContext with two working thread and batch interval of user given seconds
sc = SparkContext(appName="LocationsStream")
ssc = StreamingContext(sc, int(sys.argv[1]))
ssc.checkpoint("dgim")

# Bucket definition according to: http://infolab.stanford.edu/~ullman/mmds/ch4.pdf?fbclid=IwAR00gMaMWSqUsEAlfAZciQcj75dDFeeNI-Vs47aOcnp5Xd53Dn_3sqwMtls (Page 152)
class Bucket:
    def __init__(self, ts, ones):
        self.ones = ones
        self.final_timestamp = ts

    # We use this func to merge two buckets and its ones count    
    def __add__(self, second_bucket):
        self.final_timestamp = max(self.final_timestamp, second_bucket.final_timestamp)
        self.ones += second_bucket.ones
        return self

# We will use this queue struct to merge buckets, segments adapted from: https://github.com/simondolle/dgim/blob/master/dgim/dgim.py
class Queue:
    def __init__(self):
        self.buckets = [[]]

    # push a bucket to the stack
    def push(self, b):
        self.buckets[0].insert(0, b)
        
        # merge buckets
        for i in range(len(self.buckets)):
            if len(self.buckets[i]) > 2:
                try:
                    self.buckets[i+1].insert(0, self.buckets[i].pop() + self.buckets[i].pop())
                except:
                    # We need to compensate for the index error
                    self.buckets.append([])
                    self.buckets[i+1].insert(0, self.buckets[i].pop() + self.buckets[i].pop())

    def evaluate(self, end_ts):
        ones = 0
        last_bucket = 0
        for b1 in self.buckets:
            for bucket in b1:
                # if its the last timestamp, we can get half of its ones count
                if bucket.final_timestamp < end_ts:
                    #print("Bucket window failed: ", bucket)
                    break
                else:
                    ones += bucket.ones
                    last_bucket = bucket.ones
        ones += math.floor(last_bucket / 2)
        return ones

# Visual improvement for development
def quiet_logging(context):
    logger = sc._jvm.org.apache.log4j
    logger.LogManager.getLogger("org"). setLevel( logger.Level.ERROR )
    logger.LogManager.getLogger("akka").setLevel( logger.Level.ERROR )

# http://spark.apache.org/docs/latest/api/python/reference/api/pyspark.streaming.DStream.updateStateByKey.html
def dgim(incoming_stream, prev_stream):
    # Every new stream we evaluate the given elements
    # There's no need to store on the stream the last bits, since this algorithm still applies but is harder to evaluate
    samples = []
    queue = Queue()
    # Resets every new stream
    timestamp = 0
    for elem in incoming_stream:
        if elem=='1':
            queue.push(Bucket(timestamp, 1))
        # Even if we dont push to the bucket, the timestamp still increases
        timestamp += 1

    # Searching for same given values: []
    windows = [5, 25, 50, 100, 256]
    for window_size in windows:
        result = queue.evaluate(timestamp - window_size)
        samples.append((window_size, result))
    
    return samples

def getOrderedCounts(rdd):
    # We grab the two lists, and then map them into a better struct (value, weight)
    counts_dict = rdd.flatMap(lambda x: x[1])    
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

    print("\nEvaluating Queries: (Query_Window, N_Ones)")
    ordered_counts.pprint(5)

    ssc.start()             # Start the computation
    ssc.awaitTermination()  # Wait for the computation to terminate
