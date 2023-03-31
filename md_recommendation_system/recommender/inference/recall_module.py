

import random





def zfl_recall_layer(items_score, inference_info, rs_config, platform):
    # init
    warm_rate = rs_config['dataprocess']['warm_rate']
    inference_topK = rs_config['dataprocess']['inference_topK']
    hard_pos_score = rs_config['dataprocess']['hard_pos_score']
    soft_pos_score = rs_config['dataprocess']['soft_pos_score']
    warm_topK = int(inference_topK * warm_rate)
    cold_topK = inference_topK - warm_topK

    # inference_info
    idx_item = inference_info['idx_item']
    cold_item_set = inference_info['cold_item_set']

    # build hard_pos, soft_pos, neg
    item_id_hard_pos, item_id_soft_pos, item_id_neg = [], [], []

    for item_idx, score in enumerate(items_score):
        # reindex (item)
        item_id = idx_item[item_idx]
        # filter by hard / soft score
        if score > hard_pos_score:
            item_id_hard_pos.append(item_id)
        elif soft_pos_score <= score <= hard_pos_score:
            item_id_soft_pos.append(item_id)
        else:
            item_id_neg.append(item_id)
                    
        # when item_id_hard_pos.length >= warm_topK, break
        if len(item_id_hard_pos) >= warm_topK:
            break

    # build item_warm_rank
    item_warm_rank = item_id_hard_pos + item_id_soft_pos + item_id_neg

    # build item_cold_rank
    item_cold_rank = zfl_cold_inference(\
            item_warm_rank, inference_info, cold_topK, rs_config)

    # item_rank
    item_rank = item_warm_rank[:warm_topK] + item_cold_rank[:cold_topK]

    if platform == 'Random':
        item_rank = random.sample(item_rank, len(item_rank))

    return item_rank




def zfl_cold_inference(item_warm_rank, inference_info, cold_topK, rs_config):
    # init
    warm_num = rs_config['dataprocess']['cold_inference']['warm_num']
    cold_inf_features = rs_config['dataprocess']['cold_inference']['features']

    # inference_info
    idx_item = inference_info['idx_item']
    item2idx = inference_info['item2idx']
    item_data = inference_info['item_data']
    cold_item_set = inference_info['cold_item_set']

    cold_item_pos, cold_item_neg = [], []
    cold_item_list = list(cold_item_set)
    item_warm_rank_top = item_warm_rank[:warm_num]

    for c_idx in cold_item_list:
        score = 0
        # reindex (item)
        c_id = idx_item[c_idx]
        # cold item features
        for f in cold_inf_features:
            c_f = item_data[c_idx][f]

            if len(c_f) != 0:
                for w_id in item_warm_rank_top:
                    # reindex (item)
                    w_idx = item2idx[w_id]
                    # warm item tags
                    w_f = item_data[w_idx][f]
                    # score
                    # score += len(c_f & w_f)
                    if len(c_f & w_f) > 0:
                        score += 1
                        break
        # cold_item_pos, cold_item_neg
        if score > 0:
            cold_item_pos.append(c_id)
        else:
            cold_item_neg.append(c_id)

        # when the number of cold_item_pos >= cold_topK
        if len(cold_item_pos) >= cold_topK:
            break
    item_cold_rank = cold_item_pos + cold_item_neg
    return item_cold_rank


