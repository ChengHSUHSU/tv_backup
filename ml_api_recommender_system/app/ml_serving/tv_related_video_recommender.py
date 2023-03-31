import uuid
import random
import traceback
from pydantic import BaseModel
from fastapi import Body, status

from log import Logging
from utils.Mongodb import MongodbConnector 
from utils import load_config, send_message_to_slack


class Related_Video(BaseModel):
    hit: int = 27
    work_id: int = -1
    user_id: int = -1
    dynamic: bool = False
    dynamic_hit: int = 10
    debug: bool = False


def tv_related_video_recommender_func(input_info: dict, logging: Logging):
    # generate unique uuid for the request.
    uuid_ = uuid.uuid1()

    # logging (api-input)
    logging.add_message(f'uuid={uuid_}#(api-input)@'+str(input_info))

    # check api-input
    if input_info['work_id'] == -1 or input_info['hit'] <= 0:
        response_data = {
            'message': 'Fail',
            'hit': -1,
            'recommend_results': [],
            'debug': []
        }
        # logging (api-output)
        logging.add_message(f'uuid={uuid_}#(api-output-A)@'+str(input_info))
        return response_data, status.HTTP_400_BAD_REQUEST

    # parameter
    hit = input_info['hit']
    dynamic = input_info['dynamic']
    dynamic_hit = input_info['dynamic_hit']
    work_id = input_info['work_id'] 
    debug = input_info['debug'] 

    # get related video recommend results
    connector_cfg_path = 'config/item2item/connect.yaml'
    connect_cfg = load_config(connector_cfg_path)
    mongo_conn = MongodbConnector(connect_cfg['mongodb'], database_name='tv_test')

    try:
        item2item_rank = mongo_conn.read(collect='item2item_rank', query={'content_id': str(work_id)})
    except Exception as error:
        item2item_rank = []
        error = traceback.format_exc()
        error_simple = error.replace('\n', ' ')
        logging.add_message(f'uuid={uuid_}#(api-error)@'+str(error_simple))
        send_message_to_slack(error)

    if len(item2item_rank) != 0:
        based_recommend_results = item2item_rank[-1]['candidate_content_ids'].split(',')[:hit]
    else:
        based_recommend_results = []

    # personalization (optional, future)
    recommend_results = based_recommend_results[:]

    # dynamic (shuffle topK items)
    if dynamic is True and len(recommend_results) != 0:
        dynamic_recommend_results = recommend_results[:dynamic_hit]
        fixed_recommend_results = recommend_results[dynamic_hit:]
        dynamic_recommend_results = random.sample(dynamic_recommend_results, dynamic_hit)
        recommend_results = dynamic_recommend_results + fixed_recommend_results

    # response data
    response_data = {
        'message': 'Success',
        'hit': hit,
        'recommend_results': recommend_results,
        'debug': []
    }

    # debug (get content detailed info)
    if debug:
        try:
            # work_id (api-input)
            target_content_data = mongo_conn.read(collect='content_data', query={'content_id': int(work_id)})
            # hash id_ cannot be comsumed
            for i in range(len(target_content_data)):
                del target_content_data[i]['_id']

            # recommended work_id
            if len(recommend_results) > 0:
                or_conditions = [{'content_id': int(content_id)} for content_id in recommend_results]
                source_content_data_ = mongo_conn.read(collect='content_data', query={'$or': or_conditions})
                # sort by recommended order
                source_content_data = []
                for c_id in recommend_results:
                    for record in source_content_data_:
                        if c_id == str(record['content_id']):
                            source_content_data.append(record)
                            break
            else:
                source_content_data = []
            for i in range(len(source_content_data)):
                del source_content_data[i]['_id']
        except Exception as error:
            target_content_data = []
            source_content_data = []
            error = traceback.format_exc()
            error_simple = error.replace('\n', ' ')
            logging.add_message(f'uuid={uuid_}#(api-error)@'+str(error_simple))
            send_message_to_slack(error)

        # add debug to response_data
        if len(target_content_data) > 0:
            response_data['debug'].append(target_content_data[-1])
        if len(source_content_data) > 0 :
            response_data['debug'] += source_content_data

    # logging (api-output)
    logging.add_message(f'uuid={uuid_}#(api-output-B)@'+str(response_data))
    return response_data, status.HTTP_200_OK

# example
tv_related_video_recommender_example = Body(
        examples={
            "standard-caseII": {
                "summary": "example: 你可能會喜歡(A)",
                "description": "點擊影片後，下面的你可能會喜歡",
                "value": {
                    "hit": 27,
                    "work_id": 736,
                    "dynamic": True 
                },
            },
            "standard-caseIII": {
                "summary": "example: 你可能會喜歡(B)",
                "description": "觀賞完影片後，點擊右下角的icon，所跑出的你可能會喜歡．",
                "value": {
                    "hit": 27,
                    "work_id": 736,
                    "dynamic": False 
                },
            },
            "converted-caseI": {
                "summary": "A converted example-caseI",
                "description": "錯誤使用: hit <= 0",
                "value": {
                    "hit": 0,
                    "work_id": 736,
                    "dynamic": False 
                },
            },
            "invalid-caseI": {
                "summary": "A converted example-caseII",
                "description": "錯誤使用: work_id <= 0",
                "value": {
                    "hit": 27,
                    "work_id": -1,
                    "dynamic": False 
                },
            }
        })

