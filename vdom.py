# vdom.py
import tkinter as tk
from tkinter import ttk
from weakref import WeakKeyDictionary

MOUNTED = WeakKeyDictionary()

class TextVNode:
    def __init__(self, text):
        self.text = text

class ElementVNode:
    def __init__(self, tag, props=None, children=None, key=None, memo_key=None):
        self.tag = tag
        self.props = props or {}
        self.children = children or []
        self.key = key
        self.memo_key = memo_key

class PortalVNode:
    def __init__(self, host, child, key=None):
        self.host = host
        self.child = child
        self.key = key

def h(tag, props=None, children=None, key=None, memo_key=None):
    if isinstance(children, (str, TextVNode, ElementVNode, PortalVNode)):
        children = [children]
    elif children is None:
        children = []
    return ElementVNode(tag, props or {}, children, key, memo_key)

def Portal(host, child, key=None):
    return PortalVNode(host, child, key)

TAG_MAP = {
    "div": ttk.Frame,
    "section": ttk.Frame,
    "h2": ttk.Label,
    "span": ttk.Label,
    "button": ttk.Button,
    "input": ttk.Entry,
    "ul": tk.Listbox,  # ttk has no listbox
}

def set_prop(w, name, value):
    if name == "text":
        try:
            w.config(text=value or "")
        except Exception:
            pass
    elif name == "command":
        try:
            w.config(command=value)
        except Exception:
            pass
    elif name == "on_input":
        try:
            w.bind("<KeyRelease>", value)
        except Exception:
            pass
    elif name == "value" and isinstance(w, ttk.Entry):
        w.delete(0, tk.END)
        w.insert(0, value or "")
    else:
        try:
            w.config({name: value})
        except Exception:
            pass

def create_element(vnode, parent):
    if isinstance(vnode, str):
        lbl = ttk.Label(parent, text=vnode)
        lbl.pack()
        return lbl
    if isinstance(vnode, TextVNode):
        lbl = ttk.Label(parent, text=vnode.text)
        lbl.pack()
        return lbl
    if isinstance(vnode, PortalVNode):
        anchor = ttk.Frame(parent)
        anchor.pack()
        _mount_portal(vnode)
        return anchor

    cls = TAG_MAP.get(vnode.tag, ttk.Frame)
    w = cls(parent)
    if vnode.tag == "h2":
        try:
            w.config(font=("Cascadia Mono", 16, "bold"))
        except Exception:
            pass
    for k, v in vnode.props.items():
        set_prop(w, k, v)
    w.pack()

    if isinstance(w, tk.Listbox):
        for c in vnode.children:
            text = c if isinstance(c, str) else getattr(c, "text", str(c))
            w.insert(tk.END, text)
    else:
        for c in vnode.children:
            create_element(c, w)
    return w

def same_node(a, b):
    if type(a) is not type(b):
    # if type(a) is type(b):
        return False
    if isinstance(a, str):
        return True
    if isinstance(a, PortalVNode):
        # print("same portal", a.key, b.key)
        return a.key is not None and a.key == b.key
    if a.key is not None or b.key is not None:
        return a.key == b.key and a.tag == b.tag
    return a.tag == b.tag

def _mount_portal(vnode):
    host = vnode.host
    if host is None:
        return  # host missing, nothing to mount into
    # Clear host (portal host is separate from the main tree)
    for c in host.winfo_children():
        c.destroy()
    rec = MOUNTED.get(host)
    if not rec:
        w = create_element(vnode.child, host)
        MOUNTED[host] = {"widget": w, "vnode": vnode.child}
    else:
        # Always patch into the portal host (valid widget)
        rec["vnode"] = patch(host, rec["vnode"], vnode.child)
        MOUNTED[host] = rec

def patch(parent, old_v, new_v, index=0):
    # Parent may be missing (e.g., previously destroyed); bail out safely.
    if parent is None:
        return new_v

    children = parent.winfo_children()
    target = children[index] if index < len(children) else None

    # Mount new
    if old_v is None:
        create_element(new_v, parent)
        return new_v

    # Text nodes
    if (
        isinstance(old_v, str)
        or isinstance(new_v, str)
        or isinstance(old_v, TextVNode)
        or isinstance(new_v, TextVNode)
    ):
        old_t = old_v.text if isinstance(old_v, TextVNode) else old_v
        new_t = new_v.text if isinstance(new_v, TextVNode) else new_v
        if old_t != new_t:
            if target and target.winfo_exists():
                target.destroy()
            create_element(new_v, parent)
        return new_v

    # Portals
    if isinstance(old_v, PortalVNode) or isinstance(new_v, PortalVNode):
        if not same_node(old_v, new_v):
            if target and target.winfo_exists():
                target.destroy()
            return create_element(new_v, parent)
        _mount_portal(new_v)
        return new_v

    # Different element → replace
    if not same_node(old_v, new_v):
        if target and target.winfo_exists():
            target.destroy()
        create_element(new_v, parent)
        return new_v

    # Memo skip
    if old_v.memo_key and new_v.memo_key and old_v.memo_key == new_v.memo_key:
        return new_v

    widget = target
    # If target widget vanished for any reason, just recreate subtree
    if widget is None or not widget.winfo_exists():
        create_element(new_v, parent)
        return new_v

    # Update props
    old_p, new_p = old_v.props, new_v.props
    for k in set(old_p) | set(new_p):
        if old_p.get(k) != new_p.get(k):
            set_prop(widget, k, new_p.get(k))

    # Listbox: redraw items wholesale
    if isinstance(widget, tk.Listbox):
        widget.delete(0, tk.END)
        for c in new_v.children:
            text = c if isinstance(c, str) else getattr(c, "text", str(c))
            # Extract text from VNode properly
            if isinstance(c, str):
                text = c
            elif isinstance(c, TextVNode):
                text = c.text
            elif hasattr(c, 'children') and c.children:
                # If it's an element with text children, extract the first text child
                first_child = c.children[0] if c.children else ""
                text = first_child if isinstance(first_child, str) else str(first_child)
            else:
                text = str(c)
            widget.insert(tk.END, text)
        return new_v

    # Fixed child reconciliation
    old_kids, new_kids = old_v.children, new_v.children
    
    # First, clear all existing children if the structure changed significantly
    current_widgets = widget.winfo_children() if widget and widget.winfo_exists() else []
    
    # Check if we need a full rebuild (different child count or major structure change)
    needs_rebuild = len(old_kids) != len(new_kids)
    if not needs_rebuild:
        # Check if any child types changed
        for i in range(len(old_kids)):
            if not same_node(old_kids[i], new_kids[i]):
                needs_rebuild = True
                break
    
    if needs_rebuild:
        # Clear all children and rebuild
        for w in current_widgets:
            if w and w.winfo_exists():
                w.destroy()
        # Create all new children
        for new_child in new_kids:
            create_element(new_child, widget)
    else:
        # Structure is the same, patch children in place
        for i in range(len(new_kids)):
            patch(widget, old_kids[i], new_kids[i], i)

    return new_v

def mount_vdom(host, render_fn):
    old = [None]
    def update():
        new_tree = render_fn()
        old[0] = patch(host, old[0], new_tree)
    def unmount():
        try:
            is_n_closed = host.winfo_exists()
        except Exception:
            is_n_closed = False
        if not is_n_closed:
            old[0] = None
            return
        for c in host.winfo_children():
            c.destroy()
        old[0] = None
    return update, unmount