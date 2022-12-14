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
    * [File format](sentences/README.md#file-format)


## Intents

See [intents.yaml](intents.yaml)


## Lists

Home Assistant will automatically generate the following lists during recognition:

* `{name}`
    * List of entity friendly names
* `{area}`
    * List of area names
