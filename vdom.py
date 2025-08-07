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
    """Special VNode for child components"""
    def __init__(self, render_fn, key=None):
        self.render_fn = render_fn
        self.key = key

def h(tag, props=None, children=None, key=None, memo_key=None):
    if isinstance(children, (str, TextVNode, ElementVNode, PortalVNode, ComponentVNode)):
        children = [children]
    elif children is None:
        children = []
    return ElementVNode(tag, props or {}, children, key, memo_key)

def Portal(host, child, key=None):
    return PortalVNode(host, child, key)

def Component(render_fn, key=None):
    return ComponentVNode(render_fn, key)

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
    return hasattr(host, 'winfo_exists') and callable(host.winfo_exists)

def create_element(vnode, parent):
    if isinstance(vnode, str):
        lbl = ttk.Label(parent, text=vnode)
        lbl.pack()
        # Store vnode reference for patching
        setattr(lbl, '_vnode', TextVNode(vnode))
        return lbl
    
    if isinstance(vnode, TextVNode):
        lbl = ttk.Label(parent, text=vnode.text)
        lbl.pack()
        setattr(lbl, '_vnode', vnode)
        return lbl
    
    if isinstance(vnode, PortalVNode):
        anchor = ttk.Frame(parent)
        anchor.pack()
        setattr(anchor, '_vnode', vnode)
        _mount_portal(vnode)
        return anchor
    
    if isinstance(vnode, ComponentVNode):
        # Create a container for the component
        container = ttk.Frame(parent)
        container.pack()
        
        # Mount the component in the container
        component_vdom = vnode.render_fn()
        child_widget = create_element(component_vdom, container)
        
        setattr(container, '_vnode', vnode)
        setattr(container, '_child_widget', child_widget)
        return container

    cls = TAG_MAP.get(vnode.tag, ttk.Frame)
    w = cls(parent)
    setattr(w, '_vnode', vnode)
    
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
    if isinstance(a, ComponentVNode):
        return a.key is not None and a.key == b.key
    if hasattr(a, 'key') and hasattr(b, 'key'):
        if a.key is not None or b.key is not None:
            return a.key == b.key and getattr(a, 'tag', None) == getattr(b, 'tag', None)
    return getattr(a, 'tag', None) == getattr(b, 'tag', None)

def nodes_equal(a, b):
    if type(a) is not type(b):
        return False
    
    if isinstance(a, str):
        return a == b
    
    if isinstance(a, TextVNode):
        return a.text == b.text
    
    if isinstance(a, PortalVNode):
        return (a.key == b.key and 
                a.host == b.host and 
                nodes_equal(a.child, b.child))
    
    if isinstance(a, ComponentVNode):
        return a.key == b.key and a.render_fn == b.render_fn
    
    if isinstance(a, ElementVNode):
        if a.memo_key and b.memo_key and a.memo_key == b.memo_key:
            return True
        
        if (a.tag != b.tag or 
            a.key != b.key or 
            a.props != b.props or
            len(a.children) != len(b.children)):
            return False
        
        for old_child, new_child in zip(a.children, b.children):
            if not nodes_equal(old_child, new_child):
                return False
        
        return True
    
    return False

def find_widget_for_vnode(parent, vnode, index=None):
    """Find the widget that corresponds to a given vnode"""
    if not parent or not hasattr(parent, 'winfo_children'):
        return None
    
    children = parent.winfo_children()
    
    if index is not None and index < len(children):
        widget = children[index]
        if widget.winfo_exists():
            stored_vnode = getattr(widget, '_vnode', None)
            if stored_vnode and same_node(stored_vnode, vnode):
                return widget
    
    # Fallback: search by key or position
    for i, widget in enumerate(children):
        if not widget.winfo_exists():
            continue
        stored_vnode = getattr(widget, '_vnode', None)
        if stored_vnode and same_node(stored_vnode, vnode):
            return widget
    
    return None

def patch_widget(widget, old_vnode, new_vnode):
    """Patch a single widget with new vnode data"""
    if not widget or not widget.winfo_exists():
        return False
    
    # Update stored vnode reference
    setattr(widget, '_vnode', new_vnode)
    
    # Handle different node types
    if isinstance(new_vnode, (str, TextVNode)):
        new_text = new_vnode.text if isinstance(new_vnode, TextVNode) else new_vnode
        old_text = old_vnode.text if isinstance(old_vnode, TextVNode) else old_vnode
        if new_text != old_text:
            set_prop(widget, "text", new_text)
        return True
    
    if isinstance(new_vnode, PortalVNode):
        _mount_portal(new_vnode)
        return True
    
    if isinstance(new_vnode, ComponentVNode):
        # Re-render component
        component_vdom = new_vnode.render_fn()
        child_widget = getattr(widget, '_child_widget', None)
        
        if child_widget and child_widget.winfo_exists():
            # Patch existing child
            old_child_vnode = getattr(child_widget, '_vnode', None)
            patch_recursive(widget, old_child_vnode, component_vdom, 0)
        else:
            # Create new child
            for child in widget.winfo_children():
                child.destroy()
            new_child = create_element(component_vdom, widget)
            setattr(widget, '_child_widget', new_child)
        return True
    
    if isinstance(new_vnode, ElementVNode):
        # Update properties
        old_props = getattr(old_vnode, 'props', {})
        new_props = new_vnode.props
        
        for key in set(old_props.keys()) | set(new_props.keys()):
            if old_props.get(key) != new_props.get(key):
                set_prop(widget, key, new_props.get(key))
        
        # Handle special cases
        if isinstance(widget, tk.Listbox):
            # Update listbox items
            old_items = []
            new_items = []
            
            for child in getattr(old_vnode, 'children', []):
                if isinstance(child, str):
                    old_items.append(child)
                elif isinstance(child, TextVNode):
                    old_items.append(child.text)
                else:
                    old_items.append(str(child))
            
            for child in new_vnode.children:
                if isinstance(child, str):
                    new_items.append(child)
                elif isinstance(child, TextVNode):
                    new_items.append(child.text)
                else:
                    new_items.append(str(child))
            
            if old_items != new_items:
                widget.delete(0, tk.END)
                for item in new_items:
                    widget.insert(tk.END, item)
        else:
            # Patch children recursively
            old_children = getattr(old_vnode, 'children', [])
            new_children = new_vnode.children
            patch_children(widget, old_children, new_children)
        
        return True
    
    return False

def patch_children(parent_widget, old_children, new_children):
    """Patch child widgets based on old and new child vnodes"""
    if not parent_widget or not parent_widget.winfo_exists():
        return
    
    current_widgets = parent_widget.winfo_children()
    
    # Simple case: same length, try to patch in place
    if len(old_children) == len(new_children):
        can_patch_all = True
        for i, (old_child, new_child) in enumerate(zip(old_children, new_children)):
            if not same_node(old_child, new_child):
                can_patch_all = False
                break
        
        if can_patch_all:
            for i, (old_child, new_child) in enumerate(zip(old_children, new_children)):
                if i < len(current_widgets):
                    widget = current_widgets[i]
                    if widget.winfo_exists():
                        patch_recursive(parent_widget, old_child, new_child, i)
            return
    
    # Complex case: rebuild children
    # For simplicity, destroy all children and recreate
    for widget in current_widgets:
        if widget.winfo_exists():
            widget.destroy()
    
    for child_vnode in new_children:
        create_element(child_vnode, parent_widget)

def patch_recursive(parent, old_vnode, new_vnode, index=0):
    """Recursively patch a vnode at a specific index"""
    if parent is None or not is_real_widget(parent):
        return new_vnode
    
    if not parent.winfo_exists():
        return new_vnode
    
    # If vnodes are equal, no work needed
    if nodes_equal(old_vnode, new_vnode):
        return new_vnode
    
    # Find the target widget
    widget = find_widget_for_vnode(parent, old_vnode or new_vnode, index)
    
    if old_vnode is None:
        # Create new element
        create_element(new_vnode, parent)
        return new_vnode
    
    if widget is None or not widget.winfo_exists():
        # Widget not found, create new one
        create_element(new_vnode, parent)
        return new_vnode
    
    if not same_node(old_vnode, new_vnode):
        # Different node types, replace completely
        widget.destroy()
        create_element(new_vnode, parent)
        return new_vnode
    
    # Patch existing widget
    if patch_widget(widget, old_vnode, new_vnode):
        return new_vnode
    else:
        # Fallback: replace widget
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
    """Enhanced mounting system with component awareness"""
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
            # Real widget mounting
            if not self.host.winfo_exists():
                self.unmounted = True
                return
            
            self.old_vnode = patch_recursive(self.host, self.old_vnode, new_vnode)
        else:
            # Virtual mounting (list-based)
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
    """Enhanced mount_vdom with better host detection"""
    mount = ComponentMount(host, render_fn)
    
    def update():
        mount.update()
    
    def unmount():
        mount.unmount()
    
    return update, unmount