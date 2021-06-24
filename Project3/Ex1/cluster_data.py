from sklearn.cluster import KMeans
from sklearn.metrics.cluster import adjusted_rand_score
import json

num_nodes_user = {"0": 14,
                  "107": 5,
                  "348": 7,
                  "414": 8,
                  "686": 3,
                  "698": 11,
                  "1684": 16,
                  "1912": 6,
                  "3437": 7,
                  "3980": 10}

PATH_DATA = "data/facebook/"

with open("user-eigenvalues-eigenvectors.json", "r") as reader:
    data = json.load(reader)

user_score = {}

for u in num_nodes_user:

    with open(u+".circles","r") as reader:
        

    kmeans = KMeans(n_clusters=num_nodes_user[u])

    eigenvectors = data[u][1]

    kmeans = kmeans.fit(eigenvectors[:30])

    print(kmeans.labels_)
