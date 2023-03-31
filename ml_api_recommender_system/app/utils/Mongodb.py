import time
from pymongo import MongoClient


class MongodbConnector:
    def __init__(self, connect_yml=dict, database_name=str):
        self.db_ = MongoClient(**connect_yml)[database_name]
        print(self.db_)

    def dump(self, data, collect, batch_size=128):
        batch_data = []
        data += [None]
        for i, record in enumerate(data):
            if record is not None: 
                if i == 0 or i % batch_size != 0:
                    batch_data += [record]
                else:
                    for _ in range(5):
                        try:
                            self.db_[collect].insert_many(batch_data)
                            break
                        except:
                            time.sleep(3)
                    # init batch_data
                    batch_data = []
            else:
                self.db_[collect].insert_many(batch_data)

    def read(self, collect, query={}):
        data = list(self.db_[collect].find(query))
        return data


if __name__ == '__main__':
    conn = {
        'host': '13.229.93.144',
        'username': 'admin',
        'password': 'admin',
        'port': 27017,
        'connectTimeoutMS': 3000
    }
    mongo_conn = MongodbConnector(conn, database_name='tv_test')
    data = [{
        'content_id': 123,
        'candidate_content_ids' : [234, 345,456]},
        {
        'content_id': 123,
        'candidate_content_ids' : [234, 345,456]
        }
    ]
    mongo_conn.dump(data, collect='item2item_rank', batch_size=128)
