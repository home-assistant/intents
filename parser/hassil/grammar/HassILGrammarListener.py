# Generated from HassILGrammar.g4 by ANTLR 4.11.1
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .HassILGrammarParser import HassILGrammarParser
else:
    from HassILGrammarParser import HassILGrammarParser

# This class defines a complete listener for a parse tree produced by HassILGrammarParser.
class HassILGrammarListener(ParseTreeListener):

    # Enter a parse tree produced by HassILGrammarParser#document.
    def enterDocument(self, ctx: HassILGrammarParser.DocumentContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#document.
    def exitDocument(self, ctx: HassILGrammarParser.DocumentContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#sentence.
    def enterSentence(self, ctx: HassILGrammarParser.SentenceContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#sentence.
    def exitSentence(self, ctx: HassILGrammarParser.SentenceContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#expression.
    def enterExpression(self, ctx: HassILGrammarParser.ExpressionContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#expression.
    def exitExpression(self, ctx: HassILGrammarParser.ExpressionContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#group.
    def enterGroup(self, ctx: HassILGrammarParser.GroupContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#group.
    def exitGroup(self, ctx: HassILGrammarParser.GroupContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#optional.
    def enterOptional(self, ctx: HassILGrammarParser.OptionalContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#optional.
    def exitOptional(self, ctx: HassILGrammarParser.OptionalContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#alt.
    def enterAlt(self, ctx: HassILGrammarParser.AltContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#alt.
    def exitAlt(self, ctx: HassILGrammarParser.AltContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#text_chunk.
    def enterText_chunk(self, ctx: HassILGrammarParser.Text_chunkContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#text_chunk.
    def exitText_chunk(self, ctx: HassILGrammarParser.Text_chunkContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#list.
    def enterList(self, ctx: HassILGrammarParser.ListContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#list.
    def exitList(self, ctx: HassILGrammarParser.ListContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#list_name.
    def enterList_name(self, ctx: HassILGrammarParser.List_nameContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#list_name.
    def exitList_name(self, ctx: HassILGrammarParser.List_nameContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#rule.
    def enterRule(self, ctx: HassILGrammarParser.RuleContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#rule.
    def exitRule(self, ctx: HassILGrammarParser.RuleContext):
        pass

    # Enter a parse tree produced by HassILGrammarParser#rule_name.
    def enterRule_name(self, ctx: HassILGrammarParser.Rule_nameContext):
        pass

    # Exit a parse tree produced by HassILGrammarParser#rule_name.
    def exitRule_name(self, ctx: HassILGrammarParser.Rule_nameContext):
        pass


del HassILGrammarParser
