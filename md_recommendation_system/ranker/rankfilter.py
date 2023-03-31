
import random
from abc import abstractmethod



class Genericrankfilter(object):
    def __init__(self):
        print()

    @abstractmethod
    def query_data(self):
        pass

    @abstractmethod
    def run(self):
        pass





class RankFilterModel(Genericrankfilter):
    def __init__(self, dataloader, rk_config):
        self.topK = 200
        self.history_topK = 10
        self.used_contentType = ['all']

        # dataloader
        #self.item2info = dataloader.item2info
        self.item2rank_item = dataloader.item2rank_item
        self.user_history = dataloader.user_history

        self.item2info = dict()
        for i_ in self.item2rank_item.keys():
            self.item2info[i_] = {'contentType' : 1}


    def fit(self):
        # init recommend_info
        recommend_info = {
            'user_item_rank' : [], 'contentType' : []
            }
        # fit
        for record in self.user_history:
            user = record['USER_ID']
            history = record['history'][:self.history_topK]
            # build similiar_item_list, max_item_len
            similiar_item_list, max_item_len = [], 0
            for item_mh in history:
                if item_mh in self.item2rank_item:
                    similiar_item_ = self.item2rank_item[item_mh]
                    if len(similiar_item_) > 0:
                        similiar_item_list.append(similiar_item_)
                        if max_item_len < len(similiar_item_):
                            max_item_len = len(similiar_item_)
            used_item = set()
            cycle_num = len(similiar_item_list)
            for ct_ in self.used_contentType:
                # build rank_item
                rank_item = []
                for i in range(max_item_len):
                    cycle_list = random.sample(list(range(cycle_num)), cycle_num)
                    for j in cycle_list:
                        if i < len(similiar_item_list[j]):
                            item_ = similiar_item_list[j][i]
                            if ct_ == 'all'\
                            or self.item2info[item_]['contentType'] == ct_:
                                if item_ not in used_item:
                                    rank_item.append(item_)
                                    used_item.add(item_)
                    if len(rank_item) >= self.topK:
                        break
                if len(rank_item) != 0:
                    # diversity ranking
                    diversity = True
                    diversity_hit = 10
                    rank_item_diversity = []
                    if diversity is True:
                        batch_ = []
                        for i in range(len(rank_item)):
                            batch_.append(rank_item[i])
                            if len(batch_) % diversity_hit == 0:
                                batch_ = random.sample(batch_, len(batch_))
                                rank_item_diversity += batch_[:]
                                batch_ = []
                        rank_item_diversity += batch_
                        rank_item = rank_item_diversity[:]
                    # append recommend_info
                    recommend_info['user_item_rank']\
                        .append({'userId' : user, 'rank_itemId' : rank_item})
                    recommend_info['contentType'].append(ct_)
        return recommend_info





