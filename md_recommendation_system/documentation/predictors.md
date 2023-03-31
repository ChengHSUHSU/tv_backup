# Recommender
A recommender is flexible to design, but please follow the rules:
1. `load_split_data` and `predict` methods are neccessary for a predictor
2. Since the inferencing process is various, we tidy up the inferencing function in predict.py. If you create your own predictor,
please write the inferencing code in predict.py
3. We manage each predictor by using yaml file which contain model arguments and inference settings. Please create a yaml file once you create a customized predictor.

# The current recommenders
- UserItemRecommender  
Predict item preference for a specific user.
  - NCFRecommender  
    - Use neural collaborative filtering (NCF) to fit `user personalize` task.
    - Optional settings:
      - predict_n_items: Recommend n items for a user.

- TagRecommender  
Predict prefered tags for a specific user (user tag).
  - HDBSCANTagRecommender  
    - Use HDBSCAN to cluster the users. We use interaction data to build user vector (one-hot depends on items).  
    We get tags for each culster by calculating the tag ratio:  
  ```math
  R = \frac {\{\text{item with this tag} | item \in C\}} {\text{\# item with this tag}}
  ```
    - Optional settings:
      - Topk: Predict topk user tags.

- TagPersonalize  
Predict user personalize for specific tags.
  - This recommender combines 2 recommenders: A UserItemRecommender and TagRecommender.  
  The inference process:  
    1. Use TagRecommender to get user tags for a specific user.
    2. Get all items with these tags.
    3. For each tag, we rank the items with this tag for a specific user by using UserItemRecommender.
  - Optional settings:
    - predict_n_items: Recommend n items for a user.
    - Topk: Predict topk user tags.

- MDTVCosineItemRecommender  
Predict similar items for a specific item.
  - Use categories (one-hot) and description (tf-idf) data to get similarity for each item-item pair.

# Usage (how to use a recommender)
```
python predict.py --cfg_path <your yaml file>
```