
import argparse
from datetime import datetime

from utils import load_config
from utils import submit_to_backend
from utils import submit_to_bucket

from dataloader import RecDataLoader
from rankfilter import RankFilterModel




def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_cfg_path',
                        help='database config setting path.',
                        type=str,
                        default='./ranker/config/load.yaml')

    parser.add_argument('--rk_cfg_path',
                        help='ranklfilter config setting path.',
                        type=str,
                        default='./ranker/config/rank.yaml')
    return parser.parse_args() 



def main(args):
    # datetime-now
    datetime_now = datetime.now().strftime("%Y%m%d-%H%M")

    # load yaml (database, recommender)
    db_config = load_config(args.db_cfg_path)
    rk_config = load_config(args.rk_cfg_path)

    # build recommend dataloader
    dataloader = RecDataLoader(db_config, rk_config)

    # build rankfilter
    rankfilter = RankFilterModel(dataloader, rk_config)
    recommend_info = rankfilter.fit()

    # submit to backend
    submit_to_backend(recommend_info, db_config)

    # submit to bucket
    submit_to_bucket(recommend_info, db_config, datetime_now)
    return



if __name__ == '__main__':
    args = arg_parse()
    main(args)
    quit()

