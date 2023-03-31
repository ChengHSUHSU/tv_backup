import pandas as pd
from databricks import sql as databricks_sql


class DataBricksConnector:
    def __init__(self, connect_yml: dict):
        self.sql_connect_cfg = {
                'server_hostname': connect_yml['DATABRICKS_SERVER_HOSTNAME'],
                'http_path': connect_yml['DATABRICKS_HTTP_PATH'],
                'access_token': connect_yml['DATABRICKS_TOKEN']
                }

    def sql_query(self, sql: str, col_names: list):
        # query
        with databricks_sql.connect(**self.sql_connect_cfg) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    sql_result = cursor.fetchall()
                except:
                    sql_result = []
        # query_data
        query_data = dict()
        for col in col_names:
            query_data[col] = []
        
        for i in range(len(sql_result)):
            if len(sql_result[i]) == len(col_names):
                for j in range(len(col_names)):
                    query_data[col_names[j]].append(sql_result[i][j])
        query_data = pd.DataFrame(query_data)
        print(query_data.head(5))
        return query_data


if __name__ == '__main__':
    DATABRICKS_SERVER_HOSTNAME = 'dbc-55a1270e-3e1b.cloud.databricks.com'
    DATABRICKS_HTTP_PATH = 'sql/protocolv1/o/6624368804643013/1122-010506-r1raujkz'
    DATABRICKS_TOKEN = 'dapi304cb9a1e3d03fb38e959cb151ac844f'
    connect_yml = {
        'DATABRICKS_SERVER_HOSTNAME': DATABRICKS_SERVER_HOSTNAME,
        'DATABRICKS_HTTP_PATH': DATABRICKS_HTTP_PATH,
        'DATABRICKS_TOKEN': DATABRICKS_TOKEN
    }

    col_names = ['user_id', 'plan_id', 'started_at', 'ended_at']
    sql = "select user_id, plan_id, started_at, ended_at from sql.subscriptions LIMIT 10"

    databricks_connector = DataBricksConnector(connect_yml)
    dat = databricks_connector.sql_query(sql, col_names)
    print(dat)
