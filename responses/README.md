# Responses

YAML files for each intent with the [response template](https://www.home-assistant.io/docs/configuration/templating/) that Home Assistant will give when the intent is executed.

The sentences are rendered as a Home Assistant template with access to variables such as `state` and `slots`. The [state object](https://www.home-assistant.io/docs/configuration/state_object) contains the state of the matched object. A `slots` object contains the text of each matched intent slot.

## File Format

```yaml
language: "<language code>"
responses:
  intents:
    <intent name>:
      # List of responses. If "response" is not set in the intent, then "default" will be used.
      default:
        - "{{ slots.name }} is {{ state.state_with_unit }}"
```

**NOTE:** These are not the same format as the sentence templates in this repository.
