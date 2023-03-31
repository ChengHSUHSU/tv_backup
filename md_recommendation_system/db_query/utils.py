"""utils"""
import pytz
import json
import yaml
import time
import boto3
import logging
import pandas as pd
from gridfs import GridFS
from datetime import datetime
from dateutil.relativedelta import relativedelta



def load_config(yaml_path):
    """load_config

    it can load yaml config and return 

    Args:
        yaml_path (str) : For example, "./config.yaml"
    """
    # pylint: disable=invalid-name
    # pylint: disable=unspecified-encoding
    with open(yaml_path, mode='r') as f:
        cfg = yaml.safe_load(f)
    return cfg



def write_to_db(data, collect, db_, log_save_path, batch_size=1024, useGridFS=False):
    """write_to_db

    write data to database

    Args:
        data (list)
        collect : collect name
        db_ : database object
        log_save_path
        batch_size
        GridFS
    """
    # if data need to use GridFS
    if useGridFS is True:
        mongo_girdfs = GridFS(db_)
        for record in data:
            for _ in range(5):
                try:
                    file_id = mongo_girdfs.put(json.dumps(record).encode("utf8"))
                    break
                except Exception as error_message:
                    add_log_record(error_message, 'data_pipeline', log_save_path)   
        return
    # if not GridFS
    batch_data = []
    for i, record in enumerate(data):
        if i == 0 or i % batch_size != 0:
            batch_data += [record]
        else:
            for _ in range(5):
                try:
                    db_[collect].insert_many(batch_data)
                    break
                except Exception as error_message:
                    add_log_record(error_message, 'data_pipeline', log_save_path)
            # init batch_data
            batch_data = []
    if len(batch_data) != 0:
        for _ in range(5):
            try:
                db_[collect].insert_many(batch_data)
                break
            except Exception as error_message:
                add_log_record(error_message, 'data_pipeline', log_save_path)



def remove_all_to_db(collect ,db_write, log_save_path):
    for _ in range(5):
        try:
            db_write[collect].delete_many({})
            break
        except Exception as error_message:
            add_log_record(\
                error_message, 'recommender', log_save_path)



def setup_logger(now_datetime, logger_name, log_file, level=logging.INFO):
    """setup_logger

    Set message to log file.

    Args:
        now_datetime (str) : now datetime
        logger_name (str) : always log
        log_file (str) : log path
        level : logging.INFO
    """
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('{} : %(message)s'.format(now_datetime))
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)



def add_log_record(message, task, log_path):
    """add_log_record

    Add log to log-file.

    Args:
        task (str) : task name.
        message (str) : log message.
    """
    now_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    now_date = now_datetime.split()[0]
    setup_logger(now_datetime, 'log', f'{log_path}/{task}@{now_date}.log')
    log = logging.getLogger('log')
    log.info(message)




def get_date_time_zone(date='', adjust_year='0', adjust_month='0', \
                                adjust_day='0', zone='Asia/Taipei'):
    # set time zone
    zone_tz = pytz.timezone(zone)

    # if not input date, then get now
    if date == '':
        date = datetime.now().strftime('%Y-%m-%d')

    # to datatime format
    date_dt = datetime.strptime(date, '%Y-%m-%d')

    # adjust datetime
    # year part
    if '+' in adjust_year:
        date_dt += relativedelta(years=int(adjust_year.replace('+', '')))
    elif '-' in adjust_year:
        date_dt -= relativedelta(years=int(adjust_year.replace('-', '')))

    # month part
    if '+' in adjust_month:
        date_dt += relativedelta(months=int(adjust_month.replace('+', '')))
    elif '-' in adjust_month:
        date_dt -= relativedelta(months=int(adjust_month.replace('-', '')))

    # days part
    if '+' in adjust_day:
        date_dt += relativedelta(days=int(adjust_day.replace('+', '')))
    elif '-' in adjust_day:
        date_dt -= relativedelta(days=int(adjust_day.replace('-', '')))

    # get date_tz
    date_tz = zone_tz.localize(date_dt).astimezone(pytz.utc)
    return date_tz



def submit_to_bucket(data, name, db_config):
    # parameter
    access_info = db_config['bucket_connect_settings']['access_info']
    bucket_info = db_config['bucket_connect_settings']['bucket_info']
    ACCESS_ID = access_info['ACCESS_ID']
    ACCESS_KEY = access_info['ACCESS_KEY']
    BUCKET_NAME = bucket_info['BUCKET_NAME']
    OBJECT_NAME = bucket_info['OBJECT_NAME']
    CSV_FILE_PATH = bucket_info['CSV_FILE_PATH']


    submit_bucket_info = db_config['submit_to_bucket']
    csv_file_path = submit_bucket_info['csv_file_path']
    prefix_name = submit_bucket_info['prefix_name']
    csv_file_name = prefix_name + name+'.csv'

    # build csv file
    data_dat = pd.DataFrame(data)
    data_dat.to_csv(csv_file_path + csv_file_name, index=False)

    for _ in range(15):
        try:
            # init client cli
            s3 = boto3.client('s3',
                    aws_access_key_id=ACCESS_ID,
                    aws_secret_access_key= ACCESS_KEY)

            # upload_file
            response = s3.upload_file(\
                csv_file_path+csv_file_name, BUCKET_NAME, OBJECT_NAME+CSV_FILE_PATH+csv_file_name)
            print('response : ', response)
            break
        except:
            time.sleep(5)

