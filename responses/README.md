# Responses

YAML files for each intent with the [response template](https://www.home-assistant.io/docs/configuration/templating/) that Home Assistant will give when the intent is executed.

The success sentences are rendered as a Home Assistant template. Intents can make extra variables available that can be referenced in the success message. An example extra variable would be the [state object](https://www.home-assistant.io/docs/configuration/state_object) of the matched entity for the sentence "what is the temperature?".

## File Format

```yaml
language: "<language code>"
responses:
  intents:
    <intent name>:
      # List of responses. A random one will be executed. Responses are rendered
      # as a Home Assistant template. Intents can make extra variables
      # available that can be referenced in the success message.
      success:
        - "{{ state.state }} degrees"
```

**NOTE:** These are not the same format as the sentence templates in this repository.
