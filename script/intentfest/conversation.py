#!/usr/bin/env python

"""Simulate a conversation to check what the conversation would look like."""
from __future__ import annotations

import argparse
import json
import traceback
from threading import Thread
from time import sleep, time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from .const import LANGUAGES
from .sentenceParser import SentenceParser
from .util import get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed parameters passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language",
        required=True,
        type=str,
        choices=LANGUAGES,
        help="The language to validate.",
    )
    parser.add_argument(
        "--no-response-debug",
        action="store_true",
        help="If set, there will be no response debug data.",
    )

    return parser.parse_args()


class SentencesFilesWatcher(PatternMatchingEventHandler):
    def __init__(self, callback_files_finished_changing, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.last_modification_time = None
        self.running = False
        self.callback_files_finished_changing = callback_files_finished_changing

    def was_change(self):
        if not self.running:
            self.running = True
            while time() - self.last_modification_time <= 0.3:
                sleep(0.1)
            self.running = False

            self.callback_files_finished_changing()

    def on_any_event(self, event):
        self.last_modification_time = time()
        Thread(target=self.was_change).start()


class Conversation:
    def __init__(self, language, debug=True) -> None:
        self.language = language
        self.local_debug = debug

        self.sentence_parser = SentenceParser(self.language)

        self.last_sentence = ""
        self.have_a_conversation = True

    def reload_sentences(self):
        self.sentence_parser.prepare_new_sentences(self.language)
        print("\nNew intents reloaded!")

    def ask_user(self):
        prompt_sign = "<<<"
        user_sentence = input(f"{prompt_sign} ")

        # Toggle debug
        if user_sentence.lower() == "d":
            self.local_debug = not self.local_debug
            print(f"Debug: {'ON' if self.local_debug else 'OFF'}")

        # Quit conversation
        elif user_sentence.lower() == "q":
            self.have_a_conversation = False

        # Repeat the last query
        elif user_sentence.lower() == "a" or user_sentence == "\u001b[A":
            user_sentence = self.last_sentence
            print(f"{prompt_sign} {user_sentence}")
            return user_sentence
        else:
            return user_sentence

        return False

    def do(self):
        print(
            "Type your query here, or type 'a' (or 'arrow up' on the keyboard) to repeat it. Type 'q' (or CTRL+C) to end the conversation.\n"
        )

        while self.have_a_conversation:
            try:
                user_sentence = self.ask_user()
            except KeyboardInterrupt:
                print()
                break

            if user_sentence is not False:
                self.last_sentence = user_sentence
                response_for_user = None
                response_debug = None

                try:
                    sentence_parsing_result = self.sentence_parser.parse(user_sentence)
                    parsed_qeury_response_data = (
                        self.sentence_parser.get_response_data()
                    )
                    response_debug = json.dumps(
                        parsed_qeury_response_data, ensure_ascii=False, indent=2
                    )

                    if sentence_parsing_result:
                        response_for_user = parsed_qeury_response_data["response"]

                except Exception:
                    print("Oops! There's been an error:")
                    traceback.print_exc()

                print(
                    f'>>> {response_for_user if response_for_user is not None else "(Sorry, there is no response for this)"}'
                )
                if self.local_debug:
                    print(f"Debug: {response_debug}")
                    print("------------------------------")

        print(">>> Bye!")


def run() -> int:
    args = get_arguments()
    conversation = Conversation(args.language, not args.no_response_debug)

    sentences_files_wathcer = SentencesFilesWatcher(
        conversation.reload_sentences,
        patterns=["*.yaml", "*.yml"],
        ignore_directories=True,
    )
    path = "."
    observer = Observer()
    observer.schedule(sentences_files_wathcer, path, recursive=True)
    observer.start()

    conversation.do()

    observer.stop()
    observer.join()
    return 0
