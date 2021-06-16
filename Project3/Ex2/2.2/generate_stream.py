import sys
import socket
import random

if __name__ == "__main__":
    # Initialization of the variables
    probability_1 = 0.2
    # Socket comms
    out_address = "localhost"
    out_port = 9998
    s = socket.socket()
    s.bind((out_address, out_port))
    s.listen(1)
    c, addr = s.accept()

    try:
        while True:
            random_n = random.uniform(0, 1)
            if random_n < probability_1:
                byte = '1\n'
            else:
                byte = '0\n'
            c.sendall(byte.encode('utf-8'))


    # Catch the KeyboardInterruption
    except:
        print("Closing gracefully")
        # Close the socket for no problems
        s.close()
        sys.exit(1)

    # Close the socket for no problems
    s.close()
