# Sentences

YAML files for each domain and language with sentences and the intents that they will evoke.

Each file is named after `<domain>_<intent>.yaml` and should contain sentences that match only the intent from the filename.

Files are formatted based on our [template language and matcher](https://github.com/home-assistant/hassil).

By convention, lists, expansion rules and skip words are put into `sentences/<language>/_common.yaml`.

## File Format

``` yaml
language: "<language code>"
intents:
  <intent name>:
    data:
      # List of sentences/slots
      - sentences:
          - "<sentence template>"
          - "<sentence template>"
        slots:
          # Fixed slots for the recognized intent
          <name>: <value>

# Optional lists of items that become alternatives in sentence templates
lists:
  # Referenced as {list_name}
  <list name>:
    values:
      - "items"
      - "in"
      - "the list"
  <range_name>
    range:
      type: "number"
      from: 0
      to: 100

# Optional rules that are expanded in sentence templates
expansion_rules:
  # Referenced as <rule_name>
  <rule_name>: "<sentence template>"

# Optional words that the intent recognizer can skip during recognition
skip_words:
  - "<word>"
```


## Intents

Intent names correspond to [Home Assistant intents](https://developers.home-assistant.io/docs/intent_index). Any `{list}` in the [sentence templates](#sentence-templates) will be automatically added as a slot during recognition.

Under `data` there is a list of sentence groups, for example:

``` yaml
intents:
  HassTurnOn:
    data:
      - sentences:
          - "turn on the light"
```

In addition to sentences, the `slots` section can be used to set fixed slot values in the intent:

``` yaml
intents:
  HassTurnOn:
    data:
      - sentences:
          - "turn on the light"
        slots:
          domain: "light"
```


## Sentence Templates

* Alternative word, phrases, or parts of a word
  * `(red | green | blue)`
  * `turn(ed | ing)`
* Optional word, phrases, or parts of a word
  * `[the]`
  * `[this | that]`
  * `light[s]`
* Slot Lists
  * `{list_name}`
  * `{list_name:slot_name}` (if intent slot is named different)
  * Every value of the list is a different option
  * In YAML, `list_name` should be under `lists`
  * Use `values` for text lists, `range` for numeric lists
* Expansion Rules
  * `<rule_name>`
  * The body of the rule is substituted for `<rule_name>`
  * In YAML, `rule_name` should be under `expansion_rules`. If the `rule_name` wraps a slot name, it should match the slot name. Otherwise it should be in the native language.
