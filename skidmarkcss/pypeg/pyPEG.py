# YPL parser 1.2.1

# written by VB.

import re
import sys, codecs
import exceptions

class keyword(unicode): pass
class code(unicode): pass
class ignore(object):
    def __init__(self, regex_text):
        self.regex = re.compile(regex_text)

class _and(object):
    def __init__(self, something):
        self.obj = something

class _not(_and): pass

class Name(unicode):
    def __init__(self, *args):
        self.line = 0
        self.file = u""

word_regex = re.compile(ur"\w+")
rest_regex = re.compile(ur".*")

print_trace = False

def u(text):
    if isinstance(text, exceptions.BaseException):
        text = text.args[0]
    if type(text) is unicode:
        return text
    if isinstance(text, str):
        if sys.stdin.encoding:
            return codecs.decode(text, sys.stdin.encoding)
        else:
            return codecs.decode(text, "utf-8")
    return unicode(text)

def skip(skipper, text, pattern, skipWS, skipComments):
    if skipWS:
        t = text.strip()
    else:
        t = text
    if skipComments:
        try:
            while True:
                skip, t = skipper.parseLine(t, skipComments, [], skipWS, None)
                if skipWS:
                    t = t.strip()
        except: pass
    return t

class parser(object):
    def __init__(self, another = False):
        self.restlen = -1 
        if not(another):
            self.skipper = parser(True)
        else:
            self.skipper = self
        self.lines = None
        self.textlen = 0
        self.memory = {}
        self.packrat = False

    # parseLine():
    #   textline:       text to parse
    #   pattern:        pyPEG language description
    #   resultSoFar:    parsing result so far (default: blank list [])
    #   skipWS:         Flag if whitespace should be skipped (default: True)
    #   skipComments:   Python functions returning pyPEG for matching comments
    #   
    #   returns:        pyAST, textrest
    #
    #   raises:         SyntaxError(reason) if textline is detected not being in language
    #                   described by pattern
    #
    #                   SyntaxError(reason) if pattern is an illegal language description

    def parseLine(self, textline, pattern, resultSoFar = [], skipWS = True, skipComments = None):
        name = None
        _textline = textline
        _pattern = pattern
        _packrat = self.packrat
        _memory = self.memory

        def R(result, text):
            if __debug__:
                if print_trace:
                    try:
                        if _pattern.__name__ != "comment":
                            sys.stderr.write(u"match: " + _pattern.__name__ + u"\n")
                    except: pass

            if self.restlen == -1:
                self.restlen = len(text)
            else:
                self.restlen = min(self.restlen, len(text))
            res = resultSoFar
            if name and result:
                res.append((name, result))
            elif name:
                res.append((name, []))
            elif result:
                if type(result) is type([]):
                    res.extend(result)
                else:
                    res.extend([result])
            if _packrat:
                if name:
                    _memory[(len(_textline), id(_pattern))] = (res, text)
            return res, text

        def syntaxError():
            if _packrat:
                if name:
                    _memory[(len(_textline), id(_pattern))] = False
            raise SyntaxError()

        if callable(pattern):
            if __debug__:
                if print_trace:
                    try:
                        if pattern.__name__ != "comment":
                            sys.stderr.write(u"testing with " + pattern.__name__ + u": " + textline[:40] + u"\n")
                    except: pass

            if _packrat:
                try:
                    result = _memory[(len(_textline), id(_pattern))]
                    if result:
                        return result
                    else:
                        raise SyntaxError()
                except: pass

            if pattern.__name__[0] != "_":
                name = Name(pattern.__name__)
                name.line = self.lineNo()

            pattern = pattern()
            if callable(pattern):
                pattern = (pattern,)

        text = skip(self.skipper, textline, pattern, skipWS, skipComments)

        pattern_type = type(pattern)

        if pattern_type is str or pattern_type is unicode:
            if text[:len(pattern)] == pattern:
                text = skip(self.skipper, text[len(pattern):], pattern, skipWS, skipComments)
                return R(None, text)
            else:
                syntaxError()

        elif pattern_type is keyword:
            m = word_regex.match(text)
            if m:
                if m.group(0) == pattern:
                    text = skip(self.skipper, text[len(pattern):], pattern, skipWS, skipComments)
                    return R(None, text)
                else:
                    syntaxError()
            else:
                syntaxError()

        elif pattern_type is _not:
            try:
                r, t = self.parseLine(text, pattern.obj, [], skipWS, skipComments)
            except:
                return resultSoFar, textline
            syntaxError()

        elif pattern_type is _and:
            r, t = self.parseLine(text, pattern.obj, [], skipWS, skipComments)
            return resultSoFar, textline

        elif pattern_type is type(word_regex) or pattern_type is ignore:
            if pattern_type is ignore:
                pattern = pattern.regex
            m = pattern.match(text)
            if m:
                text = skip(self.skipper, text[len(m.group(0)):], pattern, skipWS, skipComments)
                if pattern_type is ignore:
                    return R(None, text)
                else:
                    return R(m.group(0), text)
            else:
                syntaxError()

        elif pattern_type is tuple:
            result = []
            n = 1
            for p in pattern:
                if type(p) is type(0):
                    n = p
                else:
                    if n>0:
                        for i in range(n):
                            result, text = self.parseLine(text, p, result, skipWS, skipComments)
                    elif n==0:
                        if text == "":
                            pass
                        else:
                            try:
                                newResult, newText = self.parseLine(text, p, result, skipWS, skipComments)
                                result, text = newResult, newText
                            except SyntaxError:
                                pass
                    elif n<0:
                        found = False
                        while True:
                            try:
                                newResult, newText = self.parseLine(text, p, result, skipWS, skipComments)
                                result, text, found = newResult, newText, True
                            except SyntaxError:
                                break
                        if n == -2 and not(found):
                            syntaxError()
                    n = 1
            return R(result, text)

        elif pattern_type is list:
            result = []
            found = False
            for p in pattern:
                try:
                    result, text = self.parseLine(text, p, result, skipWS, skipComments)
                    found = True
                except SyntaxError:
                    pass
                if found:
                    break
            if found:
                return R(result, text)
            else:
                syntaxError()

        else:
            raise SyntaxError(u"illegal type in grammar: " + u(pattern_type))

    def lineNo(self):
        if not(self.lines): return u""
        if self.restlen == -1: return u""
        parsed = self.textlen - self.restlen

        left, right = 0, len(self.lines)

        while True:
            mid = int((right + left) / 2)
            if self.lines[mid][0] <= parsed:
                try:
                    if self.lines[mid + 1][0] >= parsed:
                        try:
                            return u(self.lines[mid + 1][1]) + u":" + u(self.lines[mid + 1][2])
                        except:
                            return u""
                    else:
                        left = mid + 1
                except:
                    try:
                        return u(self.lines[mid + 1][1]) + u":" + u(self.lines[mid + 1][2])
                    except:
                        return u""
            else:
                right = mid - 1
            if left > right:
                return u""

# plain module API

def parseLine(textline, pattern, resultSoFar = [], skipWS = True, skipComments = None, packrat = False):
    p = parser()
    p.packrat = packrat
    text = skip(p.skipper, textline, pattern, skipWS, skipComments)
    ast, text = p.parseLine(text, pattern, resultSoFar, skipWS, skipComments)
    return ast, text

# parse():
#   language:       pyPEG language description
#   lineSource:     a fileinput.FileInput object
#   skipWS:         Flag if whitespace should be skipped (default: True)
#   skipComments:   Python function which returns pyPEG for matching comments
#   packrat:        use memoization
#   lineCount:      add line number information to AST
#   
#   returns:        pyAST
#
#   raises:         SyntaxError(reason), if a parsed line is not in language
#                   SyntaxError(reason), if the language description is illegal

def parse(language, lineSource, skipWS = True, skipComments = None, packrat = False, lineCount = True):
    lines, lineNo = [], 0

    while callable(language):
        language = language()

    orig, ld = u"", 0
    for line in lineSource:
        if lineSource.isfirstline():
            ld = 1
        else:
            ld += 1
        lines.append((len(orig), lineSource.filename(), lineSource.lineno() - 1))
        orig += u(line)

    textlen = len(orig)

    try:
        p = parser()
        p.packrat = packrat
        p.textlen = len(orig)
        if lineCount:
            p.lines = lines
        else:
            p.line = None
        text = skip(p.skipper, orig, language, skipWS, skipComments)
        result, text = p.parseLine(text, language, [], skipWS, skipComments)
        if text:
            raise SyntaxError()

    except SyntaxError, msg:
        parsed = textlen - p.restlen
        textlen = 0
        nn, lineNo, file = 0, 0, u""
        for n, ld, l in lines:
            if n >= parsed:
                break
            else:
                lineNo = l
                nn += 1
                file = ld

        lineNo += 1
        nn -= 1
        lineCont = orig.splitlines()[nn]
        raise SyntaxError(u"syntax error in " + u(file) + u":" + u(lineNo) + u": " + lineCont)

    return result
