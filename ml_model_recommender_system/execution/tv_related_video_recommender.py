import sys
sys.path.insert(0, 'ml_model_recommender_system.zip')
# zip -r ml_model_recommender_system *  

import argparse
from utils import load_config
from utils.Mongodb import MongodbConnector
from reader.tv_related_video_reader import TvRelatedVideoReader
from aggregator.tv_related_video_aggregator import TvRelatedVideoAggregator
from model.tv_related_video_model import ModelTvRelatedVideoModel


def arg_parse():
    """arg_parse

    argument setting.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--connect_cfg_path',
                        type=str,
                        help='connector config setting path.',
                        default='./config/tv_related_video/connect.yaml')
    parser.add_argument('--option_cfg_path',
                        type=str,
                        help='optional config setting path.',
                        default='./config/tv_related_video/option.yaml')
    return parser.parse_args()


def get_user_data(hot_item_aggregator):
    return


def get_item_data(hot_item_aggregator):
    return


def dump_data(cfg, model):
    # config
    connect_cfg = load_config(cfg.connect_cfg_path)
    option_cfg = load_config(cfg.option_cfg_path)
    
    # mongo connect
    database_name = option_cfg['dump']['database_name']
    mongo_conn = MongodbConnector(connect_cfg['mongodb'], database_name=database_name) 

    # recommend results
    item2item_rank = model.content2content_rank

    item2item_rank_data = []
    for item, item_rank in list(item2item_rank.items()):
        item_rank_str = [str(item) for item in item_rank]
        item2item_rank_data.append(
            {'content_id' : str(item), 'candidate_content_ids': ','.join(item_rank_str[:100])}
        )
    # debug data
    content_data = list(model.content_data.to_dict('records'))

    # dump item2item_rank
    mongo_conn.remove_all(collect='item2item_rank')
    mongo_conn.dump(item2item_rank_data, collect='item2item_rank')

    # dump content_data
    mongo_conn.remove_all(collect='content_data')
    mongo_conn.dump(content_data, collect='content_data')


def main(cfg):
    # data reader
    reader = TvRelatedVideoReader(cfg)

    # get statistic feature by aggregator
    hot_item_aggregator = TvRelatedVideoAggregator(cfg, reader)

    # train model (candidate, rerank)
    model = ModelTvRelatedVideoModel(cfg, hot_item_aggregator)
    model.forward()

    # user_data (optional, future)
    user_data = get_user_data(hot_item_aggregator)

    # item_data (optional, future)
    item_data = get_item_data(hot_item_aggregator)

    # dump data (mongodb, databricks)
    dump_data(cfg, model)


if __name__ == '__main__':
    cfg = arg_parse()
    main(cfg)
