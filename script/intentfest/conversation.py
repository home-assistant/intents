#!/usr/bin/env python

"""Simulate a conversation to check what the conversation would look like."""
from __future__ import annotations

import argparse
import traceback

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
        "--debug-response",
        help="Set to 1 to show more info about response.",
    )

    return parser.parse_args()


class InstructionsI18n:
    def __init__(self, languageKey="en") -> None:
        self.fallbackLanguage = "en"

        # Feel free to add texts in your language ;)
        self.instructionsI18n = {
            "en": {
                "HELLO_TEXT": 'Write here your query, or type \'a\' (or "arrow up" on keyboard), to repeat the last one question. Type in \'r\' to reload intents (after changing "sentences" or "responses").',
                "DEBUG": "Debug",
                "DEBUG_ON": "ON",
                "DEBUG_OFF": "OFF",
                "NEW_INTENTS_RELOADED": "New intents reloaded!",
                "ERROR_OCCURRED": "Oops! There's been an error:",
                "NO_AVAILABLE_RESPONSE": "(Sorry, there is no response for this)",
            },
            "pl": {
                "HELLO_TEXT": "Napisz o co checesz się zapytać, ewentualnie napisz 'a' (lub sztrzałka w górę na klawiaturze), aby powtórzyć ostatnie zapyatnie. Możesz też napisać 'r', aby przeładować pliki językowe (np. po zmianie \"sentences\", lub \"responses\").",
                "DEBUG": "Debug",
                "DEBUG_ON": "ON",
                "DEBUG_OFF": "OFF",
                "NEW_INTENTS_RELOADED": "Przeładowano pliki językowe!",
                "ERROR_OCCURRED": "Whoops! Wystrąpił bląd:",
                "NO_AVAILABLE_RESPONSE": "(niestety, brak odpowidzi)",
            },
        }

        self.language = None
        if languageKey not in self.instructionsI18n:
            self.language = "en"
        else:
            self.language = languageKey

    def get(self, key):
        languageSet = self.instructionsI18n[self.language]
        if key not in languageSet:
            fallbackLanguageSet = self.instructionsI18n[self.fallbackLanguage]
            if key not in fallbackLanguageSet:
                raise Exception(
                    f'Can\'t find the key "{key}" in language set "{self.language}" (and in default language set "{self.fallbackLanguage}" also).'
                )
            return fallbackLanguageSet[key]
        return languageSet[key]


class Conversation:
    def __init__(self, language, debug=False) -> None:
        self.language = language
        self.localDebug = False if debug is None or debug is False else bool(int(debug))

        self.sentenceParser = SentenceParser(self.language)
        self.instructionsI18n = InstructionsI18n(self.language)

        self.lastSentence = ""

    def askUser(self):
        promptSign = "<<<"
        userSentence = input(f"{promptSign} ")

        # Toggle debug
        if userSentence.lower() == "d":
            self.localDebug = not self.localDebug
            print(
                f"{self.instructionsI18n.get('DEBUG')}: {self.instructionsI18n.get('DEBUG_ON') if self.localDebug else self.instructionsI18n.get('DEBUG_OFF')}"
            )

        # Do intents reload
        elif userSentence.lower() == "r":
            self.sentenceParser.prepareNewIntents(self.language)
            print(self.instructionsI18n.get("NEW_INTENTS_RELOADED"))

        # Repeat the last query
        elif userSentence.lower() == "a" or userSentence == "\u001b[A":
            userSentence = self.lastSentence
            print(f"{promptSign} {userSentence}")
            return userSentence
        else:
            return userSentence

        return False

    def do(self):
        print(self.instructionsI18n.get("HELLO_TEXT"), "\n")

        while True:
            userSentence = self.askUser()
            if userSentence is not False:
                self.lastSentence = userSentence
                responseForUser = None
                responseDebug = None

                try:
                    if self.sentenceParser.parse(userSentence):
                        responseForUser = self.sentenceParser.getResponseForHuman()
                        responseDebug = self.sentenceParser.getWholeResponseDebug()
                except Exception:
                    print(self.instructionsI18n.get("ERROR_OCCURRED"))
                    traceback.print_exc()

                print(
                    f'>>> {responseForUser if responseForUser is not None else self.instructionsI18n.get("NO_AVAILABLE_RESPONSE")}'
                )
                if self.localDebug:
                    print(f'{self.instructionsI18n.get("DEBUG")}: {responseDebug}')
                    print("------------------------------")


def run() -> int:
    args = get_arguments()
    conversation = Conversation(args.language, args.debug_response)
    conversation.do()
    # Liter said 'Missing return statement',
    # but this particular return is unreachable.
    # That is why it is here.
    return 0
