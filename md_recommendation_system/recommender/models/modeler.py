"""A module for gnn model"""
import jieba
import torch
from torch import nn
import numpy as np
from tqdm import tqdm
from models.basic import BasicModel
from transformers import AutoTokenizer, AutoModel


 



class lightGCN(BasicModel):
    def __init__(self, dataset, rs_config):
        super(lightGCN, self).__init__()
        self.rs_config = rs_config
        self.dataset_ = dataset

        # side info
        self.num_users  = self.dataset_.n_users
        self.num_items  = self.dataset_.m_items
        self.A_split = self.rs_config['model']['A_split']
        self.keep_prob = self.rs_config['model']['keep_prob']
        self.latent_dim = self.rs_config['model']['latent_dim_rec'] 
        self.n_layers = self.rs_config['model']['lightGCN_n_layers']

        # initial embedding
        self.__init_weight()

        # activation func
        self.sigmoid = nn.Sigmoid()


    def __init_weight(self):
        # user embedding
        self.embedding_user = torch.nn.Embedding(
            num_embeddings=self.num_users, embedding_dim=self.latent_dim)
        
        # item embedding
        self.embedding_item = torch.nn.Embedding(
            num_embeddings=self.num_items, embedding_dim=self.latent_dim)

        # normalize by normal
        if self.rs_config['model']['pretrain'] == 0:
            nn.init.normal_(self.embedding_user.weight, std=0.1)
            nn.init.normal_(self.embedding_item.weight, std=0.1)
        else:
            # it implement in future
            self.embedding_user.weight.data.copy_(torch.from_numpy(self.rs_config['model']['user_emb']))
            self.embedding_item.weight.data.copy_(torch.from_numpy(self.rs_config['model']['item_emb']))
            print('use pretarined data')

        # build graph
        self.Graph = self.dataset_.getSparseGraph()
        print(f"lgn is already to go(dropout:{self.rs_config['model']['dropout']})")


    def __dropout_x(self, x, keep_prob):
        size = x.size()
        index = x.indices().t()
        values = x.values()
        random_index = torch.rand(len(values)) + keep_prob
        random_index = random_index.int().bool()
        index = index[random_index]
        values = values[random_index]/keep_prob
        g = torch.sparse.FloatTensor(index.t(), values, size)
        return g


    def __dropout(self, keep_prob):
        if self.A_split:
            graph = []
            for g in self.Graph:
                graph.append(self.__dropout_x(g, keep_prob))
        else:
            graph = self.__dropout_x(self.Graph, keep_prob)
        return graph


    def computer(self):
        """ propagate methods for lightGCN
        """
        # take embedding (user, item)
        users_emb = self.embedding_user.weight
        items_emb = self.embedding_item.weight
        all_emb = torch.cat([users_emb, items_emb])
        embs = [all_emb]

        # when interaction rate is high, dropout
        if self.rs_config['model']['dropout']:
            if self.training:
                g_droped = self.__dropout(self.keep_prob)
            else:
                g_droped = self.Graph        
        else:
            g_droped = self.Graph    
        
        # propagating gnn layer
        for layer in range(self.n_layers):
            # when adj matrix is very peko (for memory)
            if self.A_split:
                temp_emb = []
                for f in range(len(g_droped)):
                    temp_emb.append(torch.sparse.mm(g_droped[f], all_emb))
                side_emb = torch.cat(temp_emb, dim=0)
                all_emb = side_emb
            else:
                all_emb = torch.sparse.mm(g_droped, all_emb)
            embs.append(all_emb)
        embs = torch.stack(embs, dim=1)
        light_out = torch.mean(embs, dim=1)
        
        # take user, item
        users, items = torch.split(light_out, [self.num_users, self.num_items])
        return users, items


    def getUsersRating(self, users=None):
        # build user, item embedding
        all_users, all_items = self.computer()

        if users is not None:
            users = torch.tensor(users)
            users_emb = all_users[users.long()]
        else:
            users_emb = all_users[:]
        items_emb = all_items
        rating = self.sigmoid(torch.matmul(users_emb, items_emb.t()))
        return rating

    
    def build_user_items_score(self, users):
        user_items_score = []
        # rating
        rating = self.getUsersRating(users=users)
        # build user2items_score
        rating = rating.tolist()
        for i, scores in enumerate(rating):
            user_id = users[i]
            user_items_score.append([user_id, scores])
        return user_items_score


 
    def getEmbedding(self, users, pos_items, neg_items):
        all_users, all_items = self.computer()
        users_emb = all_users[users]
        pos_emb = all_items[pos_items]
        neg_emb = all_items[neg_items]
        users_emb_ego = self.embedding_user(users)
        pos_emb_ego = self.embedding_item(pos_items)
        neg_emb_ego = self.embedding_item(neg_items)
        return users_emb, pos_emb, neg_emb, users_emb_ego, pos_emb_ego, neg_emb_ego


    def getLoss(self, X, Y):
        users = X
        pos, neg = Y[0], Y[1]

        (users_emb, pos_emb, neg_emb, 
        userEmb0,  posEmb0, negEmb0) = self.getEmbedding(users.long(), pos.long(), neg.long())
        reg_loss = (1/2)*(userEmb0.norm(2).pow(2) + 
                         posEmb0.norm(2).pow(2)  +
                         negEmb0.norm(2).pow(2))/float(len(users))
        pos_scores = torch.mul(users_emb, pos_emb)
        pos_scores = torch.sum(pos_scores, dim=1)
        neg_scores = torch.mul(users_emb, neg_emb)
        neg_scores = torch.sum(neg_scores, dim=1)
        
        loss = torch.mean(torch.nn.functional.softplus(neg_scores - pos_scores))
        
        return loss, reg_loss


    def forward(self, users, items):
        # compute embedding
        all_users, all_items = self.computer()
        users_emb = all_users[users]
        items_emb = all_items[items]
        inner_pro = torch.mul(users_emb, items_emb)
        gamma = torch.sum(inner_pro, dim=1)
        return gamma





class ContentEmbedding:
    def __init__(self, dataset, rs_config):
        # init model
        # self.model = AutoModel.from_pretrained(\
        #             rs_config['model']['bert_model_name'])

        # # tokenizer
        # self.tokenizer = AutoTokenizer.from_pretrained(\
        #             rs_config['model']['bert_model_name'])
        print()


    def build_item_embedding(self, content):
        inputs = self.tokenizer(content, return_tensors="pt")
        outputs = self.model(**inputs)
        return outputs['pooler_output'].detach().numpy().reshape(-1)


    def build_keyword_set(self, content):
        keyword_set = set()
        for keyw in jieba.cut(content):
            if len(keyw) > 1:
                keyword_set.add(keyw)
        return keyword_set


    def build_content2embedding(self, contents):
        content2embedding = dict()
        for content in tqdm(contents):
            content2embedding[content] = \
                    self.build_item_embedding(content)
        return content2embedding


    def build_content2keyword_set(self, contents):
        content2keyword_set = dict()
        for content in tqdm(contents):
            content2keyword_set[content] = self.build_keyword_set(content)
        return content2keyword_set


    def save_model_info(self, info):
        self.model_info = info

