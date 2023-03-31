"""utils"""
import time
import yaml
import json
import logging
import numpy as np
#from gridfs import GridFS
from bson import json_util
from datetime import datetime



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


def write_to_db(data, collect, db_write, log_save_path, batch_size=1024, useGridFS=False):
    """write_to_db

    write data to database

    Args:
        data (list)
        collect : collect name
        db_write : database object
        log_save_path
        batch_size
        GridFS
    """
    # if data need to use GridFS
    if useGridFS is True:
        mongo_girdfs = GridFS(db_write)
        for record in data:
            for _ in range(5):
                try:
                    f = json_util.dumps(data[0]).encode("utf8")
                    file_id = mongo_girdfs.put(f)
                    break
                except Exception as error_message:
                    add_log_record(\
                        error_message, 'recommender', log_save_path)   
        return
    # if not GridFS
    batch_data = []
    for i, record in enumerate(data):
        if i == 0 or i % batch_size != 0:
            batch_data += [record]
        if i % batch_size == 0 or i == len(data) - 1 :
            for _ in range(1):
                try:
                    db_write[collect].insert_many(batch_data)
                    break
                except Exception as error_message:
                    add_log_record(\
                        error_message, 'recommender', log_save_path)
            # init batch_data
            batch_data = []



def remove_all_to_db(collect ,db_write, log_save_path):
    for _ in range(5):
        try:
            db_write[collect].delete_many({})
            break
        except Exception as error_message:
            add_log_record(\
                error_message, 'recommender', log_save_path)




def UniformSample_original(dataset, neg_ratio = 1, sample_ext=False):
    allPos = dataset.allPos
    if sample_ext:
        S = sampling.sample_negative(dataset.n_users, dataset.m_items,
                                     dataset.trainDataSize, allPos, neg_ratio)
    else:
        S = UniformSample_original_python(dataset)
    return S


def UniformSample_original_python(dataset):
    """negative sampling
    """
    total_start = time.time()
    user_num = dataset.trainDataSize
    users = np.random.randint(0, dataset.n_users, user_num)
    allPos = dataset.allPos
    
    S = []
    for i, user in enumerate(users):
        start = time.time()
        posForUser = allPos[user]
        if len(posForUser) == 0:
            continue
        posindex = np.random.randint(0, len(posForUser))
        positem = posForUser[posindex]
        while True:
            negitem = np.random.randint(0, dataset.m_items)
            if negitem in posForUser:
                continue
            else:
                break
        S.append([user, positem, negitem])
        end = time.time()

    total = time.time() - total_start
    return np.array(S)


def set_seed(seed): 
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.manual_seed(seed)


def getFileName(rs_config):
    lightGCN_n_layers = rs_config['model']['lightGCN_n_layers']
    latent_dim_rec = rs_config['model']['latent_dim_rec']
    save_path = rs_config['model']['save_path']
    file = f"{save_path}/lgn-{lightGCN_n_layers}-{latent_dim_rec}.pth.tar"
    return file

 
def minibatch(*tensors, **kwargs):
    batch_size = kwargs.get('batch_size', 32)
    if len(tensors) == 1:
        tensor = tensors[0]
        for i in range(0, len(tensor), batch_size):
            yield tensor[i:i + batch_size]
    else:
        for i in range(0, len(tensors[0]), batch_size):
            yield tuple(x[i:i + batch_size] for x in tensors)


def shuffle(*arrays, **kwargs):

    require_indices = kwargs.get('indices', False)

    if len(set(len(x) for x in arrays)) != 1:
        raise ValueError('All inputs to shuffle must have '
                         'the same length.')

    shuffle_indices = np.arange(len(arrays[0]))
    np.random.shuffle(shuffle_indices)

    if len(arrays) == 1:
        result = arrays[0][shuffle_indices]
    else:
        result = tuple(x[shuffle_indices] for x in arrays)

    if require_indices:
        return result, shuffle_indices
    else:
        return result

 
class timer:
    """
    Time context manager for code block
        with timer():
            do something
        timer.get()
    """
    from time import time
    TAPE = [-1]  # global time record
    NAMED_TAPE = {}

    @staticmethod
    def get():
        if len(timer.TAPE) > 1:
            return timer.TAPE.pop()
        else:
            return -1

    @staticmethod
    def dict(select_keys=None):
        hint = "|"
        if select_keys is None:
            for key, value in timer.NAMED_TAPE.items():
                hint = hint + f"{key}:{value:.2f}|"
        else:
            for key in select_keys:
                value = timer.NAMED_TAPE[key]
                hint = hint + f"{key}:{value:.2f}|"
        return hint

    @staticmethod
    def zero(select_keys=None):
        if select_keys is None:
            for key, value in timer.NAMED_TAPE.items():
                timer.NAMED_TAPE[key] = 0
        else:
            for key in select_keys:
                timer.NAMED_TAPE[key] = 0

    def __init__(self, tape=None, **kwargs):
        if kwargs.get('name'):
            timer.NAMED_TAPE[kwargs['name']] = timer.NAMED_TAPE[
                kwargs['name']] if timer.NAMED_TAPE.get(kwargs['name']) else 0.
            self.named = kwargs['name']
            if kwargs.get("group"):
                #TODO: add group function
                pass
        else:
            self.named = False
            self.tape = tape or timer.TAPE

    def __enter__(self):
        self.start = timer.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.named:
            timer.NAMED_TAPE[self.named] += timer.time() - self.start
        else:
            self.tape.append(timer.time() - self.start)


def RecallPrecision_ATk(test_data, r, k):
    """
    test_data should be a list? cause users may have different amount of pos items. shape (test_batch, k)
    pred_data : shape (test_batch, k) NOTE: pred_data should be pre-sorted
    k : top-k
    """
    right_pred = r[:, :k].sum(1)
    precis_n = k
    recall_n = np.array([len(test_data[i]) for i in range(len(test_data))])
    recall = np.sum(right_pred/recall_n)
    precis = np.sum(right_pred)/precis_n
    return {'recall': recall, 'precision': precis}


def MRRatK_r(r, k):
    """
    Mean Reciprocal Rank
    """
    pred_data = r[:, :k]
    scores = np.log2(1./np.arange(1, k+1))
    pred_data = pred_data/scores
    pred_data = pred_data.sum(1)
    return np.sum(pred_data)


def NDCGatK_r(test_data,r,k):
    """
    Normalized Discounted Cumulative Gain
    rel_i = 1 or 0, so 2^{rel_i} - 1 = 1 or 0
    """
    assert len(r) == len(test_data)
    pred_data = r[:, :k]

    test_matrix = np.zeros((len(pred_data), k))
    for i, items in enumerate(test_data):
        length = k if k <= len(items) else len(items)
        test_matrix[i, :length] = 1
    max_r = test_matrix
    idcg = np.sum(max_r * 1./np.log2(np.arange(2, k + 2)), axis=1)
    dcg = pred_data*(1./np.log2(np.arange(2, k + 2)))
    dcg = np.sum(dcg, axis=1)
    idcg[idcg == 0.] = 1.
    ndcg = dcg/idcg
    ndcg[np.isnan(ndcg)] = 0.
    return np.sum(ndcg)


def AUC(all_item_scores, dataset, test_data):
    """
        design for a single user
    """
    dataset : BasicDataset
    r_all = np.zeros((dataset.m_items, ))
    r_all[test_data] = 1
    r = r_all[all_item_scores >= 0]
    test_item_scores = all_item_scores[all_item_scores >= 0]
    return roc_auc_score(r, test_item_scores)


def getLabel(test_data, pred_data):
    r = []
    for i in range(len(test_data)):
        groundTrue = test_data[i]
        predictTopK = pred_data[i]
        pred = list(map(lambda x: x in groundTrue, predictTopK))
        pred = np.array(pred).astype("float")
        r.append(pred)
    return np.array(r).astype('float')



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
    formatter = logging.Formatter(f'{now_datetime} : %(message)s')
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


