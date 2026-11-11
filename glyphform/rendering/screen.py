"""ANSI terminal output and interactive terminal input handling."""
import os
import re
import shutil
import sys
import numpy as np

GLYPHS = " .,:;+*xX#%@"
MOUSE_RE = re.compile(r"\x1b\[<(\d+);(\d+);(\d+)([Mm])")

def enable_vt():
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        m = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(m)):
            k.SetConsoleMode(h, m.value | 0x0001 | 0x0004)
            return
    except Exception:
        pass
    os.system("")


def detect_truecolor():
    e = os.environ
    if e.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return True
    if e.get("WT_SESSION") or e.get("TERM_PROGRAM") in ("vscode", "iTerm.app", "WezTerm", "ghostty"):
        return True
    return os.name == "nt"


def to256(r, g, b):
    return 16 + 36 * int(round(r / 51)) + 6 * int(round(g / 51)) + int(round(b / 51))


class Screen:
    def __init__(self):
        self.truecolor = detect_truecolor()
        self.opened = False
        self.tty = None
        self.fd = None
        self.msvcrt = None
        self.win_old = None
        self.buf = ""
        self.W = self.H = 0
        self.size = (0, 0)
        self.prev_ch = self.prev_col = None

    def open(self):
        self.opened = True
        enable_vt()
        try:
            if os.name == "nt":
                import msvcrt
                self.msvcrt = msvcrt
                self.set_windows_input()
            else:
                import termios
                fd = sys.stdin.fileno()
                if os.isatty(fd):
                    self.tty = termios.tcgetattr(fd)
                    new = termios.tcgetattr(fd)
                    new[3] &= ~(termios.ECHO | termios.ICANON)
                    new[6][termios.VMIN] = 0
                    new[6][termios.VTIME] = 0
                    termios.tcsetattr(fd, termios.TCSADRAIN, new)
                    self.fd = fd
        except Exception:
            pass
        bg = "\x1b[48;2;0;0;0m" if self.truecolor else "\x1b[48;5;16m"
        self.write("\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[?1003h\x1b[?1006h" + bg + "\x1b[2J\x1b[H")

    def close(self):
        if not self.opened:
            return
        self.opened = False
        self.write("\x1b[?1003l\x1b[?1006l\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l")
        if self.win_old is not None:
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleMode(self.win_old[0], self.win_old[1])
            except Exception:
                pass
        if self.tty is not None:
            try:
                import termios
                termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.tty)
            except Exception:
                pass

    @staticmethod
    def write(s):
        try:
            sys.stdout.write(s)
            sys.stdout.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass

    def set_windows_input(self):
        """Ask the Windows console to send mouse and keys as ANSI sequences."""
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.GetStdHandle.restype = ctypes.c_void_p
            k.GetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            k.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            h = k.GetStdHandle(-10)
            m = ctypes.c_uint32()
            if k.GetConsoleMode(h, ctypes.byref(m)):
                self.win_old = (h, m.value)
                # virtual terminal input, processed input (Ctrl+C), extended flags
                k.SetConsoleMode(h, 0x0200 | 0x0001 | 0x0080)
        except Exception:
            pass

    def read_raw(self):
        s = ""
        try:
            if self.msvcrt is not None:
                while self.msvcrt.kbhit():
                    s += self.msvcrt.getwch()
            elif self.fd is not None:
                import select
                while select.select([self.fd], [], [], 0)[0]:
                    chunk = os.read(self.fd, 4096)
                    if not chunk:
                        break
                    s += chunk.decode("utf-8", "ignore")
        except Exception:
            pass
        return s

    def poll(self):
        """Read pending input. Returns a dict: quit, step, pos (row, col), left."""
        ev = {"quit": False, "step": 0, "pos": None, "left": None}
        data = self.buf + self.read_raw()
        self.buf = ""
        if not data:
            return ev
        part = re.search(r"\x1b(\[[<0-9;]*)?$", data)
        if part:                                   # keep an unfinished sequence
            self.buf = data[part.start():]
            data = data[:part.start()]
        for m in MOUSE_RE.finditer(data):
            b, x, y, kind = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
            btn, motion, wheel = b & 3, b & 32, b & 64
            if wheel:
                if kind == "M":
                    ev["step"] += -1 if btn == 0 else 1
                continue
            ev["pos"] = (y - 1, x - 1)
            if motion:
                ev["left"] = (btn == 0)
            elif kind == "M":
                if btn == 0:
                    ev["left"] = True
                elif btn == 2:
                    ev["step"] += 1
            elif btn == 0:
                ev["left"] = False
        rest = MOUSE_RE.sub("", data)
        ev["step"] += rest.count("\x1b[C") - rest.count("\x1b[D")
        rest = re.sub(r"\x1b\[[0-9;]*[A-Za-z~]", "", rest)
        for ch in rest:
            if ch in "qQ":
                ev["quit"] = True
            elif ch in "nN ":
                ev["step"] += 1
            elif ch in "pP":
                ev["step"] -= 1
        return ev

    @staticmethod
    def term_size():
        try:
            s = os.get_terminal_size(sys.stdout.fileno())
        except (OSError, ValueError):
            s = shutil.get_terminal_size((100, 30))
        return s.columns, s.lines

    def resize(self, cols, rows):
        self.size = (cols, rows)
        self.W, self.H = cols, rows
        self.prev_ch = np.zeros((rows, cols), np.uint8)
        self.prev_col = np.zeros((rows, cols), np.uint8)
        self.write("\x1b[2J")

    def present(self, ch, col, ramp, force):
        if self.truecolor:
            sgr = [""] + ["\x1b[38;2;%d;%d;%dm" % (r, g, b) for r, g, b in ramp.round().astype(int).tolist()]
        else:
            sgr = [""] + ["\x1b[38;5;%dm" % to256(r, g, b) for r, g, b in ramp.round().astype(int).tolist()]
        if force:
            self.prev_col[:] = 255
        changed = (ch != self.prev_ch) | ((ch != 0) & (col != self.prev_col))
        changed[-1, -1] = False
        ri, ci = np.nonzero(changed)
        if ri.size == 0:
            return
        gl = ch[ri, ci].tolist()
        co = col[ri, ci].tolist()
        parts = []
        last_r = last_c = -5
        cur = -1
        for r, c, g, k in zip(ri.tolist(), ci.tolist(), gl, co):
            if r != last_r or c != last_c + 1:
                parts.append("\x1b[%d;%dH" % (r + 1, c + 1))
            if g and k != cur:
                parts.append(sgr[k])
                cur = k
            parts.append(GLYPHS[g])
            last_r, last_c = r, c
        self.write("".join(parts))
        np.copyto(self.prev_ch, ch)
        np.copyto(self.prev_col, col)
