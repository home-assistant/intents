# Responses

YAML files for each intent with the response that Home Assistant will give when the intent is executed.

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
