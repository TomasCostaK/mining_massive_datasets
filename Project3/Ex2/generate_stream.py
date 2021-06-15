import sys

if __name__ == "__main__":
    # Initialization of the variables
    interval = int(sys.argv[1])
    in_filename = sys.argv[2]
    out_filename = "unprocessed_data/data.txt"

    # Processing of the CSV
    input_f = open(in_filename,'rt')
    output_f = open(out_filename, 'w+')
    count = 0
    while True:
        count+=1
        line = input_f.readline()
        # stopping condiditon
        if not line:
            break
        timestamp, location = line.split("\t")
        print("Current timestamp: %s and current interval %d" % (timestamp, interval))
        
    # Close the files for no problems
    input_f.close()
    output_f.close()
