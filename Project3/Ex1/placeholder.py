import networkx as nx
import scipy as sp
import numpy as np
import sys

PATH_DATA = "data/facebook/"

users = ["0", "107", "348", "414", "686", "698", "1684", "1912", "3437", "3980"]

user_eigenvectors = {}
user_eigenvalues = {}

for u in users:
    G = nx.Graph()
    friend_circles = {}
    with open(PATH_DATA + u +".circles") as friend_reader:
        for line in friend_reader:
            ls = line.rstrip().split("\t")
            for n in ls[1:]:    
                G.add_node(int(n))

    maybe_notconn = False
    with open(PATH_DATA + u + ".edges") as friend_reader:
        for line in friend_reader:
            line = line.rstrip()
            a, b = line.split(" ")
            G.add_edge(int(a), int(b))
    
    A = nx.laplacian_matrix(G)
    eigenvalues, eigenvectors = np.linalg.eig(A.todense())
    user_eigenvalues[u] = eigenvalues
    user_eigenvectors[u] = eigenvectors

## Eigengap
user_eigengap = {}

for u in users:
    user_eigenvalues[u] = sorted(user_eigenvalues[u])
    user_eigengap[u] = []
    for num in range(1, len(user_eigenvalues[u])):
        user_eigengap[u].append(user_eigenvalues[u][num] - user_eigenvalues[u][num-1])

print(user_eigengap)