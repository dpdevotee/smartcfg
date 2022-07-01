import os
from pathlib import Path

import yaml


MODE_KEY = '_mode'
MODES_KEY = '_modes'


class ConfigError(Exception):
    pass


def construct_env(loader, node):
    return os.environ[loader.construct_scalar(node)]


def construct_dummy(loader, node):
    return None


class Config:
    def __init__(self, stream, base_dir):
        def construct_text(loader, node):
            path = loader.construct_scalar(node)
            with open(Path(base_dir).parent / path, 'r') as fr:
                return fr.read().strip()

        class ExtendedSafeLoader(yaml.SafeLoader):
            pass

        ExtendedSafeLoader.add_constructor('!env', construct_env)
        ExtendedSafeLoader.add_constructor('!text', construct_text)
        ExtendedSafeLoader.add_constructor('!IN_MODE', construct_dummy)
        cfg = yaml.load(stream, Loader=ExtendedSafeLoader)

        construct_in_mode = self._get_in_mode_constructor(cfg)
        ExtendedSafeLoader.yaml_constructors['!IN_MODE'] = construct_in_mode
        self._cfg = yaml.load(stream, Loader=ExtendedSafeLoader)

    @staticmethod
    def _get_in_mode_constructor(config):
        not_given = object()
        mode = config.get(MODE_KEY, not_given)
        modes = config.get(MODES_KEY, not_given)
        if mode is not_given and modes is not_given:
            def construct_dont_use_in_mode(loader, node):
                raise ConfigError(f'!IN_MODE tag is used but `{MODE_KEY}` '
                                  f'and `{MODES_KEY}` keys are not provided')

            return construct_dont_use_in_mode

        if modes is not_given and mode is not not_given:
            raise ConfigError(
                f'`{MODE_KEY}` key is provided but `{MODES_KEY}` is not')
        if mode is not_given and modes is not not_given:
            raise ConfigError(
                f'`{MODES_KEY}` key is provided but `{MODE_KEY}` is not')
        if not isinstance(modes, list):
            raise ConfigError(f'`{MODES_KEY}` key must be a list')
        if mode not in modes:
            raise ConfigError(
                f'`{MODE_KEY}` value "{mode}" is not in `{MODES_KEY}`')

        def construct_in_mode(loader, node):
            mapping = loader.construct_mapping(node, deep=True)
            for k in mapping:
                if k not in modes:
                    raise ConfigError(f'Value "{k}" is not in `{MODES_KEY}`')
            return mapping[mode]

        return construct_in_mode

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
