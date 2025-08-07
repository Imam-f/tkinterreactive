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
        return False
    if isinstance(a, str):
        return True
    if isinstance(a, TextVNode):
        return True
    if isinstance(a, PortalVNode):
        return a.key is not None and a.key == b.key
    if a.key is not None or b.key is not None:
        return a.key == b.key and a.tag == b.tag
    return a.tag == b.tag

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

def find_child_mapping(old_children, new_children):
    old_keyed = {}
    new_keyed = {}
    
    # Build keyed maps
    for i, child in enumerate(old_children):
        if hasattr(child, 'key') and child.key is not None:
            old_keyed[child.key] = (i, child)
    
    for i, child in enumerate(new_children):
        if hasattr(child, 'key') and child.key is not None:
            new_keyed[child.key] = (i, child)
    
    moves = []
    creates = []
    deletes = []
    patches = []  # New: children that can be patched in place
    used_old_indices = set()
    used_new_indices = set()
    
    # Step 1: Handle exact position matches first (patches in place)
    min_len = min(len(old_children), len(new_children))
    for i in range(min_len):
        old_child = old_children[i]
        new_child = new_children[i]
        
        # Skip if either is keyed (handle them separately)
        old_is_keyed = hasattr(old_child, 'key') and old_child.key is not None
        new_is_keyed = hasattr(new_child, 'key') and new_child.key is not None
        
        if old_is_keyed or new_is_keyed:
            continue
            
        # If they can be the same node, patch in place
        if same_node(old_child, new_child):
            patches.append((i, i))  # (old_index, new_index)
            used_old_indices.add(i)
            used_new_indices.add(i)
    
    # Step 2: Handle keyed elements (moves/creates)
    for new_idx, new_child in enumerate(new_children):
        if new_idx in used_new_indices:
            continue
            
        if hasattr(new_child, 'key') and new_child.key is not None:
            if new_child.key in old_keyed:
                old_idx, old_child = old_keyed[new_child.key]
                if old_idx != new_idx:
                    moves.append((old_idx, new_idx))
                else:
                    patches.append((old_idx, new_idx))  # Same position, patch it
                used_old_indices.add(old_idx)
                used_new_indices.add(new_idx)
            else:
                creates.append((new_idx, new_child))
                used_new_indices.add(new_idx)
    
    # Step 3: Handle remaining unkeyed children
    remaining_old = [(i, child) for i, child in enumerate(old_children) 
                     if i not in used_old_indices]
    remaining_new = [(i, child) for i, child in enumerate(new_children)
                     if i not in used_new_indices]
    
    # Try to match remaining children by same_node
    for new_idx, new_child in remaining_new[:]:  # Copy list since we'll modify it
        best_match = None
        best_old_idx = None
        
        for j, (old_idx, old_child) in enumerate(remaining_old):
            if same_node(old_child, new_child):
                # Prefer matches that are closer to the target position
                if best_match is None:
                    best_match = j
                    best_old_idx = old_idx
                elif abs(old_idx - new_idx) < abs(best_old_idx - new_idx): # type: ignore
                    best_match = j
                    best_old_idx = old_idx
        
        if best_match is not None:
            old_idx = best_old_idx
            if old_idx == new_idx:
                patches.append((old_idx, new_idx))  # Same position, patch it
            else:
                moves.append((old_idx, new_idx))    # Different position, move it
            
            remaining_old.pop(best_match)
            remaining_new.remove((new_idx, new_child))
            used_old_indices.add(old_idx)
            used_new_indices.add(new_idx)
    
    # Step 4: Remaining items are creates and deletes
    for new_idx, new_child in remaining_new:
        creates.append((new_idx, new_child))
    
    for old_idx, _ in remaining_old:
        deletes.append(old_idx)
    
    return moves, creates, deletes, patches

def _mount_portal(vnode):
    host = vnode.host
    if host is None:
        return
    
    rec = MOUNTED.get(host)
    if not rec:
        for c in host.winfo_children():
            c.destroy()
        w = create_element(vnode.child, host)
        MOUNTED[host] = {"widget": w, "vnode": vnode.child}
    else:
        rec["vnode"] = patch(host, rec["vnode"], vnode.child)
        MOUNTED[host] = rec

def patch(parent, old_v, new_v, index=0):
    if parent is None:
        return new_v

    children = parent.winfo_children()
    target = children[index] if index < len(children) else None

    if old_v is None:
        create_element(new_v, parent)
        return new_v

    if nodes_equal(old_v, new_v):
        return new_v

    if (isinstance(old_v, str) or isinstance(new_v, str) or 
        isinstance(old_v, TextVNode) or isinstance(new_v, TextVNode)):
        old_t = old_v.text if isinstance(old_v, TextVNode) else old_v
        new_t = new_v.text if isinstance(new_v, TextVNode) else new_v
        if old_t != new_t:
            if target and target.winfo_exists():
                set_prop(target, "text", new_t)
            else:
                create_element(new_v, parent)
        return new_v

    if isinstance(old_v, PortalVNode) or isinstance(new_v, PortalVNode):
        if not same_node(old_v, new_v):
            if target and target.winfo_exists():
                target.destroy()
            create_element(new_v, parent)
            return new_v
        _mount_portal(new_v)
        return new_v

    if not same_node(old_v, new_v):
        if target and target.winfo_exists():
            target.destroy()
        create_element(new_v, parent)
        return new_v

    if (old_v.memo_key and new_v.memo_key and 
        old_v.memo_key == new_v.memo_key):
        return new_v

    widget = target
    if widget is None or not widget.winfo_exists():
        create_element(new_v, parent)
        return new_v

    old_p, new_p = old_v.props, new_v.props
    if old_p != new_p:
        for k in set(old_p) | set(new_p):
            if old_p.get(k) != new_p.get(k):
                set_prop(widget, k, new_p.get(k))

    if isinstance(widget, tk.Listbox):
        old_items = []
        new_items = []
        
        for c in old_v.children:
            if isinstance(c, str):
                old_items.append(c)
            elif isinstance(c, TextVNode):
                old_items.append(c.text)
            elif hasattr(c, 'children') and c.children:
                first_child = c.children[0] if c.children else ""
                old_items.append(first_child if isinstance(first_child, str) else str(first_child))
            else:
                old_items.append(str(c))
        
        for c in new_v.children:
            if isinstance(c, str):
                new_items.append(c)
            elif isinstance(c, TextVNode):
                new_items.append(c.text)
            elif hasattr(c, 'children') and c.children:
                first_child = c.children[0] if c.children else ""
                new_items.append(first_child if isinstance(first_child, str) else str(first_child))
            else:
                new_items.append(str(c))
        
        if old_items != new_items:
            widget.delete(0, tk.END)
            for item in new_items:
                widget.insert(tk.END, item)
        
        return new_v
    
    old_kids, new_kids = old_v.children, new_v.children
	    
    if not old_kids and not new_kids:
        return new_v

    current_widgets = widget.winfo_children() if widget and widget.winfo_exists() else []

    # Simple case: same structure, just patch each child
    if (len(old_kids) == len(new_kids) and 
        all(same_node(old_kids[i], new_kids[i]) for i in range(len(old_kids)))):
        
        for i in range(len(new_kids)):
            if i < len(current_widgets) and current_widgets[i].winfo_exists():
                patch(widget, old_kids[i], new_kids[i], i)
            else:
                create_element(new_kids[i], widget)
        return new_v

    # Complex case: use the improved mapping
    moves, creates, deletes, patches = find_child_mapping(old_kids, new_kids)
    print("Moves:", moves)
    print("Creates:", creates)
    print("Deletes:", deletes)
    print("Patches:", patches)

    # Step 1: Patch children in place first (most efficient)
    for old_idx, new_idx in patches:
        if old_idx < len(current_widgets) and current_widgets[old_idx].winfo_exists():
            patch(widget, old_kids[old_idx], new_kids[new_idx], old_idx)

    # Step 2: Delete elements that are no longer needed
    for old_idx in sorted(deletes, reverse=True):
        if old_idx < len(current_widgets) and current_widgets[old_idx].winfo_exists():
            current_widgets[old_idx].destroy()

    # Refresh widget list after deletions
    current_widgets = widget.winfo_children() if widget and widget.winfo_exists() else []

    # Step 3: Handle moves (patch and reposition)
    widget_mapping = {}
    for i, w in enumerate(current_widgets):
        if i < len(old_kids):
            widget_mapping[i] = w

    for old_idx, new_idx in moves:
        old_widget = widget_mapping.get(old_idx)
        if old_widget and old_widget.winfo_exists():
            patch(widget, old_kids[old_idx], new_kids[new_idx], old_idx)
            # Note: Actual repositioning happens in the final pack step

    # Step 4: Create new elements
    for new_idx, new_child in creates:
        create_element(new_child, widget)

    # Step 5: Reorder all widgets to match new structure
    final_widgets = widget.winfo_children() if widget and widget.winfo_exists() else []
    for w in final_widgets:
        if w and w.winfo_exists():
            w.pack_forget()
            w.pack()

    return new_v

# vdom.py - Modified mount_vdom function
def mount_vdom(host, render_fn):
    old = [None]
    
    def update():
        new_tree = render_fn()
        
        # Check if host is a child list (for collecting VDOMs)
        if isinstance(host, list):
            # Clear the list and append new VDOM
            host.clear()
            host.append(new_tree)
            return
        
        # Normal rendering to actual widget
        # timer = time.perf_counter()
        old[0] = patch(host, old[0], new_tree)
        # print("patch time = ", time.perf_counter() - timer)
    
    def unmount():
        if isinstance(host, list):
            host.clear()
            old[0] = None
            return
            
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