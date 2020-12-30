import sys
import cpython.Lib.pdb as pdb
from copy import copy

global instance

DEBUG = True

class Line():
    def __init__(self, frame, lines):
        for attr in dir(frame):
            # Ignore private functions
            if attr == "f_back" or attr[0] == "_":
                continue
            else:
                setattr(self, attr, copy(getattr(frame, attr)))
        self._frame = frame
        n_frames = len(lines)
        for i in range(n_frames):
            f = lines[-1*(i+1)]
            if self._frame is not f._frame:
                self.f_back = f
                return
        self.f_back = None

class rPdb(pdb.Pdb):
    def __init__(self):
        super().__init__(skip=__name__)
        self.trace_set = False
        self.quitting = False
        self.lines = []
        self.in_hidden_scope = True

    def start(self, frame=None):
        if frame is None:
            frame = sys._getframe().f_back
        self.reset()
        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back
        self.in_hidden_scope = True
        sys.settrace(self.trace_dispatch)

    def trace_dispatch(self, frame, event, arg):
        if frame.f_globals["__name__"] == __name__:
            self.in_hidden_scope = True
            return self.trace_dispatch
        if self.in_hidden_scope:
            if frame.f_globals["__name__"] == "__main__":
                self.in_hidden_scope = False
                return self.trace_dispatch(frame,event,arg)
            return self.trace_dispatch
        if DEBUG:
            print(f"Saving line obj {frame}")
        line = Line(frame, self.lines)
        self.lines.append(line)
        if self.trace_set:
            super().trace_dispatch(line, event, arg)
        return self.trace_dispatch

    def stop_here(self, frame):
        return super().stop_here(self.get_line(frame))

    def get_line(self, frame):
        for f in self.lines:
            if f._frame is frame or f is frame:
                return f
        print("Could not find frame in frame stack")
        return None

    def do_reverse(self, arg):
        current_line = self.lines.pop()
        previous_line = self.lines.pop()
        self.interaction(previous_line, None)
        return 1

    do_re = do_reverse

    def set_trace(self):
        return super().set_trace(self.lines[-1])

def set_trace():
    instance.set_trace()
    instance.trace_set = True

instance = rPdb()
instance.start()
