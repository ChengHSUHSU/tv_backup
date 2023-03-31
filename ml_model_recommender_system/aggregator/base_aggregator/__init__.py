import numpy as np
from scipy import sparse
from abc import ABCMeta, abstractmethod


class Aggregator(metaclass=ABCMeta):
    def __init__(self, cfg, reader):
        self.cfg = cfg
        self.reader = reader

    @abstractmethod
    def get_raw_data(self):
        pass

    @abstractmethod
    def forward(self):
        pass

    def build_uv_matrix(self, event_data, max_user_id=None, max_content_id=None, user_col='user_id', content_col='content_id'):
        # build user_id2u_idx
        user_id2u_idx = dict()
        if max_user_id is None:
            user_ids = sorted(list(set(event_data[user_col])))
            for i in range(len(user_ids)):
                user_id2u_idx[user_ids[i]] = i
            max_user_id  = max(user_ids)
        else:
            for i in range(max_user_id+1):
                user_id2u_idx[i] = i

        # content_id2c_idx
        content_id2c_idx = dict()
        for i in range(max_content_id+1):
            content_id2c_idx[i] = i      

        # build user-view sparse matrix
        I, J, K = [], [], []
        for record in event_data.to_dict('records'):
            u_idx = user_id2u_idx[record[user_col]]
            c_idx = record[content_col]
            I.append(u_idx)
            J.append(c_idx)
            K.append(1)
        I = np.array(I)
        J = np.array(J)
        K = np.array(K)
        uv_matrix = sparse.coo_matrix((K,(I,J)), shape=(max_user_id+1, max_content_id+1)).tocsr()
        return uv_matrix
