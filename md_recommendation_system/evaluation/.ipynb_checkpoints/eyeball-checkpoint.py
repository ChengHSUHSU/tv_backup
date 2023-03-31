


from utils import load_config, MongoDBSession





# parameter
query_cfg_path = './config/query.yaml'
topK = 10


# load query config
query_config = load_config(query_cfg_path)


# init mongoDB
mongodb_session = MongoDBSession(query_config['connect_settings'])
database_names = mongodb_session.database_names


# get xindong.media(my)(id, title, tags)
mongodb_session.init_db(db_name='xindong')
media_cl = mongodb_session.query(collect_name='media')


# build item2info
item2info = dict()
for record in media_cl:
    item2info[record['ITEM_ID']] = {
                        'title' : record['title'],
                        'tags' : record['tags-data']
                        }


# get All/user2meta_history data
mongodb_session.init_db(db_name='xindong_inference')
user2meta_history_cl = mongodb_session.query(collect_name='All/user2meta_history')


# build user2meta_history
user2meta_history = dict()
for record in user2meta_history_cl:
    user2meta_history[record['USER_ID']] = record['meta_history']



# get recommend results
mongodb_session.init_db(db_name='xindong_inference')
item2item_rank_cl = mongodb_session.query(collect_name='All/item2item_rank')
recommend_results = item2item_rank_cl[:]


# save to pickle


# main
history_user = list()
for record in recommend_results:
    meta_history = user2meta_history[record['USER_ID']]
    print('user_id : ', record['USER_ID'])
    # meta item
    for item_id in meta_history:
        print('meta_item : ', item_id)
        print('meta_item(title) : ', item2info[item_id]['title'])
        print('meta_item(tags) : ', item2info[item_id]['tags'])
        print('-----------------------')
    # rec item
    for item_id in record['ITEM_ID_RANK'][:topK]:
        print('rec_item : ', item_id)
        print('rec_item(title) : ', item2info[item_id]['title'])
        print('rec_item(tags) : ', item2info[item_id]['tags'])
        print('-----------------------')  
    history_user.append(record['USER_ID'])
    input('====================================')
    







