# Exercise 2.1 - Batch sized interval streams
Get the most seen locations in each timestamp

## How to Run
Start the stream generator:

````python3
    python3 generator_stream.py <interval in seconds> <file> // Example: python3 generator_stream.py 20 data/locations.csv
````
Then, on another terminal: (intervals should be the same)  

````python3
    spark-submit locations.py <interval in seconds> // Example: spark-submit locations.py 20
````