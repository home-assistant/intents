# Tests

Test sentences and their corresponding intents.


## File Format

``` yaml
language: "<language code>"
tests:
  - sentences:
      - "<sentence>"
      - "<sentence>"
    intent:
      name: "<intent name>"
      slots:
        <slot_name>:
          value: <slot value>
```
