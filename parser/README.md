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
python3 -m hassil <yaml_file_or_directory> [<yaml_file_or_directory> ...]
```

Once loaded, you may type in a sentence and see what intent it matches.
For example:

``` sh
what is the temperature in the living room
{'intent': 'HassClimateGetTemperature', 'area': 'living room', 'domain': 'climate'}
```

By default, the areas "kitchen", "bedroom", and "living room" are available. You can override this with `--areas`. Device or entity names can be provided with `--names`.

``` sh
python3 -m hassil sentences/en --areas office --names trapdoor
open the trapdoor in the office
{'intent': 'HassOpenCover', 'name': 'trapdoor', 'area': 'office'}
```


### Sampling Sentences

Sentences for each intent can be sampled from the intent YAML files:

``` sh
python3 -m hassil.sample sentences/en -n 1
{"intent": "HassTurnOff", "text": "turn off all the fan in the area"}
{"intent": "HassTurnOn", "text": "turn on the light in the area"}
{"intent": "HassCloseCover", "text": "close the entity"}
{"intent": "HassClimateSetTemperature", "text": "set the temp to 0 degrees celsius"}
{"intent": "HassLightSet", "text": "set the entity brightness to 0 percent"}
{"intent": "HassOpenCover", "text": "open the entity"}
{"intent": "HassClimateGetTemperature", "text": "what's the temp"}
```

The `--areas` and `--names` arguments are the same from `python3 -m hassil`, but default to generic "area" and "entity" terms.

Exclude the `-n` argument to sample all possible sentences.


## Sentence Templates

Parsed using a custom [ANTLR](https://www.antlr.org) grammar (see [`HassILGrammar.g4`](HassILGrammar.g4)).

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
