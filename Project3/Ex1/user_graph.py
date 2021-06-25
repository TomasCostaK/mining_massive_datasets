import networkx as nx
import scipy as sp
import numpy as np
import sys
import matplotlib.pyplot as plt
import json

PATH_DATA = "data/facebook/"

users = ["0", "107", "348", "414", "686", "698", "1684", "1912", "3437", "3980"]

user_eigenvectors = {}
user_eigenvalues = {}

for u in users:
    G = nx.Graph()
    user_counter = 0

    with open(PATH_DATA + u +".circles") as friend_reader:
        for line in friend_reader:
            ls = line.rstrip().split("\t")
            for n in ls[1:]:    
                G.add_node(int(n))
                user_counter+=1

    with open(PATH_DATA + u + ".edges") as friend_reader:
        for line in friend_reader:
            line = line.rstrip()
            a, b = line.split(" ")
            G.add_edge(int(a), int(b))
    
    A = nx.laplacian_matrix(G)
    eigenvalues, eigenvectors = np.linalg.eigh(A.todense())

    print(len(eigenvalues), user_counter, A.todense().shape)

    user_eigenvalues[u] = eigenvalues
    user_eigenvectors[u] = eigenvectors

with open("user-eigenvalues-eigenvectors.json", "w") as results:
    user_results = {}
    for u in user_eigenvalues: user_results[u] = [user_eigenvalues[u].tolist(), user_eigenvectors[u].tolist()]
    json.dump(user_results, results)

## Eigengap
user_eigengap = {}

for u in users:
    user_eigenvalues[u] = sorted(user_eigenvalues[u])
    user_eigengap[u] = np.diff(user_eigenvalues[u])
    plt.plot(range(30), user_eigengap[u][:30], marker='o')
    plt.xlabel("N Clusters")
    plt.ylabel("Eigen Gap")
    plt.savefig(u + "_eigengap_graph.png")
    plt.clf()
