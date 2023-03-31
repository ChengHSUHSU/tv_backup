"""A module for dataloader"""
import os 
import torch
import numpy as np
from time import time
import scipy.sparse as sp
from scipy.sparse import csr_matrix
from torch.utils.data import Dataset, DataLoader





class BasicDataset(Dataset):
    def __init__(self):
        print()

    @property
    def n_users(self):
        raise NotImplementedError
    
    @property
    def m_items(self):
        raise NotImplementedError
    
    @property
    def trainDataSize(self):
        raise NotImplementedError
    
    @property
    def testDict(self):
        raise NotImplementedError
    
    @property
    def allPos(self):
        raise NotImplementedError
    
    def getUserItemFeedback(self, users, items):
        raise NotImplementedError
    
    def getUserPosItems(self, users):
        raise NotImplementedError
    
    def getUserNegItems(self, users):
        """
        not necessary for large dataset
        it's stupid to return all neg items in super large dataset
        """
        raise NotImplementedError
    
    def getSparseGraph(self):
        """
        build a graph in torch.sparse.IntTensor.
        Details in NGCF's matrix form
        A = 
            |I,   R|
            |R^T, I|
        """
        raise NotImplementedError




class Loader(BasicDataset):

    def __init__(self, train_info, rs_config):
        self.n_user = 0
        self.m_item = 0
        self.traindataSize = 0
        self.testDataSize = 0
        trainUniqueUsers, trainItem, trainUser = [], [], []
        testUniqueUsers, testItem, testUser = [], [], []

        self.device = rs_config['model']['device']
        self.split = rs_config['dataloader']['A_split']
        self.folds = rs_config['dataloader']['A_n_fold']
        self.A_mat_path = rs_config['dataloader']['A_mat_path']
        self.used_old_A_mat = rs_config['dataloader']['used_old_A_mat']

        interaction_train_data = train_info['interaction_train_data']
        interaction_val_data = train_info['interaction_val_data']

        # train data
        user_list = list(interaction_train_data.keys())
        for uid in user_list:
            items = interaction_train_data[uid]
            trainUniqueUsers.append(uid)
            trainUser.extend([uid] * len(items))
            trainItem.extend(items)
            self.m_item = max(self.m_item, max(items))
            self.n_user = max(self.n_user, uid)
            self.traindataSize += len(items)

        # val data
        user_list = list(interaction_val_data.keys())
        for uid in user_list:
            items = interaction_val_data[uid]
            testUniqueUsers.append(uid)
            testUser.extend([uid] * len(items))
            testItem.extend(items)
            self.m_item = max(self.m_item, max(items))
            self.n_user = max(self.n_user, uid)
            self.traindataSize += len(items)        

        self.m_item += 1
        self.n_user += 1

        # list -> array (train)
        self.trainUniqueUsers = np.array(trainUniqueUsers)
        self.trainUser = np.array(trainUser)
        self.trainItem = np.array(trainItem)

        # list -> array (test)
        self.testUniqueUsers = np.array(testUniqueUsers)
        self.testUser = np.array(testUser)
        self.testItem = np.array(testItem)

        # sparsity
        sparsity = (self.trainDataSize + self.testDataSize) / self.n_users / self.m_items
        print(f"{self.trainDataSize} interactions for training")
        print("Dataset sparsity : {sparsity}")

        # adj info (user, item)
        self.Graph = None
        self.UserItemNet = csr_matrix((np.ones(len(self.trainUser)), (self.trainUser, self.trainItem)),
                                      shape=(self.n_user, self.m_item))
        self.users_D = np.array(self.UserItemNet.sum(axis=1)).squeeze()
        self.users_D[self.users_D == 0.] = 1
        self.items_D = np.array(self.UserItemNet.sum(axis=0)).squeeze()
        self.items_D[self.items_D == 0.] = 1.

        # pre-calculate
        self._allPos = self.getUserPosItems(list(range(self.n_user)))
        self.__testDict = self.__build_test()
        print("dataset is ready to go")


    @property
    def n_users(self):
        return self.n_user
    
    @property
    def m_items(self):
        return self.m_item
    
    @property
    def trainDataSize(self):
        return self.traindataSize
    
    @property
    def testDict(self):
        return self.__testDict

    @property
    def allPos(self):
        return self._allPos


    def _split_A_hat(self, A):
        A_fold = []
        fold_len = (self.n_users + self.m_items) // self.folds
        for i_fold in range(self.folds):
            start = i_fold*fold_len
            if i_fold == self.folds - 1:
                end = self.n_users + self.m_items
            else:
                end = (i_fold + 1) * fold_len
            A_fold.append(self._convert_sp_mat_to_sp_tensor(A[start:end]).coalesce().to(self.device))
        return A_fold


    def _convert_sp_mat_to_sp_tensor(self, X):
        coo = X.tocoo().astype(np.float32)
        row = torch.Tensor(coo.row).long()
        col = torch.Tensor(coo.col).long()
        index = torch.stack([row, col])
        data = torch.FloatTensor(coo.data)
        return torch.sparse.FloatTensor(index, data, torch.Size(coo.shape))


    def getSparseGraph(self):
        print("loading adjacency matrix")
        if self.Graph is None:
            if self.used_old_A_mat is True:
                pre_adj_mat = sp.load_npz(self.A_mat_path)
                print("successfully loaded...")
                norm_adj = pre_adj_mat
            else :
                print("generating adjacency matrix")
                s = time()

                # build adj matrix
                all_ = self.n_users + self.m_items
                adj_mat = sp.dok_matrix((all_, all_), dtype=np.float32)
                adj_mat = adj_mat.tolil()
                R = self.UserItemNet.tolil()
                adj_mat[:self.n_users, self.n_users:] = R
                adj_mat[self.n_users:, :self.n_users] = R.T
                adj_mat = adj_mat.todok()

                # normalization for adj matrix
                rowsum = np.array(adj_mat.sum(axis=1))
                d_inv = np.power(rowsum, -0.5).flatten()
                d_inv[np.isinf(d_inv)] = 0.
                d_mat = sp.diags(d_inv)
                norm_adj = d_mat.dot(adj_mat)
                norm_adj = norm_adj.dot(d_mat)
                norm_adj = norm_adj.tocsr()

                end = time()
                print(f"costing {end-s}s, saved norm_mat...")
                sp.save_npz(self.A_mat_path, norm_adj)

            if self.split == True:
                self.Graph = self._split_A_hat(norm_adj)
                print("done split matrix")
            else:
                self.Graph = self._convert_sp_mat_to_sp_tensor(norm_adj)
                self.Graph = self.Graph.coalesce().to(self.device)
                print("don't split the matrix")
        return self.Graph


    def __build_test(self):
        """
        return:
            dict: {user: [items]}
        """
        test_data = {}
        for i, item in enumerate(self.testItem):
            user = self.testUser[i]
            if test_data.get(user):
                test_data[user].append(item)
            else:
                test_data[user] = [item]
        return test_data


    def getUserItemFeedback(self, users, items):
        """
        users:
            shape [-1]
        items:
            shape [-1]
        return:
            feedback [-1]
        """
        return np.array(self.UserItemNet[users, items]).astype('uint8').reshape((-1,))


    def getUserPosItems(self, users):
        posItems = []
        for user in users:
            posItems.append(self.UserItemNet[user].nonzero()[1])
        return posItems



class ContentLoader:
    def __init__(self, train_info, rs_config):
        '''
        it will add filter in future.
        '''
        self.item_data = train_info['item_data']
        self.user2meta_history = train_info['user2meta_history']
        self.user2history = train_info['user2history']

        # build item2content
        self.item2content = dict()
        for item_id in self.item_data.keys():
            title = self.item_data[item_id]['title']
            self.item2content[item_id] = title


