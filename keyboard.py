import sys
import tkinter as tk
from tkinter import messagebox

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    PUL = ctypes.POINTER(ctypes.c_ulong)

    class KeyBdInput(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort),
            ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", PUL),
        ]

    class HardwareInput(ctypes.Structure):
        _fields_ = [
            ("uMsg", ctypes.c_ulong),
            ("wParamL", ctypes.c_short),
            ("wParamH", ctypes.c_ushort),
        ]

    class MouseInput(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", PUL),
        ]

    class InputUnion(ctypes.Union):
        _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", InputUnion)]

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004

    VK_BACK = 0x08
    VK_TAB = 0x09
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_SPACE = 0x20
    VK_SHIFT = 0x10

    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080

    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010

    def _send_input(struct: "Input"):
        user32.SendInput(1, ctypes.pointer(struct), ctypes.sizeof(struct))

    def send_unicode_char(char: str):
        extra = ctypes.c_ulong(0)
        down = Input()
        down.type = INPUT_KEYBOARD
        down.ii.ki = KeyBdInput(0, ord(char), KEYEVENTF_UNICODE, 0, ctypes.pointer(extra))

        up = Input()
        up.type = INPUT_KEYBOARD
        up.ii.ki = KeyBdInput(0, ord(char), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))

        _send_input(down)
        _send_input(up)

    def send_vk(vk_code: int):
        extra = ctypes.c_ulong(0)
        down = Input()
        down.type = INPUT_KEYBOARD
        down.ii.ki = KeyBdInput(vk_code, 0, 0, 0, ctypes.pointer(extra))

        up = Input()
        up.type = INPUT_KEYBOARD
        up.ii.ki = KeyBdInput(vk_code, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))

        _send_input(down)
        _send_input(up)

    def make_window_noactivate_and_topmost(root: tk.Tk):
        root.update_idletasks()
        hwnd = user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

        user32.SetWindowPos(
            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
        return hwnd

else:
    def send_unicode_char(char: str):
        pass

    def send_vk(vk_code: int):
        pass

    def make_window_noactivate_and_topmost(root):
        return None


EN_ROWS = [
    list("1234567890"),
    list("qwertyuiop"),
    list("asdfghjkl") + ["'"],
    list("zxcvbnm"),
]

RU_ROWS = [
    list("1234567890"),
    list("йцукенгшщзх"),
    list("фывапролдж") + ["э"],
    list("ячсмитьбю"),
]


class VirtualKeyboard:
    KEY_BG = "#1a1a1a"
    KEY_FG = "#ffffff"
    KEY_ACTIVE_BG = "#330000"
    SPECIAL_BG = "#262626"
    TOGGLE_ON_BG = "#cc0000"
    ROOT_BG = "#0d0d0d"

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.root.overrideredirect(True)
        self.root.configure(bg=self.ROOT_BG)
        self.root.attributes("-topmost", True)

        self.caps_on = False
        self.shift_once = False
        self.lang = "EN"

        self.key_buttons = []

        self._build_titlebar()
        self._build_keyboard()

        self.root.update_idletasks()

        if IS_WINDOWS:
            make_window_noactivate_and_topmost(self.root)
        else:
            messagebox.showwarning("Uyarı", "Bu program sadece Windows'ta tam çalışır.")

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        x = sw - w - 20
        y = sh - h - 60
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.root.deiconify()

        if IS_WINDOWS:
            self.root.after(50, lambda: make_window_noactivate_and_topmost(self.root))

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg="#141414", height=28)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        title = tk.Label(bar, text="poncik", bg="#141414", fg="#ff4d4d",
                         font=("Segoe UI", 9, "bold"))
        title.pack(side="left", padx=8)

        close_btn = tk.Button(bar, text="X", bg="#141414", fg="#cccccc",
                              bd=0, activebackground="#cc0000", activeforeground="#ffffff",
                              command=self.root.destroy, width=3)
        close_btn.pack(side="right")

        for widget in (bar, title):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<B1-Motion>", self._do_move)

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_move(self, event):
        x = self.root.winfo_pointerx() - self._drag_x
        y = self.root.winfo_pointery() - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _build_keyboard(self):
        self.kb_frame = tk.Frame(self.root, bg=self.ROOT_BG, padx=6, pady=6)
        self.kb_frame.pack()

        self._render_rows()
        self._render_bottom_row()

    def _render_rows(self):
        for child in getattr(self, "_row_frames", []):
            child.destroy()
        self._row_frames = []
        self.key_buttons = []

        rows = EN_ROWS if self.lang == "EN" else RU_ROWS

        top = tk.Frame(self.kb_frame, bg=self.ROOT_BG)
        top.pack(fill="x", pady=2)
        self._row_frames.append(top)

        esc_btn = tk.Button(top, text="ESC", width=6, bg=self.SPECIAL_BG, fg=self.KEY_FG,
                            activebackground=self.KEY_ACTIVE_BG, bd=0,
                            command=self.on_esc)
        esc_btn.pack(side="left", padx=2, pady=2)

        for ch in rows[0]:
            self._add_char_button(top, ch)

        bksp_btn = tk.Button(top, text="Backspace", width=10, bg=self.SPECIAL_BG, fg=self.KEY_FG,
                            activebackground=self.KEY_ACTIVE_BG, bd=0,
                            command=self.on_backspace)
        bksp_btn.pack(side="left", padx=2, pady=2)

        for row_idx in (1, 2):
            row_frame = tk.Frame(self.kb_frame, bg=self.ROOT_BG)
            row_frame.pack(fill="x", pady=2)
            self._row_frames.append(row_frame)

            if row_idx == 2:
                self.caps_btn = tk.Button(
                    row_frame, text="Caps Lock", width=9,
                    bg=self.TOGGLE_ON_BG if self.caps_on else self.SPECIAL_BG,
                    fg=self.KEY_FG, activebackground=self.KEY_ACTIVE_BG, bd=0,
                    command=self.on_capslock,
                )
                self.caps_btn.pack(side="left", padx=2, pady=2)

            for ch in rows[row_idx]:
                self._add_char_button(row_frame, ch)

            if row_idx == 2:
                enter_btn = tk.Button(row_frame, text="Enter", width=9, bg=self.SPECIAL_BG,
                                     fg=self.KEY_FG, activebackground=self.KEY_ACTIVE_BG,
                                     bd=0, command=self.on_enter)
                enter_btn.pack(side="left", padx=2, pady=2)

        last_row = tk.Frame(self.kb_frame, bg=self.ROOT_BG)
        last_row.pack(fill="x", pady=2)
        self._row_frames.append(last_row)

        self.shift_btn = tk.Button(last_row, text="Shift", width=9, bg=self.SPECIAL_BG,
                                    fg=self.KEY_FG, activebackground=self.KEY_ACTIVE_BG,
                                    bd=0, command=self.on_shift)
        self.shift_btn.pack(side="left", padx=2, pady=2)

        for ch in rows[3]:
            self._add_char_button(last_row, ch)

        self._refresh_key_labels()

    def _render_bottom_row(self):
        bottom = tk.Frame(self.kb_frame, bg=self.ROOT_BG)
        bottom.pack(fill="x", pady=2)

        lang_btn = tk.Button(bottom, text="EN / RU", width=9, bg=self.SPECIAL_BG,
                            fg=self.KEY_FG, activebackground=self.KEY_ACTIVE_BG,
                            bd=0, command=self.on_lang_switch)
        lang_btn.pack(side="left", padx=2, pady=2)

        space_btn = tk.Button(bottom, text="SPACE", width=34, bg=self.SPECIAL_BG,
                              fg=self.KEY_FG, activebackground=self.KEY_ACTIVE_BG,
                              bd=0, command=self.on_space)
        space_btn.pack(side="left", padx=2, pady=2, fill="x", expand=True)

    def _add_char_button(self, parent, ch):
        btn = tk.Button(parent, text=ch, width=4, bg=self.KEY_BG, fg=self.KEY_FG,
                        activebackground=self.KEY_ACTIVE_BG, bd=0,
                        command=lambda c=ch: self.on_char_click(c))
        btn.pack(side="left", padx=2, pady=2)
        self.key_buttons.append((btn, ch))

    def _effective_case(self, base_char: str) -> str:
        if base_char.isalpha():
            want_upper = self.caps_on ^ self.shift_once
            return base_char.upper() if want_upper else base_char.lower()
        return base_char

    def on_char_click(self, base_char: str):
        final_char = self._effective_case(base_char)
        send_unicode_char(final_char)
        if self.shift_once:
            self.shift_once = False
            self._refresh_key_labels()
            self._update_shift_visual()

    def on_backspace(self):
        if IS_WINDOWS:
            send_vk(VK_BACK)

    def on_enter(self):
        if IS_WINDOWS:
            send_vk(VK_RETURN)

    def on_esc(self):
        if IS_WINDOWS:
            send_vk(VK_ESCAPE)

    def on_space(self):
        if IS_WINDOWS:
            send_vk(VK_SPACE)

    def on_capslock(self):
        self.caps_on = not self.caps_on
        self.caps_btn.configure(bg=self.TOGGLE_ON_BG if self.caps_on else self.SPECIAL_BG)
        self._refresh_key_labels()

    def on_shift(self):
        self.shift_once = not self.shift_once
        self._update_shift_visual()
        self._refresh_key_labels()

    def _update_shift_visual(self):
        self.shift_btn.configure(bg=self.TOGGLE_ON_BG if self.shift_once else self.SPECIAL_BG)

    def on_lang_switch(self):
        self.lang = "RU" if self.lang == "EN" else "EN"
        self._render_rows()

    def _refresh_key_labels(self):
        for btn, base_char in self.key_buttons:
            btn.configure(text=self._effective_case(base_char))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = VirtualKeyboard()
    app.run()