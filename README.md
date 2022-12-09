# Smartcfg

This is library that allows python programs load configuration parameters
from YAML files. YAML file can contain different values for different
runtime environments. Parameter values can be specified directly in the YAML
file, in other YAML/JSON/TEXT files or in environment variables.

## Installation

```bash
git clone https://github.com/dpdevotee/smartcfg.git
cd smartcfg
python setup.py install
```

## Usage

YAML file with configuration MUST have at leas two keys: `_mode` and `_modes`:
* key `_modes` specifies list of names of supported runtime environments;
* key `_mode` specifies name of current runtime environment.

Other keys in file can contain parameters, required for your python program.
Let's have a look at a file named `config.yaml` with one runtime 
environment - `production`:

```YAML
_modes:
  - production
_mode: production

databases:
  default:
      host: db.example.com
      port: 5432
      dbname: app_db
      user: my_cool_user
      password: qwerty123

app_version: 2.3.1
addresses:
  - 11 Wall St, New York, NY 10005
  - 13 Bolshoy Kislovskii pereulok, Moscow
```

This file can be used that way:

```python
from smartcfg import SmartConfig

cfg = SmartConfig('config.yaml')
version = cfg('app_version')  # 2.3.1
host = cfg('database.default.host')  # 'db.example.com'
user = cfg('database.default.user')  # 'my_cool_user'
address = cfg('addresses.1')  # '13 Bolshoy Kislovskii pereulok, Moscow'
```

Values also can be loaded from environment variables:
```YAML
_modes:
  - production
_mode: production

databases:
  default:
      password: !env MY_PASSWORD_VAR
```
Here `MY_PASSWORD_VAR` is a name of a variable that contains password.
Value can be access the same way as in previous example:
```python
from smartcfg import SmartConfig

cfg = SmartConfig('config.yaml')
user = cfg('database.default.password')
```

### Loading values from other files
Suppose we have three files:
`file1.yaml`:
```YAML
one: value0
two:
  - value1
  - 10
  - another_key:
      yet_another_key: [5, 6, 7]
```
`file2.json`:
```JSON
{
  "one": "value2",
  "two": [
    "value3",
    10,
    {
      "another_key": {
        "yet_another_key": [5, 6, 7]
      }
    }
  ]
}
```
and `file3.txt`:
```text

   We all came out to Mountreux
on the lake Geneva shoreline.

```
Data from these files can also be accessed from configulations YAML file:

```YAML
_modes:
  - production
_mode: production

total_from_file1: !yaml file1.yaml
val_from_file1: !yaml [file1.yaml, two.2.another_key.yet_another_key.1]

total_from_file2: !json file2.json
val_from_file2: !json [file2.json, two.2.another_key.yet_another_key.1]

val_from_file3: !text file3.txt
```

```python
from smartcfg import SmartConfig

cfg = SmartConfig('config.yaml')
file1_data = cfg('total_from_file1')  # dictionary with whole file content
file1_value = cfg('val_from_file1')  # 6

file2_data = cfg('total_from_file2')  # dictionary with whole file content
file2_value = cfg('val_from_file2')  # 6

file3_value = cfg('val_from_file3')  # 'We all came out to Mountreux\non the lake Geneva shoreline.'
```
Note that when value is loaded from TEXT file, leading and trailing
whitespaces are stripped.

### Runtime environment selection

You can specify several runtime environments, select one with `_mode`
parameter, and specify different values for different environments.
Example:

```YAML
_modes:
  - production
  - testing
  - ci
_mode: !env ENVIRONMENT_TYPE

databases:
  default:
      host: !IN_MODE
            production: prod-db.example.com
            testing: test-db.example.com
            ci: db
      port: 5432
      dbname: app_db
      user: my_cool_user
      password: !IN_MODE
                production: !env DB_PASSWORD
                testing: !env DB_PASSWORD
                ci: my_password
```

* If environment variable `ENVIRONMENT_TYPE` equals to `production`,
`cfg('databases.defaul.host')` yields `prod-db.example.com`;
* if it equals to `testing`, `cfg('databases.defaul.host')` yields `test-db.example.com`;
* if it equals to `ci` `cfg('databases.defaul.host')` yields `db`;
* otherwise, exception is raised.

Same with `databases.defaul.password`:
* If environment variable `ENVIRONMENT_TYPE` equals to `production`,
`cfg('databases.defaul.password')` is loaded from environment variable `DB_PASSWORD`;
* if it equals to `ci` `cfg('databases.defaul.password')` yields `my_password`;
* and so on.
