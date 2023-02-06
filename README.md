# Intents for Home Assistant

This repository contains training data for Home Assistant's local voice control.

- [Progress per language and intent](https://home-assistant.github.io/intents/)
- [How to contribute](https://developers.home-assistant.io/docs/voice/intent-recognition/contributing/)
- [Language leaders](https://developers.home-assistant.io/docs/voice/language-leaders/)
- [Supported intents](https://developers.home-assistant.io/docs/intent_builtin)
- [Supported languages](https://developers.home-assistant.io/docs/voice/intent-recognition/supported-languages)

Repository layout:

- [`languages.yaml`](languages.yaml)
  - Supported languages and their language leader
- [`intents.yaml`](intents.yaml)
  - Supported intents
- `sentences/<language>`
  - Intent matching sentences in YAML files for `<language>` with the name `<domain>_<intent>.yaml`
  - [File format](https://developers.home-assistant.io/docs/voice/intent-recognition/template-sentence-syntax/)
- `responses/<language>`
  - YAML files for `<language>` with responses for intents
  - [File format](https://developers.home-assistant.io/docs/voice/intent-recognition/test-syntax/)
- `tests/<language>`
  - YAML files for `<language>` with test sentences and corresponding intents
  - [File format](tests/README.md#file-format)

See the [documentation](docs/README.md) for more information.

# Development

Checkout the repository and get a development environment with `script/setup`. This will create a new virtual environment in the `venv` directory of the repository, and install all necessary requirements.

Before developing, always activate your virtual environment with `source venv/bin/activate`.

## Run tests

Validate that the data is correctly formatted:

```sh
python3 -m script.intentfest validate --language nl
```

Run the tests. This will parse the sentences and verifies them with the test sentences.

```sh
pytest tests --language nl -k fan_HassTurnOn
```

Leave off `--language` to test all languages. Leave off `-k` to test all files.

## Test parsing sentences

You can try parsing sentences for a specific language with:

```sh
python3 -m script.intentfest parse --language en --sentence 'turn on the lights in the kitchen'
```

This will print a line of JSON for each `--sentence`:

```json
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

```sh
python3 -m script.intentfest sample --language en -n 1
```

This will print a line of JSON for each possible sentence:

```sh
python3 -m script.intentfest sample --language en -n 1
{"intent": "HassTurnOff", "text": "turn off all the fan in the kitchen"}
{"intent": "HassTurnOn", "text": "turn on the light in the kitchen"}
{"intent": "HassCloseCover", "text": "close the bedroom lamp"}
{"intent": "HassClimateSetTemperature", "text": "set the temp to 0 degrees celsius"}
{"intent": "HassLightSet", "text": "set the bedroom lamp brightness to 0 percent"}
{"intent": "HassOpenCover", "text": "open the bedroom lamp"}
{"intent": "HassClimateGetTemperature", "text": "what's the temp "}
```

You can filter for specific intents by adding `--intents HassTurnOn HassTurnOff`.

Leave off `-n` to generate all possible sentences.

## Test sampling template

To quickly test a sentence template, use:

```sh
python3 -m script.intentfest sample_template <template>
```

For example:

```sh
python3 -m script.intentfest sample_template 'open [the] door'
open the door
open door
```

You can add lists, ranges, and expansion rules as well:

```sh
python3 -m script.intentfest sample_template 'set color to <color> and brightness to {brightness}' --values color red green --range brightness 1 2 --rule color '[the] {color}'
```

## Check what the conversation would look like

To quickly simulate a conversation, use:

```sh
python3 -m script.intentfest conversation --language en # Set your preferred language
```

For example:

```
python3 -m script.intentfest conversation --language en
Type your query here, or type 'a' (or 'arrow up' on the keyboard) to repeat it. Type 'q' (or CTRL+C) to end the conversation.

<<< Turn on the lights in the living room
>>> Turned on lights in living room
Debug: {
  "text": "Turn on the lights in the living room",
  "match": true,
  "intent": "HassTurnOn",
  "slots": {
    "area": "living_room",
    "domain": "light"
  },
  "response_key": "lights_area",
  "response": "Turned on lights in living room"
}
------------------------------
<<<
New intents reloaded!
a
<<< Turn on the lights in the living room
>>> Turned on lights in living room sir
Debug: {
  "text": "Turn on the lights in the living room",
  "match": true,
  "intent": "HassTurnOn",
  "slots": {
    "area": "living_room",
    "domain": "light"
  },
  "response_key": "lights_area",
  "response": "Turned on lights in living room sir"
}
------------------------------
<<< q
>>> Bye!
```

The style of the response changed after the first query - I made a change to the response file, the script noticed this, reloaded the intents and printed "_`New intents reloaded!`_", after which I typed "**`a`**" (or `arrow up` - something like in the terminal using command history) to repeat the last query and check the response again.

There is also an option to see just the response, type **`d`** to toggle debug mode, or call the `conversation` module with `--no-response-debug`.

## Add new language

```sh
python3 -m script.intentfest add_language <language code> <language name>
```

`<language code>` should be something like `en` or `pl` according to [ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

Language name should be the name of the language in its own language.
