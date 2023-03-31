


import numpy as np
from abc import ABCMeta, abstractmethod
from aggregator.base_aggregator import Aggregator


class Model(metaclass=ABCMeta):
    def __init__(self, cfg: dict, aggregator: Aggregator):
        self.cfg = cfg
        self.aggregator = aggregator

    @abstractmethod
    def get_aggregator_data(self):
        pass

    @abstractmethod
    def forward(self):
        pass

    def add_noise_matrix(self, matrix_array, row=None, col=None):
        row = matrix_array.shape[0]
        col = matrix_array.shape[1]
        return matrix_array + np.random.rand(row, col)

    def rank_score(self, score_array):
        '''
        Reference:
        https://github.com/allenjack/HGN/blob/master/run.py
        '''
        row = score_array.shape[0]
        col = score_array.shape[1]
        topk = col
        ind = np.argpartition(score_array, -topk)
        ind = ind[:, -topk:]
        arr_ind = score_array[np.arange(len(score_array))[:, None], ind]
        arr_ind_argsort = np.argsort(arr_ind)[np.arange(len(score_array)), ::-1]
        rank_score_array = ind[np.arange(len(score_array))[:, None], arr_ind_argsort]

        row_id2col_id_rank = dict()
        for r in range(row):
            row_id2col_id_rank[r] = list(rank_score_array[r, :])
        return row_id2col_id_rank
