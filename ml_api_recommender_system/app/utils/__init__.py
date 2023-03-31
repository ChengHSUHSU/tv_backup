import yaml
import json
import requests


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


def send_message_to_slack(message: str):
    '''
    due to limited time, we adopt hard-code parameter.
    '''
    slack_url = 'https://hooks.slack.com/services/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?text="123"'
    info = {
        'text': f'Pekopeko~~~(message: {message})'}
    headers = {'Content-Type': 'application/json'}
    obj = requests.post(slack_url, data=json.dumps(info), headers=headers)
    print(obj.text)
