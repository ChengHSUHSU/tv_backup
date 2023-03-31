from abc import abstractmethod
from pymongo import MongoClient





class Genericdataloader(object):
    def __init__(self):
        print()

    @abstractmethod
    def query_data(self):
        pass

    @abstractmethod
    def run(self):
        pass



class RecDataLoader(Genericdataloader):
    def __init__(self, db_config, rk_config):
        # database
        database_name = rk_config['query_settings']['read']['database']
        self.db_read = MongoClient(**db_config\
                ['connect_settings']['read'])[database_name]
        # query_data_cfg
        self.query_data_cfg = rk_config['dataloader']['query_data']
        # run
        self.run()


    def query_data(self, data_category):
        # collect_name
        collect_name = self.query_data_cfg[data_category]['collect']
        # query data
        for _ in range(5):
            try:
                cl = list(self.db_read[collect_name].find({}))
                break
            except Exception as error_message:
                cl = []
                print(f'!!!{data_category}')
                #add_log_record(error_message, 'recommender', self.log_save_path)
        return cl


    def build_item2rank_item(self, item2item_cl):
        item2rank_item = dict()
        for record in item2item_cl:
            item2rank_item[record['ITEM_ID']] = record['ITEM_ID_RANK']
        return item2rank_item


    def build_item2info(self, item_cl):
        item2info = item_cl
        return item2info


    def build_user_history(self, meta_history_cl=None, history_cl=None):
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
            used_item = set()
            for i in range(max(len(history), len(meta_history))):
                if i < len(history) and history[i] not in used_item:
                    history_all.append(history[i])
                    used_item.add(history[i])
                if i < len(meta_history) and meta_history[i] not in used_item:
                    history_all.append(meta_history[i])
                    used_item.add(meta_history[i])
            if len(history_all) != 0:
                user_history = [{'USER_ID' : user, 'history' : history_all}] + user_history
        return user_history


    def run(self):
        # query recommend data
        # it spend 4.4 minate (item2item)
        item2item_cl = self.query_data(data_category='item2item')
        meta_history_cl = self.query_data(data_category='meta_history')
        history_cl = self.query_data(data_category='history')
        #item_cl = self.query_data(data_category='item')

        # build item2rank_item
        self.item2rank_item = self.build_item2rank_item(item2item_cl)

        # build user_history
        self.user_history = self.build_user_history(meta_history_cl, history_cl)

        # build item2info
        #self.item2info = self.build_item2info(item_cl)
        return 



