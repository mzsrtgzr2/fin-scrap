import yaml


def load_config():
    with open('config.yml', 'r') as keyfile:
        return yaml.safe_load(keyfile)
