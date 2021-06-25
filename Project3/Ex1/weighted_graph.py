import networkx as nx
import scipy as sp
import numpy as np
from sklearn.metrics import jaccard_score
import sys
import matplotlib.pyplot as plt
import json

PATH_DATA = "data/facebook/"

users = ["0", "107", "348", "414", "686", "698", "1684", "1912", "3437", "3980"]

user_eigenvectors = {}
user_eigenvalues = {}
user_features = {}

def jaccard(user1, user2):
    return jaccard_score(user1, user2)

for u in users:
    print(u)
    G = nx.Graph()

    with open(PATH_DATA + u + ".feat", "r") as feat_reader:
        for line in feat_reader:
            ls = line.rstrip().split(" ")
            user_features[ls[0]] = np.asarray(ls[1:], dtype=np.intc)

    with open(PATH_DATA + u +".circles") as friend_reader:
        for line in friend_reader:
            ls = line.rstrip().split("\t")
            for n in ls[1:]:    
                G.add_node(int(n))

    with open(PATH_DATA + u + ".edges") as friend_reader:
        for line in friend_reader:
            line = line.rstrip()
            a, b = line.split(" ")
            G.add_edge(int(a), int(b), weight=jaccard(user_features[a], user_features[b]))
    
    A = nx.adjacency_matrix(G)
    eigenvalues, eigenvectors = np.linalg.eigh(A.todense())

    user_eigenvalues[u] = eigenvalues
    user_eigenvectors[u] = eigenvectors

with open("weighted-user-eigenvalues-eigenvectors.json", "w") as results:
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
    plt.savefig(u + "_eigengap_weight_graph.png")
    plt.clf()
