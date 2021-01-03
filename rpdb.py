import sys
import cpython.Lib.pdb as pdb
from copy import copy

global instance

DEBUG = True

class Line():
    def __init__(self, frame):
        for attr in dir(frame):
            # Ignore private functions
            if attr[0] == "_":
                continue
            if attr == "f_back":
                setattr(self, attr, getattr(frame, attr))
            else:
                setattr(self, attr, copy(getattr(frame, attr)))
        self._frame = frame

    def __str__(self):
        return f"\nline: {self.f_lineno}\nlocals : {self.f_locals}"

class rPdb(pdb.Pdb):
    def __init__(self):
        super().__init__(skip=__name__)
        self.muted_modules = ["rpdb","pdb", "bdb", "cmd"]
        self.trace_set = False
        self.quitting = False
        self.line_stack = []
        self.in_hidden_scope = True

    def start(self):
        frame = sys._getframe().f_back
        self.reset()
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        sys.settrace(self.trace_dispatch)

    def trace_dispatch(self, frame, event, arg):
        if frame.f_globals["__name__"] in __name__:
            self.in_hidden_scope = True
            return self.trace_dispatch
        if self.in_hidden_scope:
            if frame.f_globals["__name__"] == "__main__":
                self.in_hidden_scope = False
                return self.trace_dispatch(frame,event,arg)
            return self.trace_dispatch
        if DEBUG:
            print(f"Saving line obj {frame}")
        line = Line(frame)
        self.line_stack.append(line)
        if self.trace_set:
            super().trace_dispatch(frame, event, arg)
        return self.trace_dispatch

    # pdb override
    def _getval(self, arg):
        try:
            return eval(arg, self.curframe_globals, self.curframe_locals)
        except:
            exc_info = sys.exc_info()[:2]
            self.error(traceback.format_exception_only(*exc_info)[-1].strip())
            raise

    # pdb override
    def default(self, line):
        if line[:1] == '!': line = line[1:]
        locals = self.curframe_locals
        globals = self.curframe_globals
        try:
            code = compile(line + '\n', '<stdin>', 'single')
            save_stdout = sys.stdout
            save_stdin = sys.stdin
            save_displayhook = sys.displayhook
            try:
                sys.stdin = self.stdin
                sys.stdout = self.stdout
                sys.displayhook = self.displayhook
                exec(code, globals, locals)
            finally:
                sys.stdout = save_stdout
                sys.stdin = save_stdin
                sys.displayhook = save_displayhook
        except Exception as e:
            print(e)

    def do_reverse(self, arg):
        # Current line
        self.line_stack.pop()
        previous_line = self.line_stack[-1]
        frame = sys._getframe()
        while frame:
            if frame.f_globals["__name__"] == "__main__":
                break
            frame = frame.f_back
        if self.setup(frame, None):
            # no interaction desired at this time (happens if .pdbrc contains
            # a command like "continue")
            self.forget()
            return
        self.curframe_locals = previous_line.f_locals
        self.curframe_globals = previous_line.f_globals
        self._set_stopinfo(frame, None)
        plineno = previous_line.f_lineno
        self.do_jump(plineno)
        self._cmdloop()
        self.forget()
        return 1

    do_re = do_reverse

    def set_trace(self):
        return super().set_trace(sys._getframe().f_back)

def set_trace():
    instance.set_trace()
    instance.trace_set = True

instance = rPdb()
instance.start()
