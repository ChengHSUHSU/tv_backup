"""A module for trainers"""
import os
import time
import torch
import random
import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm
from abc import abstractmethod
from torch import optim

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
import utils
from numpy import dot
from numpy.linalg import norm



class ExpRunner(object):
    """A class for runing experiments

    Args: 
        exp_name (str): The name of experiments.
        exp_idx (str): The index of experiments.
        model_class_name (str): The class name of a specific model.
        args (dict): The experiment parameters.

    Attributes:
        exp_name (str): The name of experiments.
        exp_idx (str): The index of experiments.
        model_class_name (str): The class name of a specific model.
        args (dict): The experiment parameters.

    Methods:
        fit: Fit data to run the experiments,
            please override this method for your experiments.
    """
    def __init__(self) -> None:
        print()

    @abstractmethod
    def fit(self):
        pass
    
    @abstractmethod
    def save_model(self):
        pass   



class PairRecommendTrainer(ExpRunner):
    def __init__(self, model, dataset, rs_config):
        self.model_ = model
        self.dataset_ = dataset
        self.rs_config = rs_config
        self.lr = self.rs_config['model']['lr']
        self.device = self.rs_config['model']['device']
        self.epoch_num = self.rs_config['model']['epoch_num']
        self.batch_size = self.rs_config['model']['bpr_batch_size']
        self.weight_decay = self.rs_config['model']['weight_decay']
        self.opt = optim.Adam(model.parameters(), lr=self.lr)


    def fit(self):
        # get train data (by negative sampling)
        with utils.timer(name="Sample"):
            S = utils.UniformSample_original(self.dataset_)
        users = torch.Tensor(S[:, 0]).long()
        posItems = torch.Tensor(S[:, 1]).long()
        negItems = torch.Tensor(S[:, 2]).long()

        # device
        users = users.to(self.device)
        posItems = posItems.to(self.device)
        negItems = negItems.to(self.device)

        # shuffle
        users, posItems, negItems = utils.shuffle(users, posItems, negItems)

        aver_loss = 0.
        total_batch = len(users) // self.batch_size + 1

        # modeling
        for epoch in tqdm(range(self.epoch_num)):
            # train
            self.model_.train()
            for (batch_i,
                (batch_users,
                 batch_pos,
                 batch_neg)) in enumerate(utils.minibatch(users,
                                                          posItems,
                                                          negItems,
                                                          batch_size=self.batch_size)):
                # get loss
                loss, reg_loss = self.model_.getLoss(batch_users, [batch_pos, batch_neg])
                reg_loss = reg_loss * self.weight_decay
                loss = loss + reg_loss
                # optimization
                self.opt.zero_grad()
                loss.backward()
                self.opt.step()
                cri = loss.cpu().item()
                break

            aver_loss += cri
            print('train aver_loss : ', aver_loss)

            # evaluation
            self.model_.eval()
            self.evaluate()

        # aver_loss
        aver_loss = aver_loss / total_batch
        time_info = utils.timer.dict()
        utils.timer.zero()
        return f"loss{aver_loss:.3f}-{time_info}"


    def save_model(self):
        weight_file = utils.getFileName(self.rs_config)
        torch.save(self.model_.state_dict(), weight_file)
 

    def evaluate(self):
        max_K = 20
        users_list = []
        rating_list = []
        groundTrue_list = []
        testDict = self.dataset_.testDict
        results = {'precision': np.zeros(1), 'recall': np.zeros(1), 'ndcg': np.zeros(1)}

        with torch.no_grad():
            users = list(testDict.keys())
            total_batch = len(users) // self.batch_size + 1
            for batch_users in utils.minibatch(users, batch_size=self.batch_size):
                # history pos click item
                allPos = self.dataset_.getUserPosItems(batch_users)
                groundTrue = [testDict[u] for u in batch_users]
                #
                batch_users_gpu = torch.Tensor(batch_users).long()
                batch_users_gpu = batch_users_gpu.to(self.device)
                rating = self.model_.getUsersRating(batch_users_gpu)
                #
                exclude_index = []
                exclude_items = []
                for range_i, items in enumerate(allPos):
                    exclude_index.extend([range_i] * len(items))
                    exclude_items.extend(items)
                rating[exclude_index, exclude_items] = -(1<<10)
                _, rating_K = torch.topk(rating, k=max_K)
                rating = rating.cpu().numpy()
                del rating
                users_list.append(batch_users)
                rating_list.append(rating_K.cpu())
                groundTrue_list.append(groundTrue)
            assert total_batch == len(users_list)

            # calculate rank metric
            X = zip(rating_list, groundTrue_list)
            pre_results = []
            for x in X:
                pre_results.append(self.test_one_batch(x, max_K))
            scale = float(self.batch_size / len(users))
            for result in pre_results:
                results['recall'] += result['recall']
                results['precision'] += result['precision']
                results['ndcg'] += result['ndcg']
            results['recall'] /= float(len(users))
            results['precision'] /= float(len(users))
            results['ndcg'] /= float(len(users))
        print(results)


    def test_one_batch(self, X, max_K):
        pre, recall, ndcg = [], [], []
        sorted_items = X[0].numpy()
        groundTrue = X[1]
        r = utils.getLabel(groundTrue, sorted_items)
        
        for k in [max_K]:
            ret = utils.RecallPrecision_ATk(groundTrue, r, k)
            pre.append(ret['precision'])
            recall.append(ret['recall'])
            ndcg.append(utils.NDCGatK_r(groundTrue,r,k))

        return {
                'recall':np.array(recall), 
                'precision':np.array(pre), 
                'ndcg':np.array(ndcg)
               }



class ContentRecommendTrainer(ExpRunner):
    def __init__(self, model, dataset, rs_config):
        self.model = model
        self.item2content = dataset.item2content
        self.user2meta_history = dataset.user2meta_history
        self.user2history = dataset.user2history


    def fit(self):
        # build content2embedding
        contents = list(self.item2content.values())
        #content2embedding = self.model.build_content2embedding(contents)
        content2keyword_set = self.model.build_content2keyword_set(contents)

        # sort by 0-index
        item_ids = sorted(self.item2content.keys())

        # build item2item_rank
        item2item_rank = dict()
        for item_id_a in item_ids:
            # item_a content
            content_a = self.item2content[item_id_a]
            # item_a embedding
            #content_a_emb = content2embedding[content_a]
            content_a_keyw = content2keyword_set[content_a]
            # rank item_ids
            rank_threshold = 0
            rank_item_ids = []
            rank_item_ids_zero = []
            for item_id_b in item_ids:
                if item_id_a != item_id_b:
                    content_b = self.item2content[item_id_b]
                    #content_b_emb = content2embedding[content_b]
                    content_b_keyw = content2keyword_set[content_b]
                    # calculate similarity score
                    #score = self.cosim_func(content_a_emb, content_b_emb)
                    score = self.count_func(content_a_keyw, content_b_keyw)
                    # append
                    if score > rank_threshold:
                        rank_item_ids.append([item_id_b, score])
                    else:
                        rank_item_ids_zero.append([item_id_b, score])
            # rerank
            rank_item_ids = sorted(rank_item_ids, reverse=True, key=lambda x:x[1])
            # shuffle
            if len(rank_item_ids_zero) != 0:
                rank_item_ids_zero = random.sample(rank_item_ids_zero, len(rank_item_ids_zero))
            # merge
            rank_item_ids = rank_item_ids + rank_item_ids_zero
            # build empty list
            item2item_rank[item_id_a] = [item for item, score in rank_item_ids]

        # build model_info
        model_info = {
            'item2item_rank' : item2item_rank, 
            'user2meta_history' : self.user2meta_history,
            'user2history' : self.user2history
            }
        self.model.save_model_info(model_info)


    def cosim_func(self, emba, embb):
        return dot(emba, embb)/(norm(emba)*norm(embb))

    def count_func(self, seta, setb):
        return len(seta & setb)

    def save_model(self):
        return   



