'''
Reference:
https://fastapi.tiangolo.com/benchmarks/
'''
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from log import Logging
from ml_serving.tv_related_video_recommender import Related_Video
from ml_serving.tv_related_video_recommender import tv_related_video_recommender_func
from ml_serving.tv_related_video_recommender import tv_related_video_recommender_example

# log setting
log_path = 'log/'
loggingA = Logging(service_names='RecommenderLog_A', log_path='log/tv_related_video/')
loggingB = Logging(service_names='TESTLog_B', log_path='log/test/')


def create_app() -> FastAPI:
    # create and configure the application
    application = FastAPI(
        title='API Recommendation',
        description='Recommendation System',
    )
    origins = [
        '*'
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    return application


# init app
app = create_app()


@app.post('/tv_recommender/related_video_recommender', response_model=Related_Video, summary="Who is Pekora? Pekopeko~~") 
async def tv_related_video_recommender(input_info: Related_Video=tv_related_video_recommender_example):
    """
    PARAMETERS:

    - **hit**: The amount of recommended video. default=20
    - **work_id**: Video id. default=-1
    - **user_id**: User id. default=-1
    - **dynamic**: Dynamic recommend. default=false
    - **dynamic_hit**: The amount of dynamic recommend. default=5
    - **debug**: Detailed message. default=false

    model : view-also-view algorithm + magic pekora~~
    """
    input_info = input_info.dict()
    response_data, status_code = tv_related_video_recommender_func(input_info, loggingA)
    response_data = jsonable_encoder(response_data)
    return JSONResponse(content=response_data, status_code=status_code)


@app.post('/test')
async def test(message):
    """
    this is test api.
    """
    import json
    import requests
    slack_url = 'https://hooks.slack.com/services/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?text="123"'
    info = {
        'text': f'Pekopeko~~~(message: {message})'}
    headers = {'Content-Type': 'application/json'}
    obj = requests.post(slack_url, data=json.dumps(info), headers=headers)
    print(obj.text)
    loggingB.add_message(message)
