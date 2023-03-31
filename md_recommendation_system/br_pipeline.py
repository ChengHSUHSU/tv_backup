


import docker

# all
image_name = 'auto_rs/all_pipeline'


# # db_query
# db_query_python_cmd = '''
#     python3 db_query/run.py 
# '''
# db_query_container_name = 'db_query_run'


# input('start db_query.....')

# client = docker.from_env()
# container = client.containers.run(image=image_name,
#                                   command=db_query_python_cmd,
#                                   network_mode='bridge',
#                                   remove=True,
#                                   detach=True,
#                                   name=db_query_container_name)
# container.logs()


# # recommender
# recommender_python_cmd = '''
#     python3 recommender/run.py 
# '''
# recommender_container_name = 'recommender_run'

# input('start recommender.....')


# client = docker.from_env()
# container = client.containers.run(image=image_name,
#                                   command=recommender_python_cmd,
#                                   network_mode='bridge',
#                                   remove=False,
#                                   detach=True,
#                                   name=recommender_container_name)
# container.logs()



# ranker
ranker_python_cmd = '''
    python3 ranker/run.py 
'''
ranker_container_name = 'ranker_run'

input('start ranker.....')


client = docker.from_env()
container = client.containers.run(image=image_name,
                                  command=ranker_python_cmd,
                                  network_mode='bridge',
                                  remove=False,
                                  detach=True,
                                  name=ranker_container_name)
container.logs()




