# Contributing

Anyone can contribute to this repository, including:

* [Sentence templates](#sentence-templates) that will be matched to intents
* [Test sentences](#test-sentences) for testing the sentence templates
* [Response templates](#response-templates) that Home Assistant will use to generate responses


## Workflows

Several workflows are available for contribution:

* For small edits to existing files, you can [edit directly on Github](docs/github/README.md)
* A complete online development environment is available with [Github codespaces](docs/codespaces/README.md)
* Local development should be done by [forking and setting up a local development environment](docs/forking/README.md)


# Sentence Templates

In order to match text to [intents](https://developers.home-assistant.io/docs/intent_index), we have created a specialized [template language and matcher](https://github.com/home-assistant/hassil). These sentences are grouped by intent, and collected into [YAML files](sentences/README.md#file-format). By convention, lists and expansion rules put into `sentences/<language>/_common.yaml`


# Test Sentences

Sentences and the intents they should match are collected together into [YAML files](tests/README.md#file-format). By convention, test names for areas and entities are put into `tests/<language>/_fixtures.yaml`


# Response Templates

Responses to intents will be generated with [Home Assistant templates](https://www.home-assistant.io/docs/configuration/templating/). These are different than the [sentence templates](#sentence-templates), which are used for matching text to intents.

Response templates will have access to the [state object](https://www.home-assistant.io/docs/configuration/state_object) of the matched entity, such as the `climate` entity for the sentence "what is the temperature?".

See [file format](responses/README.md#file-format) for more details on the YAML format for response templates.
