from aggregator.base_aggregator import Aggregator


class TvRelatedVideoAggregator(Aggregator):

    def forward(self):
        '''
        In future, 
        the funciton will be operated by config.
        '''
        raw_data = self.get_raw_data()
        content_data = raw_data['content_data']

        # get basic feature
        self.max_content_id = max(list(content_data['content_id']))

        # view-also-view score
        self.vv_score_matrix = self.get_view_also_view_scores(raw_data['event_data'])

        # hard-rank (series-episode)
        self.content_id2hard_rank = self.get_content_id2hard_rank(content_data)

        # content_data
        self.content_data = content_data.fillna('None')

    def get_raw_data(self):
        raw_data = self.reader.process()
        return raw_data

    def get_content_id2hard_rank(self, content_data):
        # series_name, episode are nonempty
        series_episode_dat = content_data[~(content_data['series_name'].isnull()) & ~(content_data['episode'].isnull())]

        # order by episode
        series_episode_dat = series_episode_dat.sort_values(by='episode')

        # series_names
        series_names = list(set(series_episode_dat['series_name']))

        # build content_id2hard_rank
        content_id2hard_rank = dict()
        for series_n in series_names:
            dat = series_episode_dat[series_episode_dat['series_name']==series_n]
            content_id_rank_list = list(dat['content_id'])
            for i, c_id in enumerate(content_id_rank_list):
                content_id2hard_rank[c_id] = content_id_rank_list[i:] + content_id_rank_list[:i]
        return content_id2hard_rank

    def get_view_also_view_scores(self, event_data, effective_duration=30):
        # effective watch
        event_data_effective_watch = event_data[event_data['duration']>=effective_duration]

        # build uv matrix (user, view(=video))
        uv_matrix = self.build_uv_matrix(event_data_effective_watch, max_user_id=None, max_content_id=self.max_content_id)

        # build view-also-view matrix  (UV.t * UV = VU * UV = VV)
        vv_matrix = uv_matrix.transpose().dot(uv_matrix)

        # to array
        vv_matrix_array = vv_matrix.toarray()
        return vv_matrix_array
