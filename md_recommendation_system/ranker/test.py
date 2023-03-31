

import requests

'https://xindong.sgp-develop.com/api/web/media/recommend/sync'
backend_api_url = 'https://api.hlbj.me/api/web/media/recommend/sync'

batch_data = []
batch_data.append({'userId': 46844, 'mediaIds': [13561, 13541]})
body = {'data': batch_data}

x = requests.post(backend_api_url, json = body)
print(x.text)
