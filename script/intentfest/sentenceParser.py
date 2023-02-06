#!/usr/bin/env python

"""Parse sentences using language intent files."""
from __future__ import annotations

import yaml
from hassil.intents import Intents
from hassil.recognize import recognize
from hassil.util import normalize_whitespace

from .const import TESTS_DIR
from .util import (
    get_slot_lists,
    load_merged_responses,
    load_merged_sentences,
    render_response,
)


class SentenceParser:
    def __init__(self, language) -> None:
        self.slot_lists = None
        self.intents = None
        self.responses = None

        self.output_dict = None

        self.prepare_new_sentences(language)

    def prepare_new_sentences(self, language):
        tests_dir = TESTS_DIR / language

        # Load test areas and entities for language
        test_names = yaml.safe_load((tests_dir / "_fixtures.yaml").read_text())
        self.slot_lists = get_slot_lists(test_names)

        # Load sentences
        sentences_dict = load_merged_sentences(language)

        assert sentences_dict, "No intent YAML files loaded"
        self.intents = Intents.from_dict(sentences_dict)

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

    def get_response_data(self):
        return self.output_dict
