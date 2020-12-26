import sys
import cpython.Lib.pdb as pdb
from copy import copy

global instance

DEBUG = True

class Frame():
    def __init__(self, frame):
        for attr in dir(frame):
            # Ignore private functions
            if attr[0] == attr[1] and attr[0] == '_':
                continue
            setattr(self, attr, getattr(frame, attr))

class rPdb(pdb.Pdb):
    # Goal: Add ability to step forwarda nd backward through individual lines
    def __init__(self):
        super().__init__(skip=__name__)
        # Start dispatching events to trace_dispatch funciton
        self.trace_set = False
        self.quitting = False
        self.frame_stack = []
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

    # store frame info for reverse command
    def save_frame(self, frame, event, arg):
        if DEBUG:
            print(f"Saving frame {frame}")
        self.frame_stack.append(Frame(frame))

    def trace_dispatch(self, frame, event, arg):
        # Hide frames until we leave module scope
        if frame.f_globals["__name__"] == __name__:
            self.in_hidden_scope = True
            return self.trace_dispatch
        if self.in_hidden_scope:
            if frame.f_globals["__name__"] == "__main__":
                self.in_hidden_scope = False
                return self.trace_dispatch(frame,event,arg)
            return self.trace_dispatch
        self.save_frame(frame, event, arg)
        if self.trace_set:
            # pass to pdb if we're currently interacting
            super().trace_dispatch(frame, event, arg)
        return self.trace_dispatch

    # next command in opposite directions
    def do_reverse(self, arg):
        self.frame_stack.pop()
        previous_frame = self.frame_stack.pop()
        if DEBUG:
            print(f"previous frame: {previous_frame}")
        self.interaction(previous_frame, None)
        return 1

    # bind re command to reverse function (see cmd.onecmd)
    do_re = do_reverse

def set_trace():
    instance.set_trace(sys._getframe().f_back)
    instance.trace_set = True

instance = rPdb()
instance.start()
