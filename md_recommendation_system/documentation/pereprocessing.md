# Data Preprocessing
## Preprocessor
A preprocessor should process interaction, item and user data.  
Current preprcoessors:  

- PersonalizePreprocessor  
    - Interaction data process: Since the duplicate logs occur in our DB, an import step is to combine the duplicate logs in watch_history.
        If the difference of timestamp is  less than `sec window` in config settings, we combine two logs and set the timestamp
        by the smaller one.  
    - Item data process: AWS personalize data can deal with categories and description data. The categories data should be seperated by `|`
    and description text should be seperated by a whitespace.  
    - User data process: Since the AWS personalize recommenders(Because you watched X and Top picks for you) don't use user data,  
    we don't process this.  
    - Finally, we map or column names for AWS personalize (all caps).

# Usage
```
python run_preprocessing.py --cfg_path <your yaml file>
```
## Preprocessor Summary

|Preprocessor Name| Interaction process| Item process | User process| Usage|
|--- | --- | --- | --- | --- |
|PersonalizePreprocessor| Remove duplicate logs | Categories and description process| None| AWS personalize, MDTV recommenders|