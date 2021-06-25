# Assignment 3 - Spectral Clustering Data

## Structure of Files

- **user_graph**: Python program that will take the dataset and create a graph, from which it will generate the Laplacian Matrix, the corresponding eigenvectors and eigenvalues (which will be written for future analysis) and graph the eigengaps.

- **cluster_data**: Python program that has a constant dictionary that maps the user to the assigned number of clusters, which will be used to perform the KMeans and calculate the Adjusted Rand Score

- **weighted_graph**: Python program similar to user_graph.py, with the key difference that instead of generating a Laplacian Matrix, it will create a Adjacency Matrix using the weights of the edges instead of 1's; as requested, these weights are calculated using the Jaccard distance and the .feat files.

- **cluster_weighted_data**: Python program basically identical to the cluster_data.py but with the key difference of taking different number of clusters

## Results

### Using the Laplace Matrix

0 with score 0.21230860402005403
107 with score 0.009938694829923413
348 with score 0.1237202275454755
414 with score 0.22171223672257726
686 with score -0.0017786133491774652
698 with score 0.33013458162668224
1684 with score 0.29539397410458373
1912 with score 0.0022293449969475972
3437 with score 0.002505319521339904
3980 with score -0.0792554157517212

### Using the Weighted Adjacency Matrix

0 with score 0.005860154666146147
107 with score -0.09489472728971199
348 with score -0.03563637439607153
414 with score -0.014149378824667913
686 with score -0.02929059053776972
698 with score 0.010324350350905351
1684 with score -0.040484595215734824
1912 with score -0.03763050445088277
3437 with score -0.009443324081057296
3980 with score -0.006195133327485168
