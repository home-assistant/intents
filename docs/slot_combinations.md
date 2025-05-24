# Slot Combinations

Each intent in Home Assistant has **slots** that change the behavior of the intent. For example, `HassTurnOn` has a `{name}` slot that determines which entity to target. When both the `{name}` and `{area}` slot are present as a **combination**, the targeted entity must be in the given area.

We plan to transition this repository to a new format where sentences are grouped by **slot combinations** instead of just by intent. Slot combinations for each intent are declared in the `intents.yaml` file at the root, and sentences for them are stored in `sentences/<language>/<intent>/<slot_combination>.yaml` files.

Slot combinations may have an **importance level** of:

-  "required" (bare minimum)
-  "usable" (expected by users)
-  "complete" (needed for 100% coverage)
-  "optional" (extra, not needed for 100% coverage)

When the built-in `{name}` slot is used ("turn on My Light") or the domain of targeted entities is inferred by the words in the sentence ("turn on the lights in here"), then importance is moved to the corresponding `name_domains` or `inferred_domains` parts of the slot combination. See below for some examples.

A slot combination with `{name}` looks like this in `intents.yaml`:

``` yaml
HassTurnOn:
  slot_combinations:
    name_only:
      example: "turn on the overhead light"
      slots:
        - "name"
      name_domains:
        required:
          - "light"
          - "cover"
        complete:
          - "valve"
```

This specifies a `name_only` slot combination that requires the built-in `{name}` slot. When `{name}` is present, `name_domains` must be provided to check the entity's domain. The `required` name domains must be covered in the sentence templates, while other importance levels only affect the language's score.

A slot combination with `inferred_domains` looks like:

``` yaml
HassTurnOn:
  slot_combinations:
    domain_only:
      example: "turn on the lights in here"
      slots:
        - "domain"
      context_area: true
      inferred_domains:
        required:
          - "light"
        optional:
          - "fan"
```

When the `{domain}` slot is used, `inferred_domains` determines which domains are required, etc. The `required` inferred domains must be covered in the sentence templates, while other importance levels only affect the language's score.

Slot combinations without `{name}` and `{domain}` have a single importance level:

``` yaml
HassNevermind:
  slot_combinations:
    default:
      example: "nevermind"
      importance: "required"
      slots: []
```


## Sentences

For each intent and slot combination found in `intents.yaml`, a corresponding file named `sentences/<language>/<intent>/<slot_combination>.yaml` may be found. When the slot combination has an `importance` of "required" (or any `name_domains` or `inferred_domains` are required), this file must be present for validation to succeed. If the `importance` is "usable", a warning will be issued when the file is missing.

All sentence templates in a slot combination YAML file must match the exact slots specified in `intents.yaml`. Additional validation of sentence templates has been added to ensure that:

**list references cannot be present in alternatives and optionals**

In other words, `(text|{list_name})` and `[{list_name}]` are no longer allowed in sentence templates. This ensures that a sentence template always matches the same slots.

Importantly, all of the information needed to correctly generate the `requires_context` portion of the sentence templates is present in `intents.yaml`. Template authors are no longer responsible this part, making it much easier to ensure consistency across languages.

When the `{name}` or `{domain}` slots are present in a slot combination, the corresponding sentence templates must contain `name_domains` or `inferred_domain` respectively. All of the required domains must be covered, but not necessarily by the same group of sentences. This allows language leaders to split sentences in a way that makes sense for their language.

For example, the `name_only` slot combination for `HassTurnOn` is used to turn on lights as well as open covers. In English, this would be split into two groups of sentences:

``` yaml
# sentences/en/HassTurnOn/name_only.yaml
language: "en"
data:
  # lights
  - sentences:
      - "turn on [the] {name}"
    name_domains:
      - "light"
    response: "default"

  # covers
  - sentences:
      - "open [the] {name}"
    name_domains:
      - "cover"
    response: "cover"
```

Similarly, all required `inferred_domains` must be covered. Note that `inferred_domain` (no "s") is used in the sentences because only one domain can be inferred:

``` yaml
# sentences/en/HassTurnOn/domain_only.yaml
language: "en"
data:
  # lights
  - sentences:
      - "turn on the lights [in here]"
    inferred_domain: "light"
    response: "lights_area"

  # fans
  - sentences:
      - "turn on the fans [in here]"
    inferred_domain: "fan"
    response: "fans_area"
```

## Lists

A slot list (referenced `{list_name}` or `{list_name:slot_name}`) can be one of three types:

1. Fixed values
2. A range of numbers
3. A wildcard

Lists were previously stored in `sentences/<language>/_common.yaml` but will be moved to `lists/<language>/{list_group_name}.yaml` for easier validation and history tracking. Multiple lists can be grouped into a single file as it makes sense for the language. For example, a lists file named `lights.yaml` may contain color names and brightness levels.

Additionally, lists could not previously be shared across languages. For range lists and wildcards, shared lists can now be created at `lists/{list_group_name}.yaml` and referenced by any language. Value lists cannot be shared since they must be translated per language.


## Expansion Rules

An expansion rule (referenced `<rule_name>`) contains a snippet of a sentence template that is repeated often. For example, a `<the>` rule may contain `(the|my|our)` so that `<the> {name}` will expand to `the {name}`, `my {name}`, and `our {name}` in a sentence template.

Rules were previously stored in `sentences/<language>/_common.yaml` but will be moved to `rules/<language>/<rule_group_name>.yaml` for easier validation and history tracking. Multiple rules can be grouped into a single file as it makes sense for the language. For example, a rules file named `verbs.yaml` may contain groups of verbs for setting timers, turning on/off things, etc.

Rules are powerful, but can quickly cause sentence templates to be unreadable or explode with complexity. For these reasons, we are **recommending** the following restrictions:

### Rules should not contain lists

A rule should not contain `{list_name}`

While convenient, allowing list references inside rules makes it impossible to know which slots a sentence template will match by just looking at it.

Many languages (inspired by the English sentences) have a `<name>` rule which contains the `{name}` list. This causes confusion for new contributors, and can result in duplicated optional words such as when `[the] <name>` expands to something like `[the] [the] {name}`.

### Rules should not contain references to other rules

A rule should not contain `<rule_name>`

Nested rules require readers to follow a chain just to understand what text can be recognized. With alternatives in the rule (e.g., `(a|b|c)`) the possible sentences can also grow very large very quickly with nesting.

## Tests

Tests will also be transitioned to be per slot combination in `tests/<language>/<intent>/<slot_combination>.yaml`. Each test file is self-contained, including all of its test entities, areas, floors, and timers. The test format is now:

```yaml
language: "<language>"

# Test fixtures
entities:
  - name: "Name of Entity"
    domain: "entity_domain"
    state: "entity_state"  # optional
    state_with_unit: "entity_state + unit_of_measurement"  # optional
    
areas:
  - name: "Name of Area"

floors:
  - name: "Name of Floor"

tests:
  # test group
  - sentences:
      - "test sentence 1"
      - "test sentence 2"
    slots:
      expected_slot_name: expected_slot_value
    response: "Response text"  # required
    timers:  # optional
      - is_active: true
        start_hours: 1
        start_minutes: 30
        start_seconds: 0
        total_seconds_left: 100
        rounded_hours_left: 0
        rounded_minutes_left: 1
        rounded_seconds_left: 40
        name: "pizza"
        area: "Kitchen"
```
