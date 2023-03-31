from loguru import logger


class Logging:
    def __init__(self, service_names=str, log_path=str, retention='7 days', rotation='1 days'):
        self.log_path = log_path
        self.logger_obj = self.add_log_file(file_name=service_names, retention=retention, rotation=rotation)

    def add_log_file(self, file_name=str, retention='7 days', rotation='1 days'):
        log_file_path = self.log_path + file_name + '.log'
        logger.add(log_file_path, retention=retention, rotation=rotation, enqueue=True, 
                        filter=lambda x: x['extra']['name']==file_name)
        return logger.bind(name=file_name)

    def add_message(self, message=str):
        self.logger_obj.info(message)
