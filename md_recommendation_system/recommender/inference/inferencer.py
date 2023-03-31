

import random
from tqdm import tqdm
from datetime import datetime
from abc import abstractmethod
from inference.recall_module import zfl_recall_layer
from inference.pipeline_module import zfl_inference_result






class Genericinferencer(object):
    """Generic process

    A data process consists 3 methods:
    1. build_interaction_data

    Args:
        user_data (dict): None.
    """
    def __init__(self):
        print()

    @abstractmethod
    def recall_layer(self):
        pass

    @abstractmethod
    def rerank_layer(self):
        pass

    @abstractmethod
    def build_inference_result(self):
        pass





class PersonalizeInferencer(Genericinferencer):
    def __init__(self, model, inference_info, rs_config):
        self.model = model
        self.rs_config = rs_config
        self.inference_info = inference_info
        self.idx_user = inference_info['idx_user']
        self.service_name = rs_config['service']['name']
        self.inference_bz = rs_config['dataprocess']['inference_batch_size']
        self.platform_list = rs_config['inference']['recall_layer']['platforms']


    def recall_layer(self, items_score, platform=None):
        if self.service_name == 'zfl':
            item_rank = zfl_recall_layer(\
                    items_score, self.inference_info, self.rs_config, platform)
        return item_rank


    def rerank_layer(self, item_rank):
        item_rerank = random.sample(item_rank, len(item_rank))
        return item_rerank


    def build_inference_result(self):
        user_list = [i for i in range(self.model.num_users)]
        batch_num = int(self.model.num_users / self.inference_bz) + 1

        # build inference result
        inference_result = dict()
        for platform in self.platform_list:
            inference_result[platform] = list()

        for i in tqdm(range(batch_num)):
            # user_batch
            user_batch = user_list[i * self.inference_bz : (i+1) * self.inference_bz]

            # build items_score for each users
            user_items_score = self.model.build_user_items_score(user_batch)

            # (未來如果需要多平台推薦)
            for platform in self.platform_list:
                for user_idx, items_score in user_items_score:
                    # reindex (user)
                    user_id = self.idx_user[user_idx]

                    # recall layer
                    item_rank = self.recall_layer(items_score, platform)

                    # rerank layer
                    item_rerank = self.rerank_layer(item_rank)

                    # append to inference
                    inference_result[platform].append({
                                            'USER_ID' : user_id, 
                                            'ITEM_ID_RANK' : item_rerank
                                            })

        return inference_result


    def build_inference_history(self, inference_result):
        # now date
        nowdate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        # user_item_inference
        user_item_inference = inference_result[:]

        # build inference_history
        inference_history = {
                    'User-Item' : user_item_inference, 
                    'UpdateTime' : nowdate
                }
        return inference_history




class ContentInferencer(Genericinferencer):
    def __init__(self, model, inference_info, rs_config):
        self.model = model
        self.platform_list = rs_config['inference']['recall_layer']['platforms']


    def recall_layer(self):
        return 


    def rerank_layer(self):
        return


    def build_inference_result(self):
        # build user_list
        item2item_rank = self.model.model_info['item2item_rank']
        user2meta_history = self.model.model_info['user2meta_history']
        user2history = self.model.model_info['user2history']
        
        # build inference result
        inference_result = dict()
        for platform in self.platform_list:
            inference_result[platform+'/item2item_rank'] = []
            inference_result[platform+'/user2meta_history'] = []
            inference_result[platform+'/user2history'] = []

            for item, item_rank in item2item_rank.items():
                inference_result[platform+'/item2item_rank']\
                    .append({'ITEM_ID' : item, 'ITEM_ID_RANK' : item_rank})

            for user, meta_history in user2meta_history.items():
                inference_result[platform+'/user2meta_history']\
                    .append({'USER_ID' : user, 'meta_history' : meta_history})   

            for user, history in user2history.items():
                inference_result[platform+'/user2history']\
                    .append({'USER_ID' : user, 'history' : history})   

        return inference_result    

    
    def build_inference_history(self):
        return

