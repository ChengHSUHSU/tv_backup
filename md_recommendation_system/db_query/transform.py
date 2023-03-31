"""transform data"""
import pandas as pd





def transform_data(data, collect, db_, cl_config):
    """Transform data

    target data left join with right collection data
    and these right collection data determined by collection.yaml

    Args:
        data (list) : it is main data.
        collect (str) : it is collection name of main data.
        db_ (pymongo object) : it is mongo database object
        cl_config (dict) : it builds by collection.yaml
    """

    if collect in cl_config['join_mapping']:
        # build data_dat
        columns = cl_config['collections']['columns'][collect]
        data_dat = pd.DataFrame(data)[columns]

        # left join for each right collect
        for r_collect_obj in cl_config['join_mapping'][collect]:

            # right collect
            r_collect = r_collect_obj['collect']

            # primary key (left collect)
            left_key = r_collect_obj['left_key']

            # added_columns
            added_columns = r_collect_obj['added_columns']

            # build r_data_dat
            r_data_dat = pd.DataFrame(list(
                db_[r_collect].find()))[added_columns]

            # build id2data
            id2data = build_id2data(r_collect_obj, r_data_dat, cl_config)

            # left join
            if r_collect_obj['format'] == 'list':
                # pylint: disable=cell-var-from-loop
                data_dat[f'{left_key}-data'] = \
                    data_dat[left_key].apply(lambda records: left_join_func(records, id2data))

            elif r_collect_obj['format'] == 'int':
                # pylint: disable=cell-var-from-loop
                data_dat[f'{left_key}-data'] = \
                    data_dat[left_key].apply(lambda records: left_join_func([records], id2data))

        # mapping original id name into new id name
        remove_columns = []
        id_name_mappings = cl_config['collections']['id_name'][collect]
        for id_n_mp in id_name_mappings:
            old = id_n_mp['old']
            new = id_n_mp['new']
            data_dat[new] = data_dat[old]
            remove_columns += [old]
        data_dat = data_dat.drop(columns=remove_columns)

        return data_dat.to_dict('records')
    return data


def build_id2data(r_collect_obj, r_data_dat, cl_config):
    """build_id2data

    build mapping (id to meta-data)

    Args:
        r_collect_obj (dict) : collection info
        r_data_dat (DataFrame) : meta-data dataframe
        cl_config (dict) : collection config
    """
    # init
    id2data = {}
    collect = r_collect_obj['collect']
    right_key = r_collect_obj['right_key']
    hard_code = r_collect_obj['hard_code']

    if not hard_code:
        for record in r_data_dat.to_dict('records'):
            id_ = record[right_key]
            id2data[id_] = record
    else:
        id2data = cl_config['hard_code_mapping'][collect]

    return id2data


def left_join_func(records, id2data):
    """left_join_func

    It can left join meta-data table with main table.

    Args:
        records (list) :  it is ids (ex. TagId of media table)
        id2data (dict) :  it is mapping (key: id, value: meta-data)
    """
    output = []
    if isinstance(records, list):
        for id_ in records:
            if id_ in id2data:
                output.append(id2data[id_])
            else:
                output.append(None)
    return output
