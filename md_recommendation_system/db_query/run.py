"""query database"""
import argparse
from datetime import datetime
from pymongo import MongoClient
from transform import transform_data
from utils import get_date_time_zone
from utils import load_config, add_log_record
from utils import write_to_db, remove_all_to_db, submit_to_bucket
from dump import dump_dataset





def arg_parse():
    """arg_parse

    argument setting.

    Args:
        .
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_cfg_path',
                        type=str,
                        help='database config setting path.',
                        default='./db_query/config/query.yaml')
    parser.add_argument('--cl_cfg_path',
                        type=str,
                        help='collection config setting path.',
                        default='./db_query/config/collection.yaml')
    parser.add_argument('--query_start',
                        type=str,
                        help='query start time',
                        default='2022-11-02')
    parser.add_argument('--query_end',
                        type=str,
                        help='query start time',
                        default='2022-11-03')
    parser.add_argument('--write_to_db',
                        type=bool,
                        help='write to database',
                        default=True)

    return parser.parse_args()



def parse_mongo_data(args):
    """parse_mongo_data

    collect hiostory data and user / item meta-data

    Args:
        args (dict) : it contains config path, query-start and query-end
    """
    # build query start / end time
    query_start_tz = get_date_time_zone(args.query_start)
    query_end_tz = get_date_time_zone(args.query_end)

    # load mongoDB config
    # (pylint: disable=unspecified-encoding)
    db_config = load_config(args.db_cfg_path)

    # load collection config
    cl_config = load_config(args.cl_cfg_path)

    # log path
    log_save_path = cl_config['log']['save_path']

    # init mongoDB (read)
    database_name = cl_config['query_settings']['database']
    db_ = MongoClient(**db_config['connect_settings']['read'])[database_name]

    # query data and save
    for collect in cl_config['collections']['names']:

        # build nosql-query
        time_query = cl_config['collections']['time_query']
        time_query_info = time_query[collect]

        # query data
        print(f'query data for collect({collect})...')
        for _ in range(5):
            try:
                if time_query_info is not None:
                    # query column
                    query_column = time_query_info['col_name']
                    # query start, end
                    query_start_tz = get_date_time_zone(**time_query_info['query_start'])
                    query_end_tz = get_date_time_zone(**time_query_info['query_end'])
                    # nosql query
                    nosql_query = {
                        query_column: {
                            '$gte': query_start_tz,
                            '$lt': query_end_tz
                        }
                    }
                    data = list(db_[collect].find(nosql_query))
                else:
                    data = [x for x in db_[collect].find()]
                break
            except Exception as error_message:
                add_log_record(error_message, 'data_pipeline', log_save_path)

        # transform data (left join main-table with meta-table)
        print('transform data...')
        data = transform_data(data, collect, db_, cl_config)

        # write data to database
        if len(data) > 0:
            # init database (write)
            database_name = cl_config['query_settings']['database']
            db_write = MongoClient(
                **db_config['connect_settings']['write'])[database_name]

            # remove all past data
            remove_all = cl_config['collections']['remove_all'][collect]
            if remove_all is True:
                print(f'Remove collection={collect}...')
                remove_all_to_db(collect, db_write, log_save_path)

            # write to database
            to_database = cl_config['collections']['to_database'][collect]
            if to_database is True:
                print('Write data to DB...')
                write_to_db(data, collect, db_write, log_save_path)

            # submit to bucket
            to_bucket = cl_config['collections']['to_bucket'][collect]
            if to_bucket is True:
                print('Submit data to bucket...')
                submit_to_bucket(data, collect, db_config)



def get_db_data(db_config, cl_config):
    mongo_data, mysql_data = None, None
    return mongo_data, mysql_data



def dataset_preparation(args):
    # database config
    db_config = load_config(args.db_cfg_path)

    # collect config
    cl_config = load_config(args.cl_cfg_path)

    # load data (mysql, mongodb)
    data = get_db_data(db_config, cl_config)

    # transform
    prepared_dataset= transform_data(data)

    # dump result
    dump_dataset(prepared_dataset, db_config, cl_config)






if __name__ == '__main__':
    cfg = arg_parse()
    parse_mongo_data(cfg)
    quit()
