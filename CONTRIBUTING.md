# Contributing

This repository contains three different types of files:

* Directory `sentences` contains [sentence templates](sentences/README.md). These are sentences that match user input to intents.
* Directory `tests` contain [test sentences](tests/README.md). These are example user input and the intent that we should match it to.
* Directory `responses` contain [response templates](responses/README.md). These are used by Home Assistant to generate responses

We prefer a lot of small contributions over a few large ones. Contributions that contain a lot of changes are hard to review. That's why we want each contribution limited to a single language and single domain.

The filenames of sentences and tests are named like `<domain>_<intent>.yaml`. So if you are translating covers, only add sentences and tests to `cover_HassCoverOpen.yaml` and `cover_HassCoverClose.yaml`.

## Adding a new language

New languages should be based on the output of `python3 -m script.intentfest add_language <language>`, which generates an empty language directory with all the files needed for a new language.

Limit the first contribution to translations of the error sentences in `_common.yaml` and adding sentences and tests for the `homeassistant` domain.

If you are unable to run the `add_language` script locally, ask in Discord to have a maintainer run it for you.

## Ways to contribute

There are several workflows available to contribute:

* For small edits to existing files, you can [edit directly on Github](docs/github/README.md)
* A complete online development environment is available with [Github codespaces](docs/codespace/README.md)
* Local development should be done by [forking and setting up a local development environment](docs/forking/README.md)
