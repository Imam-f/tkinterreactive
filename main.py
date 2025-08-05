# main.py
import tkinter as tk
from tkinter import ttk

from theme import create_two_color_theme, apply_focus_bigger, BASE_FONT
from multi_view_with_portal import MultiViewWithPortal
from runner import run_component

def main():
    root = tk.Tk()
    root.title("Multi-View + Portal (Tk generator + Themed)")

    try:
        root.option_add("*Font", BASE_FONT)
    except Exception:
        root.option_add("*Font", ("Courier New", 12))

    style = create_two_color_theme(root)
    apply_focus_bigger(style, root)

    app_frame = ttk.Frame(root, padding=24)
    app_frame.pack(fill="both", expand=True)

    external = ttk.Frame(root)
    external.pack(fill="x")

    gen = MultiViewWithPortal({"title": "Multi-View + Portal"}, app_frame, external)
    app = run_component(gen)

    tick = 0
    # fps = 144
    # fps = 10
    fps = 1

    global pump
    def pump():
        nonlocal tick
        evs = app.get_events()
        if evs:
            print("Events:", evs)
        tick += 1
        app.send({"tick": tick//fps})
        # root.after(1000//fps, pump)
        root.after(5000, pump)

    root.after(1000, pump)
    root.minsize(560, 380)
    root.mainloop()

if __name__ == "__main__":
    main()