



import pymysql.cursors

db_config = {
    'host': 'modeltv-release-aurora.cluster-ro-ckosb3gyldzv.ap-northeast-1.rds.amazonaws.com',
    'user': 'admin',
    'password': '3fmXH6zys7spvu9e',
    'database': 'model_tv',
    'port': 3306
    }

db_config['cursorclass']  = pymysql.cursors.DictCursor

connection = pymysql.connect(**db_config)


'''
# hostname = modeltv-release.cluster-ro-ckosb3gyldzv.ap-northeast-1.rds.amazonaws.com
hostname = modeltv-release-aurora.cluster-ro-ckosb3gyldzv.ap-northeast-1.rds.amazonaws.com
username = admin
password = 3fmXH6zys7spvu9e
database = model_tv
port = 3306
'''


with connection.cursor() as cursor:
    # Read a single record
    sql = "SELECT * FROM model_tv.works"
    cursor.execute(sql)
    result = cursor.fetchall()
    for record in result:
        print(record)

quit()










