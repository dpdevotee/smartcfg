import json
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
            with open(Path(base_dir) / path, 'r') as fr:
                return fr.read().strip()

        def construct_yaml(loader, node):
            if isinstance(node, yaml.ScalarNode):
                file = loader.construct_scalar(node)
                with open(Path(base_dir) / file, 'r') as fr:
                    return yaml.safe_load(fr.read())
            file = loader.construct_sequence(node)
            if len(file) != 2:
                raise ConfigError('List notations of !yaml tag requires '
                                  f'2 arguments, {len(file)} were given.')
            file, path = file
            with open(Path(base_dir) / file, 'r') as fr:
                content = yaml.safe_load(fr.read())
            return self._get_value_by_path(content, path)

        def construct_json(loader, node):
            if isinstance(node, yaml.ScalarNode):
                file = loader.construct_scalar(node)
                with open(Path(base_dir) / file, 'r') as fr:
                    return json.load(fr)
            file = loader.construct_sequence(node)
            if len(file) != 2:
                raise ConfigError('List notations of !yaml tag requires '
                                  f'2 arguments, {len(file)} were given.')
            file, path = file
            with open(Path(base_dir) / file, 'r') as fr:
                content = json.load(fr)
            return self._get_value_by_path(content, path)

        class ExtendedSafeLoader(yaml.SafeLoader):
            pass

        ExtendedSafeLoader.add_constructor('!env', construct_env)
        ExtendedSafeLoader.add_constructor('!text', construct_text)
        ExtendedSafeLoader.add_constructor('!yaml', construct_yaml)
        ExtendedSafeLoader.add_constructor('!json', construct_json)
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
            for k in modes:
                if k not in mapping:
                    raise ConfigError(f'Value for mode "{k}" is '
                                      'not specified in tag !IN_MODE')
            return mapping[mode]

        return construct_in_mode

    @staticmethod
    def _get_value_by_path(obj, path):
        path = path.split(sep='.')
        for i, item in enumerate(path):
            try:
                if isinstance(obj, list):
                    item = int(item)
                obj = obj[item]
            except (KeyError, IndexError, ValueError):
                current_path = '.'.join(path[:i + 1])
                raise ConfigError(f'Path `{current_path}` does not exist')
        return obj

    def __call__(self, path):
        return self._get_value_by_path(self._cfg, path)


class SmartConfig:
    """Class that load configuration YAML files.

    Parameters
    ----------
    path : str
        Path to configuration YAML file.
    """
    def __init__(self, path):
        self._path = path
        self._stream = None
        self._cfg = None

    def _lazy_load(self):
        with open(self._path, 'r') as fr:
            self._stream = fr.read()
            self._cfg = Config(self._stream,
                               base_dir=Path(self._path).resolve().parent)

    def __call__(self, path):
        if self._stream is None:
            self._lazy_load()
        return self._cfg(path)
