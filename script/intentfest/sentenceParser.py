#!/usr/bin/env python

"""Parse sentences using language intent files."""
from __future__ import annotations

import json
from typing import Any, Dict

import yaml
from hassil.intents import Intents
from hassil.recognize import recognize
from hassil.util import merge_dict, normalize_whitespace

from .const import SENTENCE_DIR, TESTS_DIR
from .util import get_slot_lists, load_merged_responses, render_response


class SentenceParser:
    def __init__(self, language) -> None:
        self.slot_lists = None
        self.intents = None
        self.responses = None

        self.output_dict = None

        self.prepareNewIntents(language)

    def prepareNewIntents(self, language):
        language_dir = SENTENCE_DIR / language
        tests_dir = TESTS_DIR / language

        # Load test areas and entities for language
        test_names = yaml.safe_load((tests_dir / "_fixtures.yaml").read_text())
        self.slot_lists = get_slot_lists(test_names)

        # Load intents
        intents_dict: Dict[str, Any] = {}
        for intent_path in language_dir.glob("*.yaml"):
            with open(intent_path, "r", encoding="utf-8") as intent_file:
                merge_dict(intents_dict, yaml.safe_load(intent_file))

        assert intents_dict, "No intent YAML files loaded"
        self.intents = Intents.from_dict(intents_dict)

        self.responses = (
            load_merged_responses(language).get("responses", {}).get("intents", {})
        )

    def parse(self, sentence):
        # Parse sentence
        result = recognize(sentence, self.intents, slot_lists=self.slot_lists)
        self.output_dict = {"text": sentence, "match": result is not None}
        if result is not None:
            self.output_dict["intent"] = result.intent.name
            self.output_dict["slots"] = {
                entity.name: entity.value for entity in result.entities_list
            }

            # Response
            self.output_dict["response_key"] = result.response
            response_template = self.responses.get(result.intent.name, {}).get(
                result.response
            )
            self.output_dict["response"] = normalize_whitespace(
                render_response(response_template, result)
            ).strip()

            return True
        return False

    def getResponseForHuman(self):
        return self.output_dict["response"]

    def getWholeResponseDebug(self):
        return json.dumps(self.output_dict, ensure_ascii=False, indent=2)
