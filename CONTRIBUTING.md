# Contributing

Anyone can contribute to this repository, including:

* [Sentence templates](#sentence-templates) that will be matched to intents
* [Test sentences](#test-sentences) for testing the sentence templates
* [Response templates](#response-templates) that Home Assistant will use to generate responses


## Existing Languages

If your [language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) already exists in the [list of sentences](https://github.com/home-assistant/intents/tree/main/sentences), you can contribute by:

1. Forking [the repository](https://github.com/home-assistant/intents) on Github
2. Setting up a local development environment with `script/setup`
3. Creating a new branch off of `main`
4. Modifying the files for your language in:
    * `sentences/<language>` ([sentence templates](#sentence-templates))
    * `tests/<language>` ([test sentences](#test-sentences))
    * `responses/<language>` ([response templates](#response-templates))
5. Running `script/lint` and `script/test`
6. Submitting a pull request (PR) with your suggested changes


## New Languages

If you do not see your language in the repository, please [open an issue](https://github.com/home-assistant/intents/issues) or:

1. Fork [the repository](https://github.com/home-assistant/intents) on Github
2. Set up a local development environment with `script/setup`
3. Create a new branch off of `main`
4. Run `python3 -m script.intentfest add-language <language>` with a new [language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
5. Submit a pull request (PR) with your suggested changes


# Sentence Templates

In order to match text to [intents](https://developers.home-assistant.io/docs/intent_index), we have created a specialized [template language and matcher](https://github.com/home-assistant/hassil). These sentences are grouped by intent, and collected into [YAML files](sentences/README.md#file-format). By convention, lists and expansion rules put into `sentences/<language>/_common.yaml`


# Test Sentences

Sentences and the intents they should match are collected together into [YAML files](tests/README.md#file-format). By convention, test names for areas and entities are put into `tests/<language>/_fixtures.yaml`


# Response Templates

Responses to intents will be generated with [Home Assistant templates](https://www.home-assistant.io/docs/configuration/templating/). These are different than the [sentence templates](#sentence-templates), which are used for matching text to intents.

Response templates will have access to the [state object](https://www.home-assistant.io/docs/configuration/state_object) of the matched entity, such as the `climate` entity for the sentence "what is the temperature?".

See [file format](responses/README.md#file-format) for more details on the YAML format for response templates.
