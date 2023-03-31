


import yaml
from tqdm import tqdm
from pymongo import MongoClient




def load_config(yaml_path):
    """load_config

    it can load yaml config and return 

    Args:
        yaml_path (str) : For example, "./config.yaml"
    """
    # pylint: disable=invalid-name
    # pylint: disable=unspecified-encoding
    with open(yaml_path, mode='r') as f:
        cfg = yaml.safe_load(f)
    return cfg


class MongoDBSession:
    def __init__(self, connect_settings):
        self.database_names = list(connect_settings.keys())
        self.connect_settings = connect_settings

    def init_db(self, db_name):
        self.db_ = MongoClient(**self.connect_settings[db_name])[db_name]
        print(f'ready db(={db_name})....')

    def query(self, collect_name=None, nosql_query={}, progress=False):
        if progress is False:
            return list(self.db_[collect_name].find(nosql_query))
        else:
            output = []
            for record in tqdm(self.db_[collect_name].find(nosql_query)):
                output.append(record)
            return output



def build_user_history(meta_history_cl=None, history_cl=None):
     # build user2history_info
    user2history_info = dict()
    for record in meta_history_cl + history_cl:
        user = record['USER_ID']
        if user not in user2history_info:
            user2history_info[user] = {'meta_history' : [], 'history' : []}
        if 'meta_history' in record:
            user2history_info[user]['meta_history'] = record['meta_history']
        if 'history' in record: 
            user2history_info[user]['history'] = record['history']
    # build user_history
    user_history = []
    for user, history_info in list(user2history_info.items()):
        history = history_info['history']
        meta_history = history_info['meta_history']
        history_all = []
        for i in range(max(len(history), len(meta_history))):
            if i < len(history):
                history_all.append(history[i])
            if i < len(meta_history):
                history_all.append(meta_history[i])
        if len(history_all) != 0:
            user_history = [{'USER_ID' : user, 'history' : history_all}] + user_history
    return user_history

