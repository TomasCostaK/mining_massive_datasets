# Exercise 2.2 - Batch sized interval streams
DGIM on a bit stream

## Help
To evaluate the queries, we test for these values = [5, 10, 15, 20, 50]
## How to Run
Start the stream generator:

````python3
    python3 generator_stream.py
````
Then, on another terminal:  

````python3
    spark-submit dgim.py <interval in seconds> // Example: spark-submit dgim.py 20
````