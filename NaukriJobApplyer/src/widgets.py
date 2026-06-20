import tkinter as tk

class HoverButton(tk.Button):
    """
    A custom tkinter Button with hover and active (pressed) color states.

    When the mouse enters the button, it shifts to the hover color.
    When clicked (held down), it shifts to a darker active color.
    When disabled, it appears dimmed and non-interactive.
    """

    def __init__(self, master, normal_bg, hover_bg, active_bg,
                 normal_fg="#ffffff", disabled_bg="#21262d", disabled_fg="#484f58",
                 **kwargs):
        super().__init__(master, bg=normal_bg, fg=normal_fg,
                         activebackground=active_bg, activeforeground=normal_fg,
                         relief=tk.FLAT, bd=0, cursor="hand2", **kwargs)

        # Store color states
        self._normal_bg = normal_bg
        self._hover_bg = hover_bg
        self._active_bg = active_bg
        self._normal_fg = normal_fg
        self._disabled_bg = disabled_bg
        self._disabled_fg = disabled_fg

        # Bind mouse events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event):
        """Mouse enters the button area → show hover color."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._hover_bg)

    def _on_leave(self, event):
        """Mouse leaves the button area → restore normal color."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._normal_bg)

    def _on_press(self, event):
        """Mouse button pressed down → show dark active color."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._active_bg)

    def _on_release(self, event):
        """Mouse button released → return to hover (mouse is still over button)."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._hover_bg)

    def set_disabled(self, disabled: bool):
        """Enable or disable the button with proper visual feedback."""
        if disabled:
            self.configure(state=tk.DISABLED, bg=self._disabled_bg,
                           fg=self._disabled_fg, cursor="arrow")
        else:
            self.configure(state=tk.NORMAL, bg=self._normal_bg,
                           fg=self._normal_fg, cursor="hand2")
