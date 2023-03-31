"""Run Recommendation System"""
import argparse
from pymongo import MongoClient
from models import modeler
from train import trainer
from preprocess import dataprocess, dataloader
from inference import inferencer
from utils import load_config, write_to_db, remove_all_to_db






def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_cfg_path',
                        help='database config setting path.',
                        type=str,
                        default='./recommender/config/query.yaml')

    parser.add_argument('--rs_cfg_path',
                        help='recommender config setting path.',
                        type=str,
                        default='./recommender/config/recsym.yaml')

    parser.add_argument('--inferencer',
                        help='the module of trainer.',
                        type=str,
                        default='PersonalizeInferencer')

    parser.add_argument('--query_start',
                        help='query start',
                        type=str,
                        default='2022-11-05')

    parser.add_argument('--query_end',
                        help='query end',
                        type=str,
                        default='2022-11-15')

    parser.add_argument('--write_to_db',
                        help='write to database ?!',
                        action="store_true")

    return parser.parse_args()




def main(args):
    # load yaml (database, recommender)
    db_config = load_config(args.db_cfg_path)
    rs_config = load_config(args.rs_cfg_path)

    # add query date to rs_config
    rs_config['dataprocess']['query_start'] = args.query_start
    rs_config['dataprocess']['query_end'] = args.query_end

    # build train, inference info
    dpr = getattr(dataprocess, rs_config['dataprocess']['func'])(db_config, rs_config)

    train_info = dpr.build_train_info()
    inference_info = dpr.build_inference_info()

    # build dataset
    dataset = getattr(dataloader, rs_config['dataloader']['func'])(train_info, rs_config)

    # model
    model = getattr(modeler, rs_config['model']['func'])(dataset, rs_config)

    # modeling and save
    pr_trainer = getattr(trainer, rs_config['trainer']['func'])(model, dataset, rs_config)
    pr_trainer.fit()
    pr_trainer.save_model()

    # test
    args.write_to_db = True

    # write to database
    if args.write_to_db is True:
       # inference
        infr = getattr(inferencer, \
                rs_config['inference']['func'])(model, inference_info, rs_config)
        inference_result = infr.build_inference_result()

        # init database (write)
        database = rs_config['query_settings']['write']['database']
        cl_name_mapping = rs_config['write_to_db']
        infh_db_name = rs_config['query_settings']\
                    ['write']['database_GridFS']['inference_history']

        db_write = MongoClient(**db_config['connect_settings']['write'])[database]
        infh_db_write = MongoClient(**db_config['connect_settings']['write'])[infh_db_name]

        # log path
        log_save_path = rs_config['log']['save_path']

        for inf_name in list(inference_result.keys()):
            if '/' in inf_name:
                cl_name = inf_name
            else:
                cl_name = cl_name_mapping[inf_name]['collect']
            inf_result_ = inference_result[inf_name]
            remove_all_to_db(cl_name, db_write, log_save_path)
            # write to database (inference)
            write_to_db(inf_result_, cl_name, db_write, log_save_path)
            # # write to database (inference_history)
            # inf_history_ = infr.build_inference_history(inf_result_)
            # write_to_db([inf_history_], None, infh_db_write, log_save_path, useGridFS=True)






if __name__ == '__main__':
    args = arg_parse()
    main(args)
    quit()
