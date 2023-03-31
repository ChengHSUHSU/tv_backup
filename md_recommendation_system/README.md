# Md recommendation system
This project is compose of preprocessing, training and inferencing phase:  
- [Preprocessing](documentation/pereprocessing.md) deals with interatcion, item and user data.
- [Generate data split](documentation/generate_split.md) (training/validation/testing).
- A [training](documenatation/trainers.md) stage can be conduct multiple experiments according our settings.  
- [Inference](documenatation/predictors) can perform a ensemble method and different topic recommendation (personalize / video similarity).

## Framework

![Alt text](images/framework.png?raw=true "Framework")


The following graph presents the correspondings of objects in each phases:  
![Alt text](images/objects_correspondings.png?raw=true "Corresponding of objects")


## How to install

1. Clone this repository
    ```
    git clone https://gitlab.com/mathewko0711/md_recommendation_system.git
    cd md_recommendation_system
    ```
2. We recommend you creat a virtual environment to start a project:
    ```
    python -m venv <your vitual environment name> --system-site-packages
    ```
3. Install the requirements for python packages.
    ```
    pip install -r requirements.txt
    ```

## Start your experiments
1. Go to the recommender folder to start your experiments:
    ```
    cd recommender
    ```
2. Before staring a experiment, we need preprocess our raw data:
    ```
    python run_preprocessing.py --cfg_path <your yaml file>
    ```
    For example:
    ```
    python run_preprocessing.py --cfg_path ./preprocessing/settings/md_tv_setting.yaml
    ```
3. Generate a train-val-test split for your preprocessed data (supervied tasks are required)
    ```
    python ./dataset/generate_split.py <interaction_dir> <item_data_path> --tag <tag> 
    ```

    For example:
    ```
    python ./dataset/generate_split.py ./data/preprocessed_data/ ./data/preprocessed_data/item_2022_09_27.csv --tag <tag> 
    ```
4. Start our experiemnts
    ```
    python run_exp.py <your yaml file path>
    ```

    For example:
    ```
    python run_exp.py ./training/exp_cfgs/ncf.yaml
    ```

## Inference

- Personalize (item-user recommender):
    - Rank all items which are not wathced by a specific user.
- Tag Recommender:
    - Rank prefered item tags for a specific user.
- Tag Personalize:
    - After training a item-user recommender and a tag recommender (user clustering), we combine two recommenders and get Tag personalize service.
- Similar-item recommender:
    - Recommend a simialr items for a specific item.

    ```
    python predict.py <your yaml files>
    ```

    For example:

    ```
    python predict.py ./inference/predict_cfgs/tag_personalize.yaml
    ```







