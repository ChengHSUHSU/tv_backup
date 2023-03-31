# Trainer
A trainer is flexible to design, but please follow the rules:
1. `fit` method is neccessary for a trainer.
2. Since we utilize `mlflow` to manage our experiemnts,  
so please set the exp_name, exp_idx and args to initialize a trainer.

# The current trainers
## SupervisedTrainer
Train model with ground truth tasks

- NCFNetworkTrainer  
  - Using neural collaborative filtering (NCF) to fit `user personalize` task.

## ClusterTuner
Tune a clustering method to get the best parameters

- MDTVHDBSCANTuner  
  - The MDTV user cluster Tuner which is used to fit the `user tags` task.


# Usage (how to run a experiments)
```
python run_exp.py --exp_cfg_path <your yaml file path>
```