import os

import yaml


class ConfigError(Exception):
    pass


class ExtendedSafeLoader(yaml.SafeLoader):
    pass


def construct_env(loader, node):
    return os.environ[loader.construct_scalar(node)]


def construct_text(loader, node):
    path = loader.construct_scalar(node)
    with open(path, 'r') as fr:
        return fr.read().strip()


ExtendedSafeLoader.add_constructor('!env', construct_env)
ExtendedSafeLoader.add_constructor('!text', construct_text)


class Config:
    def __init__(self, stream):
        self._cfg = yaml.load(stream, Loader=ExtendedSafeLoader)

    def __call__(self, path):
        path = path.split(sep='.')
        obj = self._cfg
        for i, item in enumerate(path):
            try:
                if isinstance(obj, list):
                    item = int(item)
                obj = obj[item]
            except (KeyError, IndexError, ValueError):
                current_path = '.'.join(path[:i + 1])
                raise ConfigError(f'Path `{current_path}` does not exist')
        return obj
