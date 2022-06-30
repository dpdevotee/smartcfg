from pathlib import Path
import pytest
from smartcfg import Config, ConfigError


def test_load_dict():
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
    """)
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
    """)
    assert cfg('c.3.another_key.key1') == 'hello'


def test_load_text():
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
        """)
    assert cfg('c.3.another_key.key1') == (
        'We all came out to Mountreux\non the lake Geneva shoreline.'
    )

    rel_path = abs_path.relative_to(Path.cwd())
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
        """)
    assert cfg('c.3.another_key.key1') == (
        'We all came out to Mountreux\non the lake Geneva shoreline.'
    )
