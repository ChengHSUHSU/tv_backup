from utils import load_config
from abc import ABCMeta, abstractmethod


class Reader(metaclass=ABCMeta):
    def __init__(self, cfg=dict):
        self.cfg = cfg
        self.connect_cfg = load_config(cfg.connect_cfg_path)
        self.option_cfg = load_config(cfg.option_cfg_path)
        self.reader_cfg = self.option_cfg['reader']

    @abstractmethod
    def get_event_data(self):
        pass

    @abstractmethod
    def get_content_data(self):
        pass

    def read_sql(self, sql_path=str):
        with open(sql_path, 'r') as f:
            sql = f.read()
        print(f'sql_path : {sql_path}')
        print(sql)
        return sql

    def is_integer(self, val):
        try:
            int(val)
            return True
        except:
            return False

    def dataframe_only_interger(self, dataframe, col=str):
        integer_vals = [val for val in list(dataframe[col]) \
                                    if self.is_integer(val) is True]
        dataframe = dataframe[dataframe[col].isin(integer_vals)]
        return dataframe
