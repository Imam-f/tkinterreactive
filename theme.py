# theme.py
# Two-color ttk theme: White & Light Ink Blue, high-contrast mono font.
# Bigger padded focus ring, and tabs do not change size when selected.

import tkinter as tk
from tkinter import ttk

LIGHT_INK_BLUE = "#2a62a9"
WHITE = "#FFFFFF"

BIG_PAD = 24
BIG_IPAD = 12
FONT_FAMILY = "Cascadia Mono"
BASE_FONT = (FONT_FAMILY, 12)

def create_two_color_theme(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=WHITE)

    style.configure(
        ".",
        background=WHITE,
        foreground=LIGHT_INK_BLUE,
        fieldbackground=WHITE,
        bordercolor=LIGHT_INK_BLUE,
        focuscolor=LIGHT_INK_BLUE,
        lightcolor=WHITE,
        darkcolor=LIGHT_INK_BLUE,
        troughcolor=WHITE,
        padding=BIG_PAD // 2,
        font=BASE_FONT,
    )

    style.configure("TFrame", background=WHITE, borderwidth=0, relief="flat")

    style.configure(
        "TLabel",
        background=WHITE,
        foreground=LIGHT_INK_BLUE,
        padding=(0, BIG_PAD // 2),
        font=(FONT_FAMILY, 12, "bold"),
    )

    style.configure(
        "TButton",
        background=WHITE,
        foreground=LIGHT_INK_BLUE,
        borderwidth=2,
        relief="ridge",
        padding=(BIG_PAD, BIG_IPAD),
        focusthickness=3,
        focuscolor=LIGHT_INK_BLUE,
        font=(FONT_FAMILY, 12, "bold"),
    )
    style.map(
        "TButton",
        background=[("active", WHITE), ("pressed", WHITE)],
        foreground=[("disabled", LIGHT_INK_BLUE)],
        bordercolor=[("focus", LIGHT_INK_BLUE), ("!focus", LIGHT_INK_BLUE)],
        relief=[("pressed", "sunken"), ("!pressed", "ridge")],
        padding=[
            ("focus", (BIG_PAD + 6, BIG_IPAD + 4)),
            ("!focus", (BIG_PAD, BIG_IPAD)),
        ],
    )

    style.configure(
        "TEntry",
        foreground=LIGHT_INK_BLUE,
        fieldbackground=WHITE,
        insertcolor=LIGHT_INK_BLUE,
        borderwidth=2,
        relief="solid",
        padding=(BIG_PAD, BIG_IPAD),
        font=(FONT_FAMILY, 12),
    )
    style.map(
        "TEntry",
        padding=[
            ("focus", (BIG_PAD + 6, BIG_IPAD + 4)),
            ("!focus", (BIG_PAD, BIG_IPAD)),
        ],
        bordercolor=[("focus", LIGHT_INK_BLUE)],
    )

    style.configure(
        "TCombobox",
        foreground=LIGHT_INK_BLUE,
        fieldbackground=WHITE,
        background=WHITE,
        borderwidth=2,
        relief="solid",
        padding=(BIG_PAD, BIG_IPAD),
        arrowsize=16,
        font=(FONT_FAMILY, 12),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", WHITE)],
        foreground=[("readonly", LIGHT_INK_BLUE)],
        background=[("readonly", WHITE)],
    )

    style.configure(
        "TCheckbutton",
        background=WHITE,
        foreground=LIGHT_INK_BLUE,
        padding=(BIG_PAD, BIG_IPAD),
        font=(FONT_FAMILY, 12),
    )

    style.configure(
        "TRadiobutton",
        background=WHITE,
        foreground=LIGHT_INK_BLUE,
        padding=(BIG_PAD, BIG_IPAD),
        font=(FONT_FAMILY, 12),
    )

    style.configure("TNotebook", background=WHITE, borderwidth=0)

    constant_tab_pad = (BIG_PAD + 12, BIG_IPAD + 8)
    style.configure(
        "TNotebook.Tab",
        background=WHITE,
        foreground=LIGHT_INK_BLUE,
        padding=constant_tab_pad,
        borderwidth=2,
        font=(FONT_FAMILY, 12, "bold"),
        focusthickness=3,
    )

    style.layout(
        "TNotebook.Tab",
        [
            (
                "Notebook.tab",
                {
                    "sticky": "nswe",
                    "children": [
                        (
                            "Notebook.padding",
                            {
                                "sticky": "nswe",
                                "children": [
                                    (
                                        "Notebook.focus",
                                        {
                                            "sticky": "nswe",
                                            "children": [
                                                ("Notebook.label", {"sticky": ""})
                                            ],
                                        },
                                    )
                                ],
                            },
                        )
                    ],
                },
            )
        ],
    )

    style.map(
        "TNotebook.Tab",
        background=[("selected", WHITE)],
        foreground=[("selected", LIGHT_INK_BLUE)],
        bordercolor=[("selected", LIGHT_INK_BLUE), ("!selected", LIGHT_INK_BLUE)],
        padding=[("selected", constant_tab_pad), ("!selected", constant_tab_pad)],
    )

    style.configure(
        "TProgressbar",
        background=LIGHT_INK_BLUE,
        troughcolor=WHITE,
        bordercolor=WHITE,
        lightcolor=LIGHT_INK_BLUE,
        darkcolor=LIGHT_INK_BLUE,
        thickness=20,
    )

    style.configure(
        "TScrollbar",
        background=LIGHT_INK_BLUE,
        troughcolor=WHITE,
        bordercolor=WHITE,
        arrowcolor=WHITE,
        relief="flat",
    )
    style.map(
        "TScrollbar",
        background=[("active", LIGHT_INK_BLUE)],
        arrowcolor=[("active", WHITE)],
    )

    return style

def apply_focus_bigger(style: ttk.Style, root: tk.Tk):
    root.configure(highlightthickness=2, highlightcolor=LIGHT_INK_BLUE)
    style.configure(".", focuscolor=LIGHT_INK_BLUE)

    style.configure("TButton", focusthickness=3)
    style.map(
        "TButton",
        padding=[
            ("focus", (BIG_PAD + 6, BIG_IPAD + 4)),
            ("!focus", (BIG_PAD, BIG_IPAD)),
        ],
        bordercolor=[("focus", LIGHT_INK_BLUE)],
    )

    style.configure("TEntry", borderwidth=2, relief="solid")
    style.map(
        "TEntry",
        padding=[
            ("focus", (BIG_PAD + 6, BIG_IPAD + 4)),
            ("!focus", (BIG_PAD, BIG_IPAD)),
        ],
        bordercolor=[("focus", LIGHT_INK_BLUE)],
    )

    style.configure("TNotebook.Tab", focusthickness=3)
    style.map(
        "TNotebook.Tab",
        bordercolor=[("focus", LIGHT_INK_BLUE)],
        padding=[
            ("focus", (BIG_PAD + 12, BIG_IPAD + 8)),
            ("!focus", (BIG_PAD + 12, BIG_IPAD + 8)),
        ],
    )