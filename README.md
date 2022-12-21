# Intents for Home Assistant

This repository contains training data for Home Assistant's local voice control.

Repository layout:

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

* `nl` - Dutch (language leader position open)
* `en` - English (language leader position open)
* `fr` - French (language leader position open)
* `de` - German (language leader position open)
* `nb` - Norwegian Bokmål (language leader position open)
* `sv` - Swedish (language leader position open)


## Language leader

Each language is maintained by one or more language leaders. Language leaders are responsible for reviewing the contributions in their language and making sure that they are grammatically correct.

Anyone can apply to become one. If you want to apply to be a language leader, join us in `#devs_voice` on [Discord](https://www.home-assistant.io/join-chat/) or [open an issue](https://github.com/home-assistant/intents/issues).

## Contributing sentences

Anyone can [contribute to the repository](CONTRIBUTING.md). The sentences will be reviewed by the language leaders and merged if they are correct. You can either contribute new sentences or improve existing ones.

If you only want to contribute sentences that should be supported, but don't feel comfortable with YAML, you can add them to [the issue of your language](https://github.com/home-assistant/intents/issues?q=is:issue+is:open+label:%22suggest+sentence%22). Limit your submissions to commands that work with the [supported intents](intents.yaml).

## Intents

See [intents.yaml](intents.yaml) for the Home Assistant intent schemas that are supported.


## Lists

Home Assistant will automatically generate the following lists during recognition:

* `{name}`
    * List of device or entity names
* `{area}`
    * List of area names


# Development

Checkout the repository and get a development enviornment with `script/setup`. This will create a new virtual environment in the `venv` directory of the repository, and install all necessary requirements.

Before developing, always activate your virtual environment with `source venv/bin/activate`.

## Run tests

Validate the data is correctly formatted.

```
python3 -m script.intentfest validate
```

Run the tests. Leave `--language` off to run all tests.

```
pytest tests --language nl
```

## Test parsing sentences

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

`<language>` should be something like `en` or `pl` according to [ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

Before you start on a new language, confirm that no one else is already working on one.
