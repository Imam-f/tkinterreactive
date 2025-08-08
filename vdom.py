# vdom.py - Refactored with better host detection and component awareness
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


class ComponentVNode:
    """Special VNode for declaring a child component's location."""

    def __init__(self, component_factory, key=None, extra_args=None):
        self.component_factory = component_factory
        self.key = key
        self.extra_args = extra_args or []
        # This will be populated by create_element with the container it creates
        self._container_host: ttk.Frame | None = None


def h(tag, props=None, children=None, key=None, memo_key=None):
    if isinstance(
        children, (str, TextVNode, ElementVNode, PortalVNode, ComponentVNode)
    ):
        children = [children]
    elif children is None:
        children = []
    return ElementVNode(tag, props or {}, children, key, memo_key)


def Portal(host, child, key=None):
    return PortalVNode(host, child, key)


def Component(component_factory, key=None, extra_args=None):
    """Factory function to create a ComponentVNode."""
    return ComponentVNode(component_factory, key, extra_args)


TAG_MAP = {
    "div": ttk.Frame,
    "section": ttk.Frame,
    "h2": ttk.Label,
    "span": ttk.Label,
    "button": ttk.Button,
    "input": ttk.Entry,
    "ul": tk.Listbox,
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


def is_real_widget(host):
    """Check if host is a real tkinter widget vs a collection"""
    return hasattr(host, "winfo_exists") and callable(host.winfo_exists)


def create_element(vnode, parent):
    if isinstance(vnode, str):
        lbl = ttk.Label(parent, text=vnode)
        lbl.pack()
        setattr(lbl, "_vnode", TextVNode(vnode))
        return lbl

    if isinstance(vnode, TextVNode):
        lbl = ttk.Label(parent, text=vnode.text)
        lbl.pack()
        setattr(lbl, "_vnode", vnode)
        return lbl

    if isinstance(vnode, PortalVNode):
        anchor = ttk.Frame(parent)
        anchor.pack()
        setattr(anchor, "_vnode", vnode)
        _mount_portal(vnode)
        return anchor

    if isinstance(vnode, ComponentVNode):
        # Create a container for the component. The component itself will be
        # initialized by the parent and will render into this container.
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        setattr(container, "_vnode", vnode)
        # Mark this widget as a managed component boundary
        setattr(container, "_component_managed", True)
        # Store the created container back on the vnode for the parent to find
        vnode._container_host = container
        return container

    cls = TAG_MAP.get(vnode.tag, ttk.Frame)
    w = cls(parent)
    setattr(w, "_vnode", vnode)

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
        return False
    if isinstance(a, str):
        return True
    if isinstance(a, TextVNode):
        return True
    if isinstance(a, PortalVNode):
        return a.key is not None and a.key == b.key
    # Components are the same if their key is the same
    if isinstance(a, ComponentVNode):
        return a.key is not None and a.key == b.key
    if hasattr(a, "key") and hasattr(b, "key"):
        if a.key is not None or b.key is not None:
            return a.key == b.key and getattr(a, "tag", None) == getattr(
                b, "tag", None
            )
    return getattr(a, "tag", None) == getattr(b, "tag", None)


def nodes_equal(a, b):
    if type(a) is not type(b):
        return False

    if isinstance(a, str):
        return a == b

    if isinstance(a, TextVNode):
        return a.text == b.text

    if isinstance(a, PortalVNode):
        return (
            a.key == b.key
            and a.host == b.host
            and nodes_equal(a.child, b.child)
        )

    if isinstance(a, ComponentVNode):
        # Equality is based on key and factory. If these are the same,
        # we assume the component can handle its own updates.
        return a.key == b.key and a.component_factory == b.component_factory

    if isinstance(a, ElementVNode):
        if a.memo_key and b.memo_key and a.memo_key == b.memo_key:
            return True

        if (
            a.tag != b.tag
            or a.key != b.key
            or a.props != b.props
            or len(a.children) != len(b.children)
        ):
            return False

        for old_child, new_child in zip(a.children, b.children):
            if not nodes_equal(old_child, new_child):
                return False

        return True

    return False


def find_widget_for_vnode(parent, vnode, index=None):
    if not parent or not hasattr(parent, "winfo_children"):
        return None

    children = parent.winfo_children()

    if index is not None and index < len(children):
        widget = children[index]
        if widget.winfo_exists():
            stored_vnode = getattr(widget, "_vnode", None)
            if stored_vnode and same_node(stored_vnode, vnode):
                return widget

    for i, widget in enumerate(children):
        if not widget.winfo_exists():
            continue
        stored_vnode = getattr(widget, "_vnode", None)
        if stored_vnode and same_node(stored_vnode, vnode):
            return widget

    return None


def patch_widget(widget, old_vnode, new_vnode):
    if not widget or not widget.winfo_exists():
        return False

    setattr(widget, "_vnode", new_vnode)

    if isinstance(new_vnode, (str, TextVNode)):
        new_text = (
            new_vnode.text if isinstance(new_vnode, TextVNode) else new_vnode
        )
        old_text = (
            old_vnode.text if isinstance(old_vnode, TextVNode) else old_vnode
        )
        if new_text != old_text:
            set_prop(widget, "text", new_text)
        return True

    if isinstance(new_vnode, PortalVNode):
        _mount_portal(new_vnode)
        return True

    if isinstance(new_vnode, ComponentVNode):
        # The container widget itself doesn't need patching. The component
        # inside it manages its own updates. We just need to ensure the
        # vnode reference is updated.
        new_vnode._container_host = widget
        return True

    if isinstance(new_vnode, ElementVNode):
        old_props = getattr(old_vnode, "props", {})
        new_props = new_vnode.props

        for key in set(old_props.keys()) | set(new_props.keys()):
            if old_props.get(key) != new_props.get(key):
                set_prop(widget, key, new_props.get(key))

        if isinstance(widget, tk.Listbox):
            old_items = [
                (
                    c.text
                    if isinstance(c, TextVNode)
                    else c if isinstance(c, str) else str(c)
                )
                for c in getattr(old_vnode, "children", [])
            ]
            new_items = [
                (
                    c.text
                    if isinstance(c, TextVNode)
                    else c if isinstance(c, str) else str(c)
                )
                for c in new_vnode.children
            ]

            if old_items != new_items:
                widget.delete(0, tk.END)
                for item in new_items:
                    widget.insert(tk.END, item)
        else:
            patch_children(
                widget,
                getattr(old_vnode, "children", []),
                new_vnode.children,
            )

        return True

    return False


def patch_children(parent_widget, old_children, new_children):
    if not parent_widget or not parent_widget.winfo_exists():
        return

    current_widgets = parent_widget.winfo_children()

    if len(old_children) == len(new_children):
        can_patch_all = all(
            same_node(old, new) for old, new in zip(old_children, new_children)
        )
        if can_patch_all:
            for i, (old_child, new_child) in enumerate(
                zip(old_children, new_children)
            ):
                if i < len(current_widgets):
                    widget = current_widgets[i]
                    if widget.winfo_exists():
                        patch_recursive(parent_widget, old_child, new_child, i)
            return

    # For simplicity in this context, destroy and recreate children.
    # A more advanced implementation would use key-based reconciliation.
    for widget in current_widgets:
        if widget.winfo_exists():
            widget.destroy()

    for child_vnode in new_children:
        create_element(child_vnode, parent_widget)


def patch_recursive(parent, old_vnode, new_vnode, index=0):
    if parent is None or not is_real_widget(parent):
        return new_vnode

    if not parent.winfo_exists():
        return new_vnode

    if nodes_equal(old_vnode, new_vnode):
        return new_vnode

    widget = find_widget_for_vnode(parent, old_vnode or new_vnode, index)

    if new_vnode is None:
        if widget and widget.winfo_exists():
            widget.destroy()
        return None

    if old_vnode is None:
        create_element(new_vnode, parent)
        return new_vnode

    if not same_node(old_vnode, new_vnode):
        if widget and widget.winfo_exists():
            widget.destroy()
        create_element(new_vnode, parent)
        return new_vnode

    if patch_widget(widget, old_vnode, new_vnode):
        return new_vnode
    else:
        if widget and widget.winfo_exists():
            widget.destroy()
        create_element(new_vnode, parent)
        return new_vnode


def _mount_portal(vnode):
    host = vnode.host
    if host is None or not is_real_widget(host):
        return

    rec = MOUNTED.get(host)
    if not rec:
        for c in host.winfo_children():
            c.destroy()
        w = create_element(vnode.child, host)
        MOUNTED[host] = {"widget": w, "vnode": vnode.child}
    else:
        old_vnode = rec["vnode"]
        rec["vnode"] = patch_recursive(host, old_vnode, vnode.child)
        MOUNTED[host] = rec


class ComponentMount:
    def __init__(self, host, render_fn):
        self.host = host
        self.render_fn = render_fn
        self.old_vnode = None
        self.is_real_host = is_real_widget(host)
        self.unmounted = False

    def update(self):
        if self.unmounted:
            return

        try:
            new_vnode = self.render_fn()
        except Exception as e:
            print(f"Error in render function: {e}")
            return

        if self.is_real_host:
            if not self.host.winfo_exists():
                self.unmounted = True
                return

            self.old_vnode = patch_recursive(self.host, self.old_vnode, new_vnode)
        else:
            if isinstance(self.host, list):
                self.host.clear()
                self.host.append(new_vnode)
                self.old_vnode = new_vnode

    def unmount(self):
        if self.unmounted:
            return

        self.unmounted = True

        if self.is_real_host:
            try:
                if self.host.winfo_exists():
                    for child in self.host.winfo_children():
                        child.destroy()
            except Exception:
                pass
        else:
            if isinstance(self.host, list):
                self.host.clear()

        self.old_vnode = None


def mount_vdom(host, render_fn):
    mount = ComponentMount(host, render_fn)

    def update():
        mount.update()

    def unmount():
        mount.unmount()

    return update, unmount