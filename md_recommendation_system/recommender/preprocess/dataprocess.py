"""A module for data process"""
import os
import json
import pytz
import random
from tqdm import tqdm
from datetime import datetime
from abc import abstractmethod
from pymongo import MongoClient
from utils import add_log_record
from query_sp import time_query_sp
from query_sp import item_query_sp
from query_sp import meta_history_query_sp



class Genericproccessor(object):
    """Generic process

    A data process consists 3 methods:
    1. build_interaction_data
    2. build_item_data
    3. build_user_data

    Args:
        user_data (dict): None.
        item_data (dict): None.
        interaction_data (dict): None.
        interaction_train_data (dict): None.
        interaction_val_data (dict): None.
    """
    def __init__(self):
        print()

    @abstractmethod
    def query_data(self):
        pass

    @abstractmethod
    def build_user_item_set(self):
        pass


    @abstractmethod
    def build_item_data(self):
        pass

    @abstractmethod
    def build_user_data(self):
        pass

    @abstractmethod
    def build_train_info(self):
        pass

    @abstractmethod
    def build_inference_info(self):
        pass





class PersonalizeProcessor(Genericproccessor):
    def __init__(self, db_config, rs_config):
        # database
        database_name = rs_config['query_settings']['read']['database']
        self.db_read = MongoClient(**db_config['connect_settings']['read'])[database_name]

        # query_data config
        self.query_data_cfg = rs_config['dataprocess']['query_data']

        # build_item_data config
        self.build_item_data_cfg = rs_config['dataprocess']['build_item_data']

        # train, val
        self.train_seq_limit = rs_config['dataprocess']['train_seq_limit']
        self.train_val_rate = rs_config['dataprocess']['train_val_rate']

        # query date (start, end)
        taipei = pytz.timezone('Asia/Taipei')
        query_start = rs_config['dataprocess']['query_start']
        query_end = rs_config['dataprocess']['query_end']

        query_start = taipei.localize(datetime.strptime(query_start, '%Y-%m-%d'))
        query_end = taipei.localize(datetime.strptime(query_end, '%Y-%m-%d'))
        self.query_start_tz = query_start.astimezone(pytz.utc)
        self.query_end_tz = query_end.astimezone(pytz.utc)

        # inference
        self.warm_rate = rs_config['dataprocess']['warm_rate']
        self.inference_topK = rs_config['dataprocess']['inference_topK']
        self.hard_pos_score = rs_config['dataprocess']['hard_pos_score']
        self.soft_pos_score = rs_config['dataprocess']['soft_pos_score']
        self.inference_bz = rs_config['dataprocess']['inference_batch_size']
        self.cold_inf_features = rs_config['dataprocess']['cold_inference']['features']
        self.warm_num = rs_config['dataprocess']['cold_inference']['warm_num']

        # topK (warm, cold)
        self.warm_topK = int(self.inference_topK * self.warm_rate)
        self.cold_topK = self.inference_topK - self.warm_topK

        # reindex
        self.idx_user = []
        self.idx_item = []
        self.user2idx = dict()
        self.item2idx = dict()
        self.user_set = set()
        self.item_set = set()
        self.warm_item_set = set()
        self.cold_item_set = set()
        
        # log path
        self.log_save_path = rs_config['log']['save_path']



    def query_data(self, data_category):
        # collect_name
        collect_name = self.query_data_cfg[data_category]['collect']
        # nosql_query
        query_sp = self.query_data_cfg[data_category]['query_sp']
        if query_sp is None:
            nosql_query = {}
        elif query_sp == 'time_query':
            time_query_column = self.query_data_cfg[data_category]['time_query_column']
            nosql_query = time_query_sp(\
                    time_query_column, self.query_start_tz, self.query_end_tz)
        # query data
        for _ in range(5):
            try:
                cl = list(self.db_read[collect_name].find(nosql_query))
                break
            except Exception as error_message:
                cl = []
                add_log_record(\
                        error_message, 'recommender', self.log_save_path)
        return cl


    def build_user_item_set(self, history_cl, item_cl):
        # item
        for i, record in enumerate(item_cl):
            item_id = record['ITEM_ID']
            self.item_set.add(item_id)
        # user
        for i, record in enumerate(history_cl):
            user_id = record['USER_ID']
            item_id = record['ITEM_ID']
            if item_id in self.item_set:
                self.user_set.add(user_id)
        print('user num : ', len(self.user_set))  
        print('item num : ', len(self.item_set))    


    def build_interaction_data(self, history_cl):
        self.interaction_data = dict()
        num = 0
        for record in history_cl:
            user_id = record['USER_ID']
            item_id = record['ITEM_ID']
            if user_id in self.user_set and item_id in self.item_set:
                # user idx
                if user_id not in self.user2idx:
                    # add index (user)
                    u_idx = len(self.idx_user)
                    self.user2idx[user_id] = u_idx
                    self.idx_user.append(user_id)
                    # add interaction
                    self.interaction_data[u_idx] = []
                else:
                    u_idx = self.user2idx[user_id]
                
                # item idx
                if item_id not in self.item2idx:
                    # add index (item)
                    i_idx = len(self.idx_item)
                    self.item2idx[item_id] = i_idx
                    self.idx_item.append(item_id)
                else:
                    i_idx = self.item2idx[item_id]
                
                # add interaction_data
                if u_idx not in self.interaction_data:
                    self.interaction_data[u_idx] = []
                self.interaction_data[u_idx].append(i_idx)
                
                # add item-idx to warm_item_set
                self.warm_item_set.add(i_idx)
            else:
                # it add to log in future.
                #print(f'cannot mapping user-id or item-id !!!{user_id} - {item_id}')
                pass


    def build_item_data(self, item_cl):
        self.item_data = dict()
        column_names = self.build_item_data_cfg['column_names']
        column_type = self.build_item_data_cfg['column_type']

        # build item_data
        for i, record in enumerate(item_cl):
            item_id = record['ITEM_ID']
            # cold item
            if item_id not in self.item2idx:
                # add index (item)
                i_idx = len(self.idx_item)
                self.item2idx[item_id] = i_idx
                self.idx_item.append(item_id)
            else:
                i_idx = self.item2idx[item_id]
            
            # add meta data
            self.item_data[i_idx] = {}
            for col in column_names:
                if column_type[col] == 'str':
                    self.item_data[i_idx][col] = str(record[col])
                elif column_type[col] == 'set':
                    self.item_data[i_idx][col] = set(record[col])
                elif column_type[col] == 'int':
                    self.item_data[i_idx][col] = int(record[col])

            # add item-idx to cold_item_set
            if i_idx not in self.warm_item_set:
                self.cold_item_set.add(i_idx)


    def build_user_data(self):
        self.user_data = dict()


    def split_train_val(self):
        self.interaction_train_data = dict()
        self.interaction_val_data = dict()
        
        user_list = list(self.interaction_data.keys())
        for user_idx in user_list:
            d = self.interaction_data[user_idx]
            l = int(len(d) * self.train_val_rate)
            
            if len(d) > self.train_seq_limit:
                self.interaction_train_data[user_idx] = d[:l]
                self.interaction_val_data[user_idx] = d[l:]
            else:
                self.interaction_train_data[user_idx] = d


    def build_train_info(self):
        # query user-item interaction data (history)
        history_cl = self.query_data(data_category='history')

        # query item meta data
        item_cl = self.query_data(data_category='item')

        # build user, item set
        self.build_user_item_set(history_cl, item_cl)

        # build interaction data
        self.build_interaction_data(history_cl)

        # build user data
        self.build_user_data()

        # build item data
        self.build_item_data(item_cl) 

        # split train, val
        self.split_train_val()

        # train_info
        train_info = {
            'interaction_train_data' : self.interaction_train_data,
            'interaction_val_data' : self.interaction_val_data
            }

        return train_info


    def build_inference_info(self):
        inference_info = {
                'idx_user' : self.idx_user,
                'idx_item' : self.idx_item,
                'item2idx' : self.item2idx,
                'cold_item_set' : self.cold_item_set,
                'item_data' : self.item_data
               }
        return inference_info




class ContentBaseProcessor(Genericproccessor):
    def __init__(self, db_config, rs_config):
        # database
        database_name = rs_config['query_settings']['read']['database']
        self.db_read = MongoClient(**db_config['connect_settings']['read'])[database_name]

        # build_item_data config
        self.build_item_data_cfg = rs_config['dataprocess']['build_item_data']
        
        # query_data config
        self.query_data_cfg = rs_config['dataprocess']['query_data']

        # log path
        self.log_save_path = rs_config['log']['save_path']

        # service
        self.service = rs_config['service']['name']


    def query_data(self, data_category):
        # collect_name
        collect_name = self.query_data_cfg[data_category]['collect']
        # nosql_query
        query_sp = self.query_data_cfg[data_category]['query_sp']
        if query_sp is None:
            nosql_query = {}
        elif query_sp == 'time_query':
            time_query_column = self.query_data_cfg[data_category]['time_query_column']
            nosql_query = time_query_sp(\
                time_query_column, self.query_start_tz, self.query_end_tz)
        
        elif query_sp == 'meta_history':
            nosql_query = meta_history_query_sp(self.service)
        
        elif query_sp == 'item_query':
            nosql_query = item_query_sp(self.service)

        elif query_sp == 'history':
            nosql_query = {}

        # query data
        for _ in range(5):
            try:
                cl = list(self.db_read[collect_name].find(nosql_query))
                break
            except Exception as error_message:
                cl = []
                add_log_record(error_message, 'recommender', self.log_save_path)
        return cl


    def build_user_item_set(self):
        return


    def build_item_data(self, item_cl):
        self.item_data = dict()
        column_names = self.build_item_data_cfg['column_names']
        column_type = self.build_item_data_cfg['column_type']

        # build item_data
        for record in item_cl:
            item_id = record['ITEM_ID']
            self.item_data[item_id] = dict()
            # add data
            for col in column_names:
                if column_type[col] == 'str':
                    self.item_data[item_id][col] = str(record[col])
                elif column_type[col] == 'set':
                    self.item_data[item_id][col] = set(record[col])
                elif column_type[col] == 'int':
                    self.item_data[item_id][col] = int(record[col])


    def build_user_data(self):
        return


    def build_meta_history_data(self, meta_history_cl):
        # init user2meta_history
        self.user2meta_history = dict()

        # add data (it will add filter_sp in future)
        for record in meta_history_cl:
            user_id = record['USER_ID']
            item_id = record['ITEM_ID']
            contentType = record['contentType']
            # add data
            if item_id in self.item_data \
            and contentType in [1,2]:
                if user_id not in self.user2meta_history:
                    self.user2meta_history[user_id] = []
                self.user2meta_history[user_id].append(item_id)


    def build_history_data(self, history_cl):
        # init user2history
        self.user2history = dict()

        # add data (it will add filter_sp in future)
        for record in history_cl:
            user_id = record['USER_ID']
            item_id = record['ITEM_ID']
            if item_id in self.item_data \
            and self.item_data[item_id]['contentType'] in [1,2]:
                if user_id not in self.user2history:
                    self.user2history[user_id] = []
                self.user2history[user_id].append(item_id)


    def build_train_info(self):
        # query item data
        item_cl = self.query_data(data_category='item')

        # build item data
        self.build_item_data(item_cl)

        # query meta_history data
        meta_history_cl = self.query_data(data_category='meta_history')

        # query history data
        history_cl = self.query_data(data_category='history')

        # build history data
        self.build_history_data(history_cl)

        # build meta history data
        self.build_meta_history_data(meta_history_cl)

        # train_info
        train_info = {
            'user2history' : self.user2history,
            'user2meta_history' : self.user2meta_history, 
            'item_data' : self.item_data
            }

        return train_info


    def build_inference_info(self):
        inference_info = {
                'user2history' : self.user2history,
                'user2meta_history' : self.user2meta_history
               }
        return inference_info


        

