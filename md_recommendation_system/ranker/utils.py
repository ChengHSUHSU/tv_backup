

import yaml
import boto3
import time
import requests
import pandas as pd




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



def submit_to_backend(recommend_info, db_config):
    #{'userId': 33088, 'rank_itemId': [950
    #recommend_info = {'user_item_rank' : [], 'contentType' : []}
    batch_data = []
    submit_backend_info = db_config['submit_to_backend']
    batch_size = submit_backend_info['batch_size']
    backend_api_url = submit_backend_info['backend_api_url']
    backend_userId = submit_backend_info['backend_userId']
    backend_rank_itemId = submit_backend_info['backend_rank_itemId']

    # user_item_rank
    user_item_rank = recommend_info['user_item_rank']

    for i, record in enumerate(user_item_rank): 
        userId = record['userId']
        rank_itemId = record['rank_itemId']
        rank_itemId = []
        batch_data.append(\
            {backend_userId: userId, backend_rank_itemId: rank_itemId}\
            )
        if len(batch_data) == batch_size or i == len(user_item_rank) - 1:
            body = {'data': batch_data}
            for _ in range(15):
                try:
                    x= requests.post(backend_api_url, json = body)
                    print(x.text)
                    x = dict(x.json())
                    if x['code'] != 200:
                        for record_ in batch_data:
                            body = {'data': [record_]}
                            x= requests.post(backend_api_url, json = body)
                            x = dict(x.json())
                            if x['code'] != 200:
                                print(body)
                                print('====')
                    batch_data = []
                    time.sleep(5)
                    break
                except Exception as error_message:
                    print('[Error][BackendAPI] : ', error_message)
                    time.sleep(5)
       


def submit_to_bucket(recommend_info, db_config, datetime_now=None):
    # parameter
    access_info = db_config['bucket_connect_settings']['access_info']
    bucket_info = db_config['bucket_connect_settings']['bucket_info']
    submit_bucket_info = db_config['submit_to_bucket']
    ACCESS_ID = access_info['ACCESS_ID']
    ACCESS_KEY = access_info['ACCESS_KEY']
    BUCKET_NAME = bucket_info['BUCKET_NAME']
    OBJECT_NAME = bucket_info['OBJECT_NAME']

    folder_name = datetime_now.split('-')[0]
    datetime_now = datetime_now.replace('-', '')
    FILE_NAME = f'/{folder_name}/{datetime_now}.csv'
    LOCAL_FILE_NAME = f'{datetime_now}.csv'
    OBJECT_NAME += FILE_NAME

    csv_file_path = submit_bucket_info['csv_file_path']
    prefix_name = submit_bucket_info['prefix_name']
    csv_file_name = prefix_name + LOCAL_FILE_NAME

    # build csv file
    user_item_rank = recommend_info['user_item_rank']
    recommend_dat = pd.DataFrame(user_item_rank)
    recommend_dat.to_csv(csv_file_path + csv_file_name, index=False)

    for _ in range(15):
        try:
            # init client cli
            s3 = boto3.client('s3',
                    aws_access_key_id=ACCESS_ID,
                    aws_secret_access_key= ACCESS_KEY)

            # upload_file
            response = s3.upload_file(\
                csv_file_path+csv_file_name, BUCKET_NAME, OBJECT_NAME)
            print('response : ', response)
            break
        except:
            time.sleep(5)
