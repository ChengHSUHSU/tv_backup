



'''
# 11/11~11/15 上哪些影片 (item.csv -> publish_at)
'''

import pandas as pd


dat = pd.read_csv('item.csv')


dat_filter = dat[(dat['published_at'] >= '2022-11-18 00:00:00') \
                    & (dat['published_at'] < '2022-11-28 00:00:00')]
print(set(dat_filter['name']))

'''
OUTPUT
{'黑絲空姐 貼身服務', '義工', 
'十一假期旅遊性事', '單身鬼父同好會', 
'給室友的驚喜', '女神體育祭ep6', '淫行漫畫王', 
'無料玩具', '爆乳嫩姊秘密性愛', '意猶未盡分手炮', 
'四手聯彈', '11/07~11/13 強檔預告', 'AV女優面試 白皙女大生', 
'爆乳御姐洗浴服務', '課後時光', '11/14~11/18 強檔預告', '任是無情也動人'}
'''

