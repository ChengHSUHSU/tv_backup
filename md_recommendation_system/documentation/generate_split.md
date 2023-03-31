# Data split
## Generate a data split set for experiments
A data split can be composed by train / val /testing (according the timestamp).  
The latest 20% data is treated as val and testing data (then randomly select val and testing data with ratio 1:1).
Finally the split ratio of train:val:testing is 8:1:1.

The split data is a dictionay which is saved in `./dataset/split` named by `split_<tag>`.
If a tag is not set, set tag as datatime automatically.

Structure of split data is placed like:
```
dict:
    key (str): The set name or `all_item_ids`.
    value (dict):
        key (str): The user id.
        value (dict):
            key (str): `ITEMS` or `TIMESTAMP`.
            value (list): The list of integers (or float32).
```

## To generate data split
```
python ./dataset/generate_split.py <interaction_dir> <item_data_path> --tag <tag>
```
