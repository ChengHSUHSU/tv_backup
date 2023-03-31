





def time_query_sp(time_query_column, query_start, query_end):
    nosql_query = {
        time_query_column: {
                '$gte': query_start,
                '$lt': query_end
            }
        }
    return nosql_query



def meta_history_query_sp(service):
    if service == 'xindong':
        nosql_query = {
                'contentType' : {'$in' : [1,2]},
                'historyType' : 2,
            }
    return nosql_query


def item_query_sp(service):
    if service == 'xindong':
        nosql_query = {
                'contentType' : {'$in' : [1,2]}
            }
    return nosql_query





