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

    kmeans = KMeans(n_clusters=num_nodes_user[u])

    eigenvectors = []
    for e in data[u][1]:
        eigenvectors.append(e[:30])

    kmeans = kmeans.fit(eigenvectors)

    user_circles = []
    user_control = set()

    with open(PATH_DATA + u +".circles") as friend_reader:
        for line in friend_reader:
            ls = line.rstrip().split("\t")
            for n in ls[1:]:
                if n not in user_control:
                    user_circles.append(ls[0])
                    user_control.add(n)

    print(u, "has", len(user_circles))

    solution = kmeans.labels_[:len(user_circles)]

    user_score[u] = adjusted_rand_score(solution, user_circles)

    print(u, "with score", adjusted_rand_score(solution, user_circles))

print(user_score)
