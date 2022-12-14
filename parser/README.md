# HassIL

The Home Assistant Intent Language (HassIL) parser.


## Dependencies

* antlr4-python3-runtime
* PyYAML
* dataclasses-json


## Installation

Create a virtual environment:

``` sh
python3 -m venv .venv
.venv/bin/pip3 install --upgrade pip
.venv/bin/pip3 install --upgrade wheel setuptools
```

Install dependencies:

``` sh
.venv/bin/pip3 install -r requirements.txt
```


# Running

``` sh
python3 -m hassil --language en
```

Once loaded, you may type in a sentence and see what intent it matches.
For example:

``` sh
what is the temperature in the living room
{'intent': 'HassClimateGetTemperature', 'area': 'living room', 'domain': 'climate'}
```

By default, the areas "kitchen", "bedroom", and "living room" are available. You can override this with `--areas`. Device or entity names can be provided with `--names`.

``` sh
python3 -m hassil --language en --areas office --names trapdoor
open the trapdoor in the office
{'intent': 'HassOpenCover', 'name': 'trapdoor', 'area': 'office'}
```


## Sentence Templates

* Alternative words or phrases
  * `(red | green | blue)`
* Optional words or phrases
  * `[the]`
  * `[this | that]`
* Slot Lists
  * `{list_name}`
  * `{list_name:slot_name}`
  * Refers to a pre-defined list of values in YAML
* Expansion Rules
  * `<rule_name>`
  * Refers to a pre-defined expansion rule in YAML
