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
    
See the [documentation](docs/README.md) for more information.


## Supported Languages

| Code | Language         | Leaders            |
|------|------------------|--------------------|
| `de` | German           | @Scorpoon          |
| `dk` | Danish           | (position open)    |
| `en` | English          | (position open)    |
| `fr` | French           | @benjaminlecouteux |
| `he` | Hebrew           | @leranp            |
| `hu` | Hungarian        | @nagyrobi          |
| `nb` | Norwegian Bokmål | (position open)    |
| `nl` | Dutch            | @TheFes            |
| `pl` | Polish           | (position open)    |
| `sk` | Slovak           | (position open)    |
| `sv` | Swedish          | (position open)    |


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

## Test sampling sentences

You can sample the possible sentences for a specific language with:

``` sh
python3 -m script.intentfest sample --language en -n 1
```

This will print a line of JSON for each possible sentence:

``` sh
python3 -m script.intentfest sample --language en -n 1
{"intent": "HassTurnOff", "text": "turn off all the fan in the kitchen"}
{"intent": "HassTurnOn", "text": "turn on the light in the kitchen"}
{"intent": "HassCloseCover", "text": "close the bedroom lamp"}
{"intent": "HassClimateSetTemperature", "text": "set the temp to 0 degrees celsius"}
{"intent": "HassLightSet", "text": "set the bedroom lamp brightness to 0 percent"}
{"intent": "HassOpenCover", "text": "open the bedroom lamp"}
{"intent": "HassClimateGetTemperature", "text": "what's the temp "}
```

You also can sample the possible sentences for a specific language and intent(s) with:

``` sh
python3 -m script.intentfest sample --language en -n 1 --intents HassTurnOn HassClimateGetTemperature
```

This will print a line of JSON for each possible sentence for the given intents:

``` sh
python3 -m script.intentfest sample --language en -n 1 --intents HassTurnOn HassClimateGetTemperature
{"intent": "HassClimateGetTemperature", "text": "what's the temp"}
{"intent": "HassTurnOn", "text": "turn on all the fan in the kitchen"}
```

Leave off `-n` to generate all possible sentences.

## Test sampling template

To quickly test a sentence template, use:

``` sh
python3 -m script.intentfest sample_template <template>
```

For example:

``` sh
python3 -m script.intentfest sample_template 'open [the] door'
open the door
open door
```

You can add lists, ranges, and expansion rules as well:

``` sh
python3 -m script.intentfest sample_template 'set color to <color> and brightness to {brightness}' --values color red green --range brightness 1 2 --rule color '[the] {color}'
```

## Add new language

```
python3 -m script.intentfest add_language <language>
```

`<language>` should be something like `en` or `pl` according to [ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

Before you start on a new language, confirm that no one else is already working on one.
