# Intents for Home Assistant

This repository contains training data for Home Assistant's local voice control.

Repository layout:

* `parser`
    * Sentence template parser and intent recognizer
* `sentences/<language>`
    * YAML files for `<language>` with the name `<domain>_<intent>.yaml`
    * [File format](sentences/README.md#file-format)
* `responses/<language>`
    * YAML files for `<language>` with responses for intents
    * [File format](responses/README.md#file-format)
* `tests/<language>`
    * YAML files for `<language>` with test sentences and corresponding intents
    * [File format](tests/README.md#file-format)


## Supported Languages

* `en` - English
* `nl` - Dutch


## Intents

See [intents.yaml](intents.yaml) for available intent schemas.


## Lists

Home Assistant will automatically generate the following lists during recognition:

* `{name}`
    * List of device or entity names
* `{area}`
    * List of area names


# Development

Checkout the repository and get a development enviornment with `script/setup`.

Before developing, always activate your virtual environment with `source venv/bin/activate`.

## Run tests

```
pytest tests --language nl
```

Leave `--language` off to run all tests.

## Testing sentences

You can try parsing sentences for a specific language with:

``` sh
python3 -m script.intentfest parse --language en --sentence 'turn on the lights in the kitchen'
```

This will print a line of JSON for each `--sentence`:

```
{
  "text": "turn on the lights in the kitchen",
  "match": true,
  "intent": "HassTurnOn",
  "slots": {
    "area": "kitchen",
    "domain": "light"
  }
}
```

## Add new language

```
python3 -m script.intentfest add_language <language>
```

Before you start on a new language, confirm that no one else is already working on one.
