# Generated from HassILGrammar.g4 by ANTLR 4.11.1
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .HassILGrammarParser import HassILGrammarParser
else:
    from HassILGrammarParser import HassILGrammarParser

# This class defines a complete generic visitor for a parse tree produced by HassILGrammarParser.


class HassILGrammarVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by HassILGrammarParser#document.
    def visitDocument(self, ctx: HassILGrammarParser.DocumentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#sentence.
    def visitSentence(self, ctx: HassILGrammarParser.SentenceContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#expression.
    def visitExpression(self, ctx: HassILGrammarParser.ExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#group.
    def visitGroup(self, ctx: HassILGrammarParser.GroupContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#optional.
    def visitOptional(self, ctx: HassILGrammarParser.OptionalContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#alt.
    def visitAlt(self, ctx: HassILGrammarParser.AltContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#text_chunk.
    def visitText_chunk(self, ctx: HassILGrammarParser.Text_chunkContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#list.
    def visitList(self, ctx: HassILGrammarParser.ListContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#list_name.
    def visitList_name(self, ctx: HassILGrammarParser.List_nameContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#rule.
    def visitRule(self, ctx: HassILGrammarParser.RuleContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by HassILGrammarParser#rule_name.
    def visitRule_name(self, ctx: HassILGrammarParser.Rule_nameContext):
        return self.visitChildren(ctx)


del HassILGrammarParser
