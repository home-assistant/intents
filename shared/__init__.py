from dataclasses import dataclass, field
from functools import partial
from typing import Any, Dict, Optional, List, Set, Tuple

from hassil import parse_sentence
from hassil.intents import SlotList, TextSlotList, is_template
from hassil.recognize import RecognizeResult
from hassil.sample import sample_expression
from jinja2 import BaseLoader, Environment, StrictUndefined


@dataclass
class State:
    """Minimal HA-like state object for responses."""

    entity_id: str
    name: str
    hass_state: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    area_id: Optional[str] = None
    human_state: Optional[str] = None
    aliases: Set[str] = field(default_factory=set)
    _domain: Optional[str] = None

    @property
    def state(self) -> str:
        if self.human_state is not None:
            return self.human_state

        return self.hass_state

    @property
    def domain(self) -> str:
        if self._domain is None:
            self._domain = self.entity_id.split(".", maxsplit=1)[0]

        return self._domain

    @property
    def state_with_unit(self) -> str:
        unit = self.attributes.get("unit_of_measurement")
        if unit:
            return f"{self.state} {unit}"

        return self.state


@dataclass
class AreaEntry:
    """Minimal HA-like area object for responses."""

    id: str
    name: str
    aliases: Set[str] = field(default_factory=set)


def get_matched_states(
    states: List[State], areas: List[AreaEntry], result: RecognizeResult
) -> Tuple[List[State], List[State]]:
    """Split states into matched/unmatched."""
    if result.intent.name in ("HassClimateGetTemperature", "HassClimateSetTemperature"):
        # Match climate entities only
        states = [state for state in states if state.domain == "climate"]
    elif result.intent.name in ("HassGetWeather",):
        # Match weather entities only
        states = [state for state in states if state.domain == "weather"]

    # Implement some matching logic from Home Assistant
    entity_name: Optional[str] = None
    name_entity = result.entities.get("name")
    if name_entity is not None:
        entity_name = _normalize_name(name_entity.value)

    area_name: Optional[str] = None
    area_entity = result.entities.get("area")
    if area_entity is not None:
        area_name = _normalize_name(area_entity.value)

    domain_name: Optional[str] = None
    domain_entity = result.entities.get("domain")
    if domain_entity is not None:
        domain_name = _normalize_name(domain_entity.value)

    device_class: Optional[str] = None
    device_class_entity = result.entities.get("device_class")
    if device_class_entity is not None:
        device_class = device_class_entity.value

    state_name: Optional[str] = None
    state_entity = result.entities.get("state")
    if state_entity is not None:
        state_name = state_entity.value

    # name -> id
    area_ids: Dict[str, str] = {}
    for area in areas:
        area_ids[_normalize_name(area.name)] = area.id
        for area_alias in area.aliases:
            area_ids[_normalize_name(area_alias)] = area.id

    matched: List[State] = []
    unmatched: List[State] = []

    for state in states:
        if entity_name is not None:
            name_match = _normalize_name(state.name) == entity_name

            if not name_match:
                # Check aliases
                for state_alias in state.aliases:
                    if _normalize_name(state_alias) == entity_name:
                        name_match = True
                        break

            if not name_match:
                # Filter by entity name
                continue

        if (area_name is not None) and (state.area_id != area_ids.get(area_name)):
            # Filter by area
            continue

        if (domain_name is not None) and (domain_name != state.domain):
            # Filter by domain
            continue

        if (device_class is not None) and (
            device_class != state.attributes.get("device_class")
        ):
            # Filter by entity name
            continue

        if state_name is not None:
            # Match state
            if state.hass_state == state_name:
                matched.append(state)
            else:
                unmatched.append(state)
        else:
            # Everything "matches" with no state constraint
            matched.append(state)

    return matched, unmatched


def _normalize_name(name: str) -> str:
    return name.strip().casefold()


def get_jinja2_environment() -> Environment:
    """Create default Jinja2 environment."""
    return Environment(loader=BaseLoader(), undefined=StrictUndefined)


def render_response(
    response_template: str,
    result: RecognizeResult,
    matched: List[State],
    unmatched: Optional[List[State]] = None,
    env: Optional[Environment] = None,
) -> str:
    """Renders a response template using Jinja2."""
    assert response_template, "Empty response template"
    if unmatched is None:
        unmatched = []

    # First matched or unmatched state
    state1: Optional[State] = None
    if matched:
        state1 = matched[0]
    elif unmatched:
        state1 = unmatched[0]

    if env is None:
        env = get_jinja2_environment()

    return env.from_string(response_template).render(
        {
            "slots": {
                entity.name: entity.text_clean or entity.value
                for entity in result.entities_list
            },
            "state": state1,
            "query": {
                "matched": matched,
                "unmatched": unmatched,
                "total_results": len(matched) + len(unmatched),
            },
            "state_attr": partial(state_attr, matched),
        }
    )


def state_attr(states: List[State], entity_id: str, attr_name: str) -> Any | None:
    """Mimic state_attr from Home Assistant."""
    for state in states:
        if state.entity_id == entity_id:
            return state.attributes.get(attr_name)

    return None


def get_slot_lists(fixtures: dict[str, Any]) -> dict[str, SlotList]:
    # Load test areas and entities for language
    slot_lists: dict[str, SlotList] = {}

    # area/floor
    area_names: List[str] = []
    floor_names: List[str] = []
    for area in fixtures["areas"]:
        area_name = area["name"]
        if is_template(area_name):
            area_names.extend(
                area_name.strip()
                for area_name in sample_expression(parse_sentence(area_name))
            )
        else:
            area_names.append(area_name.strip())

        floor_name = area.get("floor")
        if not floor_name:
            continue

        if is_template(floor_name):
            floor_names.extend(
                floor_name.strip()
                for floor_name in sample_expression(parse_sentence(floor_name))
            )
        else:
            floor_names.append(floor_name.strip())

    slot_lists["area"] = TextSlotList.from_strings(area_names)
    slot_lists["floor"] = TextSlotList.from_strings(floor_names)

    # name
    entity_tuples: List[Tuple[str, str, Dict[str, Any]]] = []
    for entity in fixtures["entities"]:
        context = _entity_context(entity)
        entity_name = entity["name"]
        if is_template(entity_name):
            entity_names = list(
                name.strip() for name in sample_expression(parse_sentence(entity_name))
            )
        else:
            entity_names = [entity_name.strip()]

        entity_tuples.extend((name, name, context) for name in entity_names)

    slot_lists["name"] = TextSlotList.from_tuples(entity_tuples)

    return slot_lists


def _entity_context(entity: dict[str, Any]) -> dict[str, Any]:
    """Extract matching context from test fixture entity."""
    entity_id = entity["id"]
    domain = entity_id.split(".", maxsplit=1)[0]
    return {"domain": domain, **entity.get("attributes", {})}


def get_states(fixtures: dict[str, Any]) -> List[State]:
    """Load entity states from test fixtures."""
    states: List[State] = []
    for entity in fixtures.get("entities", []):
        # State may either be a string or a dict with in/out, where "in" is the
        # human (translated) name and "out" is the Home Assistant state name.
        entity_state = entity.get("state", "off")
        if isinstance(entity_state, str):
            hass_state = entity_state
            human_state: Optional[str] = None
        else:
            human_state = entity_state["in"]
            hass_state = entity_state["out"]

        entity_names: List[str] = []
        entity_name = entity["name"]
        if is_template(entity_name):
            entity_names.extend(
                entity_name.strip()
                for entity_name in sample_expression(parse_sentence(entity_name))
            )
        else:
            entity_names.append(entity_name.strip())

        states.append(
            State(
                entity_id=entity["id"],
                name=entity_names[0],
                aliases=set(entity_names[1:]),
                hass_state=hass_state,
                human_state=human_state,
                area_id=entity.get("area"),
                attributes=entity.get("attributes", {}),
            )
        )
    return states


def get_areas(fixtures: dict[str, Any]) -> List[AreaEntry]:
    """Load areas from test fixtures."""
    areas: List[AreaEntry] = []
    for area in fixtures.get("areas", []):
        area_names: List[str] = []
        area_name = area["name"]
        if is_template(area_name):
            area_names.extend(
                area_name.strip()
                for area_name in sample_expression(parse_sentence(area_name))
            )
        else:
            area_names.append(area_name.strip())

        areas.append(
            AreaEntry(id=area["id"], name=area_names[0], aliases=set(area_names[1:]))
        )
    return areas
