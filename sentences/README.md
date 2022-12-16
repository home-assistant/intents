# Sentences

YAML files for each domain and language with sentences and the intents that they will evoke.


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


## Sentence Templates

* Alternative words or phrases
  * `(red | green | blue)`
* Optional words or phrases
  * `[the]`
  * `[this | that]`
* Slot Lists
  * `{list_name:slot_name}`
  * In YAML, `list_name` should be under `lists`
* Expansion Rules
  * `<rule_name>`
  * In YAML, `rule_name` should be under expansion rules
