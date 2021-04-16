# Frequent itemsets and association rules between similar items

Two main goals:  
    - Using Spark to implement the A-Priori algorithm and LSH to find associations between diseases.  
    - Implement and apply LSH to identify similar movies based on their plots.

## Authors

[Tomás Costa](https://github.com/TomasCostaK) - 89016  
[Pedro Oliveira](https://github.com/PedroOliveiraPT) - 89156   

## How to Run
k can be equals to 2 or 3  
````spark
spark-submit conditions.py k data/conditions_small.csv result/
````