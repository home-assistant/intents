# Intents for Home Assistant

This repository contains training data for Home Assistant's local voice control.

Repository layout:

* `parser`
    * Sentence template parser and intent recognizer
* `sentences/<language>` 
    * YAML files for `<language>` with the name `<domain>_<intent>.yaml`
    * [File format](sentences/README.md#file-format)
* `tests/<language>`
    * YAML files for `<language>` with test sentences and corresponding intents
    * [File format](tests/README.md#file-format)
    

## Supported Languages

* `en` - English


## Installation

Run `script/setup` to create a virtual environment (`venv`) and install requirements.


## Testing

Run `script/test` to run tests for all languages.

Tests for individual languages can be run with: 

``` sh
pytest tests --language en
```

You can try parsing sentences for a specific language with:

``` sh
python3 -m script.intentfest --language en --sentence 'turn on the lights in the kitchen'
```

This will print a line of JSON for each `--sentence`:

```
{"text": "turn on the lights in the kitchen", "match": true, "intent": "HassTurnOn", "slots": {"area": "kitchen", "domain": "light", "name": "all"}}
```


## Intents

See [intents.yaml](intents.yaml) for available intent schemas.


## Lists

Home Assistant will automatically generate the following lists during recognition:

* `{name}`
    * List of device or entity names
* `{area}`
    * List of area names
    
