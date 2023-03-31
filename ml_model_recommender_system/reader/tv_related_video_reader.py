from reader.base_reader import Reader
from utils.Databricks import DataBricksConnector


class TvRelatedVideoReader(Reader):

    def process(self):
        # initial database
        self.initial()

        # get event data
        event_data = self.get_event_data()

        # get content data
        content_data = self.get_content_data()

        raw_data = {
            'event_data': event_data,
            'content_data': content_data
        }
        return raw_data

    def initial(self):
        # databricks
        self.dbricks_conn = DataBricksConnector(self.connect_cfg['databricks'])

    def get_event_data(self):
        # read event sql
        sql_path = self.reader_cfg['get_event_data']['sql_path']
        event_sql = self.read_sql(sql_path)

        # read event data columns
        # 'user_id', 'content_id', 'duration', 'datetime']
        event_data_cols = self.reader_cfg['get_event_data']['event_data_cols']

        # get event data (databricks)
        event_data = self.dbricks_conn.sql_query(event_sql, event_data_cols)

        # to integer and remove no-integer
        remove_not_int_cols = self.reader_cfg['get_event_data']['remove_not_int_cols']
        for col in remove_not_int_cols:
            event_data = self.dataframe_only_interger(event_data, col=col)
            event_data[col] = event_data[col].apply(lambda x: int(x))
        return event_data

    def get_content_data(self):
        # read content sql
        sql_path = self.reader_cfg['get_content_data']['sql_path']
        content_sql = self.read_sql(sql_path)

        # read content data columns
        # ['content_id', 'title', 'introduction', 'published_at', 'series_name', 'episode']
        content_data_cols = self.reader_cfg['get_content_data']['content_data_cols']

        # get content data from databricks
        content_data = self.dbricks_conn.sql_query(content_sql, content_data_cols)

        # to integer and remove no-integer
        remove_not_int_cols = self.reader_cfg['get_content_data']['remove_not_int_cols']
        for col in remove_not_int_cols:
            content_data = self.dataframe_only_interger(content_data, col=col)
            content_data[col] = content_data[col].apply(lambda x: int(x))
        return content_data

    def get_user_data(self):
        return
