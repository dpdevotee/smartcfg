from pathlib import Path

import pytest

from smartcfg import Config, ConfigError


def test_load_dict():
    base_dir = str(Path(__file__).resolve())
    cfg = Config("""
    a: 1
    b: hello
    c:
      - one
      - two
      - 3
      - another_key:
          key1: "value1"
          key2: 'value2'
    """, base_dir)
    assert cfg('a') == 1
    assert cfg('b') == 'hello'
    assert cfg('c.0') == 'one'
    assert cfg('c.1') == 'two'
    assert cfg('c.2') == 3
    assert cfg('c.3') == {'another_key': {'key1': 'value1', 'key2': 'value2'}}
    assert cfg('c.3.another_key.key2') == 'value2'

    with pytest.raises(ConfigError) as err:
        _ = cfg('c.3.another_key.key3')
    assert str(err.value) == 'Path `c.3.another_key.key3` does not exist'
    with pytest.raises(ConfigError) as err:
        _ = cfg('c.3.yet_another_key.key3')
    assert str(err.value) == 'Path `c.3.yet_another_key` does not exist'
    with pytest.raises(ConfigError) as err:
        _ = cfg('c.not_integer.yet_another_key.key3')
    assert str(err.value) == 'Path `c.not_integer` does not exist'


def test_load_env(set_env):
    base_dir = str(Path(__file__).resolve())
    set_env('MY_VAR', 'hello')
    cfg = Config("""
    a: 1
    b: hello
    c:
      - one
      - two
      - 3
      - another_key:
          key1: !env MY_VAR
          key2: 'value2'
    """, base_dir)
    assert cfg('c.3.another_key.key1') == 'hello'


def test_load_text():
    base_dir = str(Path(__file__).resolve())
    abs_path = Path(__file__).parent / 'files_to_load/some.txt'
    cfg = Config(f"""
        a: 1
        b: hello
        c:
          - one
          - two
          - 3
          - another_key:
              key1: !text {abs_path}
              key2: 'value2'
        """, base_dir)
    assert cfg('c.3.another_key.key1') == (
        'We all came out to Mountreux\non the lake Geneva shoreline.'
    )

    rel_path = 'files_to_load/some.txt'
    cfg = Config(f"""
        a: 1
        b: hello
        c:
          - one
          - two
          - 3
          - another_key:
              key1: !text {rel_path}
              key2: 'value2'
        """, base_dir)
    assert cfg('c.3.another_key.key1') == (
        'We all came out to Mountreux\non the lake Geneva shoreline.'
    )


def test_in_mode_broken_config():
    base_dir = str(Path(__file__).resolve())
    with pytest.raises(ConfigError) as err:
        Config("_mode: testing", base_dir)
    assert str(err.value) == '`_mode` key is provided but `_modes` is not'
    with pytest.raises(ConfigError) as err:
        Config(
            """
                _modes:
                  - testing
                  - stable
            """, base_dir)
    assert str(err.value) == '`_modes` key is provided but `_mode` is not'
    with pytest.raises(ConfigError) as err:
        Config(
            """
                _mode: testing
                _modes: testing
            """, base_dir)
    assert str(err.value) == '`_modes` key must be a list'
    with pytest.raises(ConfigError) as err:
        Config(
            """
                _mode: production
                _modes:
                  - testing
                  - stable
            """, base_dir)
    assert str(err.value) == '`_mode` value "production" is not in `_modes`'
    with pytest.raises(ConfigError) as err:
        Config(
            """
                a: !IN_MODE
                   testing: val1
                   stable: val2
            """, base_dir)
    assert str(err.value) == ('!IN_MODE tag is used but `_mode` and '
                              '`_modes` keys are not provided')


def test_in_mode(set_env):
    stream = ("""
        _mode: !env MODE
        _modes:
          - testing
          - stable
        a: 1
        b: hello
        c:
          - one
          - two
          - another_key: !IN_MODE
                         testing: !text files_to_load/some.txt
                         stable: 'value2'
          - 3
    """)
    base_dir = str(Path(__file__).resolve())

    set_env('MODE', 'testing')
    cfg = Config(stream, base_dir)
    assert cfg('_mode') == 'testing'
    assert cfg('c.2.another_key') == (
        'We all came out to Mountreux\non the lake Geneva shoreline.'
    )

    set_env('MODE', 'stable')
    cfg = Config(stream, base_dir)
    assert cfg('_mode') == 'stable'
    assert cfg('c.2.another_key') == 'value2'


def test_in_mode_unknown_mode():
    base_dir = str(Path(__file__).resolve())
    with pytest.raises(ConfigError) as err:
        Config("""
            _mode: testing
            _modes:
              - testing
              - stable
            another_key: !IN_MODE
                         testing: !text files_to_load/some.txt
                         production: 'value2'
        """, base_dir)
    assert str(err.value) == 'Value "production" is not in `_modes`'
