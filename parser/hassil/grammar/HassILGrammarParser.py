# Generated from HassILGrammar.g4 by ANTLR 4.11.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,17,71,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,1,0,1,0,3,0,23,8,0,1,1,1,1,1,1,1,1,1,1,
        3,1,30,8,1,1,1,1,1,3,1,34,8,1,1,1,5,1,37,8,1,10,1,12,1,40,9,1,1,
        2,1,2,1,2,1,2,1,3,1,3,1,3,1,3,1,4,3,4,51,8,4,1,4,1,4,3,4,55,8,4,
        1,5,1,5,1,6,1,6,1,6,1,6,1,7,1,7,1,8,1,8,1,8,1,8,1,9,1,9,1,9,0,0,
        10,0,2,4,6,8,10,12,14,16,18,0,0,69,0,20,1,0,0,0,2,29,1,0,0,0,4,41,
        1,0,0,0,6,45,1,0,0,0,8,50,1,0,0,0,10,56,1,0,0,0,12,58,1,0,0,0,14,
        62,1,0,0,0,16,64,1,0,0,0,18,68,1,0,0,0,20,22,3,2,1,0,21,23,5,16,
        0,0,22,21,1,0,0,0,22,23,1,0,0,0,23,1,1,0,0,0,24,30,3,4,2,0,25,30,
        3,6,3,0,26,30,3,10,5,0,27,30,3,12,6,0,28,30,3,16,8,0,29,24,1,0,0,
        0,29,25,1,0,0,0,29,26,1,0,0,0,29,27,1,0,0,0,29,28,1,0,0,0,30,38,
        1,0,0,0,31,34,5,17,0,0,32,34,3,8,4,0,33,31,1,0,0,0,33,32,1,0,0,0,
        34,35,1,0,0,0,35,37,3,2,1,0,36,33,1,0,0,0,37,40,1,0,0,0,38,36,1,
        0,0,0,38,39,1,0,0,0,39,3,1,0,0,0,40,38,1,0,0,0,41,42,5,1,0,0,42,
        43,3,2,1,0,43,44,5,2,0,0,44,5,1,0,0,0,45,46,5,3,0,0,46,47,3,2,1,
        0,47,48,5,4,0,0,48,7,1,0,0,0,49,51,5,17,0,0,50,49,1,0,0,0,50,51,
        1,0,0,0,51,52,1,0,0,0,52,54,5,5,0,0,53,55,5,17,0,0,54,53,1,0,0,0,
        54,55,1,0,0,0,55,9,1,0,0,0,56,57,5,10,0,0,57,11,1,0,0,0,58,59,5,
        6,0,0,59,60,3,14,7,0,60,61,5,7,0,0,61,13,1,0,0,0,62,63,5,10,0,0,
        63,15,1,0,0,0,64,65,5,8,0,0,65,66,3,18,9,0,66,67,5,9,0,0,67,17,1,
        0,0,0,68,69,5,10,0,0,69,19,1,0,0,0,6,22,29,33,38,50,54
    ]

class HassILGrammarParser ( Parser ):

    grammarFileName = "HassILGrammar.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'('", "')'", "'['", "']'", "'|'", "'{'", 
                     "'}'", "'<'", "'>'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "STRING", "QUOTED_STRING", 
                      "QUOTED_ESC", "UNQUOTED_STRING", "UNQUOTED_ESC", "CHARACTER", 
                      "EOL", "WS" ]

    RULE_sentence = 0
    RULE_expression = 1
    RULE_group = 2
    RULE_optional = 3
    RULE_alt = 4
    RULE_word = 5
    RULE_list = 6
    RULE_list_name = 7
    RULE_rule = 8
    RULE_rule_name = 9

    ruleNames =  [ "sentence", "expression", "group", "optional", "alt", 
                   "word", "list", "list_name", "rule", "rule_name" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    STRING=10
    QUOTED_STRING=11
    QUOTED_ESC=12
    UNQUOTED_STRING=13
    UNQUOTED_ESC=14
    CHARACTER=15
    EOL=16
    WS=17

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.11.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class SentenceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self):
            return self.getTypedRuleContext(HassILGrammarParser.ExpressionContext,0)


        def EOL(self):
            return self.getToken(HassILGrammarParser.EOL, 0)

        def getRuleIndex(self):
            return HassILGrammarParser.RULE_sentence

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSentence" ):
                listener.enterSentence(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSentence" ):
                listener.exitSentence(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSentence" ):
                return visitor.visitSentence(self)
            else:
                return visitor.visitChildren(self)




    def sentence(self):

        localctx = HassILGrammarParser.SentenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_sentence)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 20
            self.expression()
            self.state = 22
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==16:
                self.state = 21
                self.match(HassILGrammarParser.EOL)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def group(self):
            return self.getTypedRuleContext(HassILGrammarParser.GroupContext,0)


        def optional(self):
            return self.getTypedRuleContext(HassILGrammarParser.OptionalContext,0)


        def word(self):
            return self.getTypedRuleContext(HassILGrammarParser.WordContext,0)


        def list_(self):
            return self.getTypedRuleContext(HassILGrammarParser.ListContext,0)


        def rule_(self):
            return self.getTypedRuleContext(HassILGrammarParser.RuleContext,0)


        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(HassILGrammarParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(HassILGrammarParser.ExpressionContext,i)


        def WS(self, i:int=None):
            if i is None:
                return self.getTokens(HassILGrammarParser.WS)
            else:
                return self.getToken(HassILGrammarParser.WS, i)

        def alt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(HassILGrammarParser.AltContext)
            else:
                return self.getTypedRuleContext(HassILGrammarParser.AltContext,i)


        def getRuleIndex(self):
            return HassILGrammarParser.RULE_expression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpression" ):
                listener.enterExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpression" ):
                listener.exitExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression" ):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = HassILGrammarParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_expression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 29
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1]:
                self.state = 24
                self.group()
                pass
            elif token in [3]:
                self.state = 25
                self.optional()
                pass
            elif token in [10]:
                self.state = 26
                self.word()
                pass
            elif token in [6]:
                self.state = 27
                self.list_()
                pass
            elif token in [8]:
                self.state = 28
                self.rule_()
                pass
            else:
                raise NoViableAltException(self)

            self.state = 38
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,3,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 33
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,2,self._ctx)
                    if la_ == 1:
                        self.state = 31
                        self.match(HassILGrammarParser.WS)
                        pass

                    elif la_ == 2:
                        self.state = 32
                        self.alt()
                        pass


                    self.state = 35
                    self.expression() 
                self.state = 40
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,3,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class GroupContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self):
            return self.getTypedRuleContext(HassILGrammarParser.ExpressionContext,0)


        def getRuleIndex(self):
            return HassILGrammarParser.RULE_group

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterGroup" ):
                listener.enterGroup(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitGroup" ):
                listener.exitGroup(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitGroup" ):
                return visitor.visitGroup(self)
            else:
                return visitor.visitChildren(self)




    def group(self):

        localctx = HassILGrammarParser.GroupContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_group)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 41
            self.match(HassILGrammarParser.T__0)
            self.state = 42
            self.expression()
            self.state = 43
            self.match(HassILGrammarParser.T__1)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OptionalContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self):
            return self.getTypedRuleContext(HassILGrammarParser.ExpressionContext,0)


        def getRuleIndex(self):
            return HassILGrammarParser.RULE_optional

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOptional" ):
                listener.enterOptional(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOptional" ):
                listener.exitOptional(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOptional" ):
                return visitor.visitOptional(self)
            else:
                return visitor.visitChildren(self)




    def optional(self):

        localctx = HassILGrammarParser.OptionalContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_optional)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 45
            self.match(HassILGrammarParser.T__2)
            self.state = 46
            self.expression()
            self.state = 47
            self.match(HassILGrammarParser.T__3)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AltContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WS(self, i:int=None):
            if i is None:
                return self.getTokens(HassILGrammarParser.WS)
            else:
                return self.getToken(HassILGrammarParser.WS, i)

        def getRuleIndex(self):
            return HassILGrammarParser.RULE_alt

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAlt" ):
                listener.enterAlt(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAlt" ):
                listener.exitAlt(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAlt" ):
                return visitor.visitAlt(self)
            else:
                return visitor.visitChildren(self)




    def alt(self):

        localctx = HassILGrammarParser.AltContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_alt)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 50
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==17:
                self.state = 49
                self.match(HassILGrammarParser.WS)


            self.state = 52
            self.match(HassILGrammarParser.T__4)
            self.state = 54
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==17:
                self.state = 53
                self.match(HassILGrammarParser.WS)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WordContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(HassILGrammarParser.STRING, 0)

        def getRuleIndex(self):
            return HassILGrammarParser.RULE_word

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWord" ):
                listener.enterWord(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWord" ):
                listener.exitWord(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWord" ):
                return visitor.visitWord(self)
            else:
                return visitor.visitChildren(self)




    def word(self):

        localctx = HassILGrammarParser.WordContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_word)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 56
            self.match(HassILGrammarParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def list_name(self):
            return self.getTypedRuleContext(HassILGrammarParser.List_nameContext,0)


        def getRuleIndex(self):
            return HassILGrammarParser.RULE_list

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterList" ):
                listener.enterList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitList" ):
                listener.exitList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitList" ):
                return visitor.visitList(self)
            else:
                return visitor.visitChildren(self)




    def list_(self):

        localctx = HassILGrammarParser.ListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_list)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 58
            self.match(HassILGrammarParser.T__5)
            self.state = 59
            self.list_name()
            self.state = 60
            self.match(HassILGrammarParser.T__6)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class List_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(HassILGrammarParser.STRING, 0)

        def getRuleIndex(self):
            return HassILGrammarParser.RULE_list_name

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterList_name" ):
                listener.enterList_name(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitList_name" ):
                listener.exitList_name(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitList_name" ):
                return visitor.visitList_name(self)
            else:
                return visitor.visitChildren(self)




    def list_name(self):

        localctx = HassILGrammarParser.List_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_list_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 62
            self.match(HassILGrammarParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RuleContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def rule_name(self):
            return self.getTypedRuleContext(HassILGrammarParser.Rule_nameContext,0)


        def getRuleIndex(self):
            return HassILGrammarParser.RULE_rule

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRule" ):
                listener.enterRule(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRule" ):
                listener.exitRule(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule" ):
                return visitor.visitRule(self)
            else:
                return visitor.visitChildren(self)




    def rule_(self):

        localctx = HassILGrammarParser.RuleContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_rule)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 64
            self.match(HassILGrammarParser.T__7)
            self.state = 65
            self.rule_name()
            self.state = 66
            self.match(HassILGrammarParser.T__8)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Rule_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(HassILGrammarParser.STRING, 0)

        def getRuleIndex(self):
            return HassILGrammarParser.RULE_rule_name

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRule_name" ):
                listener.enterRule_name(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRule_name" ):
                listener.exitRule_name(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRule_name" ):
                return visitor.visitRule_name(self)
            else:
                return visitor.visitChildren(self)




    def rule_name(self):

        localctx = HassILGrammarParser.Rule_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_rule_name)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 68
            self.match(HassILGrammarParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





