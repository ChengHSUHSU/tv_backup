



import pandas as pd


# load data
coupons_dat = pd.read_csv('coupons.csv')
subscriptions_dat = pd.read_csv('subscriptions.csv')
success_order_dat = pd.read_csv('success_order.csv')


# 來算前三個欄位

# duplicate coupon_id
coupons_dat['coupon_id'] = coupons_dat['id']
coupons_dat['coupon_name'] = coupons_dat['name']
coupons_dat = coupons_dat[['coupon_id', 'coupon_name']]


# subscriptions_dat
subscriptions_dat['date'] = subscriptions_dat['created_at']
subscriptions_dat = subscriptions_dat[['user_id', 'coupon_id', 'date']]



# remove null
subscriptions_dat = subscriptions_dat.dropna()


# ex. 2022-11-18 23:09:15+08:00 => 2022-11-18
subscriptions_dat['date'] = \
            subscriptions_dat['date'].apply(lambda x: str(x).split()[0])

# filter by (2022-11-18 ~ 2022-11-27)
subscriptions_dat_filter = subscriptions_dat[(subscriptions_dat['date'] >= '2022-11-18') \
                                & (subscriptions_dat['date'] < '2022-11-28')]



# left join
dat = subscriptions_dat_filter.merge(coupons_dat, on='coupon_id', how='left')
dat['number'] = 1


# group by date
dat_ = dat.groupby(['date' ,'coupon_name']).count()[['number']]

'''          
date       coupon_name   number
2022-11-18 行銷_LGBTQ      14
2022-11-19 行銷_LGBTQ      43
2022-11-20 行銷_LGBTQ      24
2022-11-21 行銷_LGBTQ       9
2022-11-22 行銷_LGBTQ      10
2022-11-23 行銷_LGBTQ       8
2022-11-24 行銷_LGBTQ       9
2022-11-25 行銷_LGBTQ       9
2022-11-26 行銷_LGBTQ      11
2022-11-27 行銷_LGBTQ       9
'''

# 來算第四個個欄位

# duplicate user_id
success_order_dat['user_id'] = success_order_dat['id']
success_order_dat['date'] = success_order_dat['created_at']
success_order_dat = success_order_dat[['user_id', 'date', 'amount']]


# ex. 2022-11-18 04:25:22  => 2022-11-18
success_order_dat['date'] = \
            success_order_dat['date'].apply(lambda x: str(x).split()[0])

# filter by date
success_order_dat = success_order_dat[(success_order_dat['date'] >= '2022-11-18') \
                                & (success_order_dat['date'] < '2022-11-28')]

# amount > 5
success_order_dat = success_order_dat[success_order_dat['amount']>5]

# 在18號以後有 兌換券的使用者
exist_user_set = set(subscriptions_dat_filter['user_id'])


dat = success_order_dat[success_order_dat['user_id'].isin(exist_user_set)]
print(dat)

'''
        user_id      date  amount
8287    74198  2022-11-22   749.0
'''

