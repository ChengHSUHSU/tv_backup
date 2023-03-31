

import yaml



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







