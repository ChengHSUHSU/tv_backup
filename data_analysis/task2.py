


'''
data_team/watch_history/MDTVxx.csv
(time, device, city, region, user_id)
DashboardData/sccuess_order.csv (11/16`11/17 成功訂閱 )  (user_id, success_order.id left_join)
STAT : groupy by device, city, region  幾個人
'''

import pandas as pd


MDTV_Watch_ds_dat = pd.read_csv('MDTV_Watch_ds.csv')
success_order_dat = pd.read_csv('success_order.csv')

# filetr
MDTV_Watch_ds_dat = MDTV_Watch_ds_dat[['time', '$device', '$city', '$region', '$user_id']]
success_order_dat = success_order_dat[['id', 'status', 'created_at']]




success_order_dat_filter = success_order_dat[(success_order_dat['created_at'] >= '2022-11-21') \
                                & (success_order_dat['created_at'] <= '2022-11-27')]

print(success_order_dat_filter.shape)
# filter new subscribe user
old_id_set = set(success_order_dat[(success_order_dat['created_at'] < '2022-11-21')]['id'])
success_order_dat_filter = success_order_dat_filter[~success_order_dat_filter['id'].isin(old_id_set)]




# duplicate id
MDTV_Watch_ds_dat['id'] = MDTV_Watch_ds_dat['$user_id']



# left join
dat = success_order_dat_filter.merge(MDTV_Watch_ds_dat, on='id', how='left')

# fill na data
dat = dat.fillna('NAN')

# group by $device
dat_ = dat.groupby(['$device']).count()[['status']]
dat_['count'] = dat_['status']
dat_ = dat_.drop(columns=['status'])
dat_.to_csv('2127$device_count.csv')


# group by $city
dat_ = dat.groupby(['$city']).count()[['status']]
dat_['count'] = dat_['status']
dat_ = dat_.drop(columns=['status'])
dat_.to_csv('2127$city_count.csv')

# group by $region
dat_ = dat.groupby(['$region']).count()[['status']]
dat_['count'] = dat_['status']
dat_ = dat_.drop(columns=['status'])
dat_.to_csv('2127$region_count.csv')

