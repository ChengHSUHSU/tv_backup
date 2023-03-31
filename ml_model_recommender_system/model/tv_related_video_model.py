from model.base_model import Model


class ModelTvRelatedVideoModel(Model):

    def forward(self):
        '''
        In future,
        the forward funciton will be operated by config.
        '''
        self.get_aggregator_data()
        self.data_preprocess()
        self.train()
        self.evaluate()

    def get_aggregator_data(self):
        self.aggregator.forward()

    def data_preprocess(self):
        # view-aslo-view score
        vv_score_matrix = self.aggregator.vv_score_matrix

        # add noise to vv_score_matrix
        self.vv_score_matrix_noise = self.add_noise_matrix(vv_score_matrix)

        # get content_id2hard_rank
        self.content_id2hard_rank = self.aggregator.content_id2hard_rank

        # get content_data
        self.content_data = self.aggregator.content_data

    def train(self):
        # build content2content_rank
        content2content_rank = self.rank_score(score_array=self.vv_score_matrix_noise)

        # rerank (hard-filter)
        self.content2content_rank = self.hard_filter_rerank(content2content_rank)

    def evaluate(self):
        return

    def hard_filter_rerank(self, content2content_rank: dict):
        '''
        these hard content_id (series, episode), 
        it makes recommend results hard-rerank.
        '''
        content_id_list = list(self.content_id2hard_rank.keys())
        for c_id in content_id_list:
            if c_id in content2content_rank:
                content_rerank = []
                used_content_ids = set()
                content_rank = content2content_rank[c_id]
                prioty_rank = self.content_id2hard_rank[c_id]
                content_rerank += prioty_rank
                used_content_ids = used_content_ids | set(prioty_rank)
                for i in range(len(content_rank)):
                    if content_rank[i] not in used_content_ids:
                        used_content_ids.add(content_rank[i])
                        content_rerank += [content_rank[i]]
                # update rerank results
                content2content_rank[c_id] = content_rerank
        return content2content_rank
