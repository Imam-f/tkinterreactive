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
    """Check if two nodes represent the same logical element"""
    if type(a) is not type(b):
        return False
    if isinstance(a, str):
        return True  # All text nodes are considered "same" for positioning
    if isinstance(a, TextVNode):
        return True  # All text nodes are considered "same" for positioning
    if isinstance(a, PortalVNode):
        return a.key is not None and a.key == b.key
    if a.key is not None or b.key is not None:
        return a.key == b.key and a.tag == b.tag
    return a.tag == b.tag

def nodes_equal(a, b):
    """Check if two nodes are completely equal (no update needed)"""
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
        # Check memo key first for quick bailout
        if a.memo_key and b.memo_key and a.memo_key == b.memo_key:
            return True
        
        # Check basic properties
        if (a.tag != b.tag or 
            a.key != b.key or 
            a.props != b.props or
            len(a.children) != len(b.children)):
            return False
        
        # Check all children
        for old_child, new_child in zip(a.children, b.children):
            if not nodes_equal(old_child, new_child):
                return False
        
        return True
    
    return False

def find_child_mapping(old_children, new_children):
    """
    Create a mapping of how old children should be rearranged to match new children.
    Returns (moves, creates, deletes) where:
    - moves: list of (old_index, new_index) for children that moved
    - creates: list of (new_index, new_vnode) for new children
    - deletes: list of old_index for children to delete
    """
    old_keyed = {}  # key -> (index, vnode)
    old_by_index = {}  # index -> vnode
    new_keyed = {}  # key -> (index, vnode)
    new_by_index = {}  # index -> vnode
    
    # Build lookup tables
    for i, child in enumerate(old_children):
        old_by_index[i] = child
        if hasattr(child, 'key') and child.key is not None:
            old_keyed[child.key] = (i, child)
    
    for i, child in enumerate(new_children):
        new_by_index[i] = child
        if hasattr(child, 'key') and child.key is not None:
            new_keyed[child.key] = (i, child)
    
    moves = []
    creates = []
    deletes = []
    used_old_indices = set()
    
    # First pass: handle keyed children
    for new_idx, new_child in enumerate(new_children):
        if hasattr(new_child, 'key') and new_child.key is not None:
            if new_child.key in old_keyed:
                old_idx, old_child = old_keyed[new_child.key]
                if old_idx != new_idx:
                    moves.append((old_idx, new_idx))
                used_old_indices.add(old_idx)
            else:
                creates.append((new_idx, new_child))
    
    # Second pass: handle non-keyed children by trying to match by type/tag
    remaining_old = [(i, child) for i, child in enumerate(old_children) 
                     if i not in used_old_indices]
    remaining_new = [(i, child) for i, child in enumerate(new_children)
                     if not (hasattr(child, 'key') and child.key is not None)]
    
    # Try to match remaining children by similarity
    for new_idx, new_child in remaining_new:
        matched = False
        # Look for a matching old child starting from current position
        for j in range(len(remaining_old)):
            old_idx, old_child = remaining_old[j]
            if same_node(old_child, new_child):
                if old_idx != new_idx:
                    moves.append((old_idx, new_idx))
                used_old_indices.add(old_idx)
                remaining_old.pop(j)
                matched = True
                break
        
        if not matched:
            creates.append((new_idx, new_child))
    
    # Mark remaining old children for deletion
    for old_idx, _ in remaining_old:
        deletes.append(old_idx)
    
    return moves, creates, deletes

def _mount_portal(vnode):
    host = vnode.host
    if host is None:
        return  # host missing, nothing to mount into
    
    rec = MOUNTED.get(host)
    if not rec:
        # Clear host and create new
        for c in host.winfo_children():
            c.destroy()
        w = create_element(vnode.child, host)
        MOUNTED[host] = {"widget": w, "vnode": vnode.child}
    else:
        # Patch existing
        rec["vnode"] = patch(host, rec["vnode"], vnode.child)
        MOUNTED[host] = rec

def patch(parent, old_v, new_v, index=0):
    """Improved patch function with better diffing"""
    # Parent may be missing (e.g., previously destroyed); bail out safely.
    if parent is None:
        return new_v

    children = parent.winfo_children()
    target = children[index] if index < len(children) else None

    # Mount new
    if old_v is None:
        create_element(new_v, parent)
        return new_v

    # Quick equality check - if nodes are completely equal, do nothing
    if nodes_equal(old_v, new_v):
        return new_v

    # Text nodes
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

    # Portals
    if isinstance(old_v, PortalVNode) or isinstance(new_v, PortalVNode):
        if not same_node(old_v, new_v):
            if target and target.winfo_exists():
                target.destroy()
            create_element(new_v, parent)
            return new_v
        _mount_portal(new_v)
        return new_v

    # Different element type → replace
    if not same_node(old_v, new_v):
        if target and target.winfo_exists():
            target.destroy()
        create_element(new_v, parent)
        return new_v

    # Memo skip - but we already checked complete equality above
    if (old_v.memo_key and new_v.memo_key and 
        old_v.memo_key == new_v.memo_key):
        return new_v

    widget = target
    # If target widget vanished for any reason, just recreate subtree
    if widget is None or not widget.winfo_exists():
        create_element(new_v, parent)
        return new_v

    # Update props only if they changed
    old_p, new_p = old_v.props, new_v.props
    if old_p != new_p:
        for k in set(old_p) | set(new_p):
            if old_p.get(k) != new_p.get(k):
                set_prop(widget, k, new_p.get(k))

    # Handle children based on widget type
    if isinstance(widget, tk.Listbox):
        # For listbox, we need to check if items actually changed
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
        
        # Only update listbox if items changed
        if old_items != new_items:
            widget.delete(0, tk.END)
            for item in new_items:
                widget.insert(tk.END, item)
        
        return new_v

    # Enhanced child reconciliation
    old_kids, new_kids = old_v.children, new_v.children
    
    # If no children in both old and new, nothing to do
    if not old_kids and not new_kids:
        return new_v
    
    # Get current child widgets
    current_widgets = widget.winfo_children() if widget and widget.winfo_exists() else []
    
    # Simple case: if structure is exactly the same, just patch in place
    if (len(old_kids) == len(new_kids) and 
        all(same_node(old_kids[i], new_kids[i]) for i in range(len(old_kids)))):
        
        # Patch each child in place
        for i in range(len(new_kids)):
            if i < len(current_widgets) and current_widgets[i].winfo_exists():
                patch(widget, old_kids[i], new_kids[i], i)
            else:
                # Widget missing, recreate this child
                create_element(new_kids[i], widget)
        return new_v
    
    # Complex case: children were added, removed, or reordered
    moves, creates, deletes = find_child_mapping(old_kids, new_kids)
    
    # Apply deletes first (in reverse order to maintain indices)
    for old_idx in sorted(deletes, reverse=True):
        if old_idx < len(current_widgets) and current_widgets[old_idx].winfo_exists():
            current_widgets[old_idx].destroy()
    
    # Refresh widget list after deletions
    current_widgets = widget.winfo_children() if widget and widget.winfo_exists() else []
    
    # Apply moves and updates
    # We need to be careful about order here - tkinter pack order matters
    widget_mapping = {}  # old_index -> widget
    for i, w in enumerate(current_widgets):
        if i < len(old_kids):
            widget_mapping[i] = w
    
    # Create new children and update existing ones
    final_widgets: list = [None] * len(new_kids)
    
    for i, new_child in enumerate(new_kids):
        # Check if this is a moved child
        moved_from = None
        for old_idx, new_idx in moves:
            if new_idx == i:
                moved_from = old_idx
                break
        
        if moved_from is not None:
            # This is a moved child, patch it
            old_widget = widget_mapping.get(moved_from)
            if old_widget and old_widget.winfo_exists():
                patch(widget, old_kids[moved_from], new_child, moved_from)
                final_widgets[i] = old_widget
            else:
                # Widget was destroyed, recreate
                final_widgets[i] = create_element(new_child, widget)
        else:
            # Check if this position had a child that wasn't moved
            found_existing = False
            if i < len(old_kids):
                # Check if old child at this position is staying
                staying = True
                for old_idx, new_idx in moves:
                    if old_idx == i:
                        staying = False
                        break
                if staying and i not in deletes and same_node(old_kids[i], new_child):
                    # Patch existing child in place
                    old_widget = widget_mapping.get(i)
                    if old_widget and old_widget.winfo_exists():
                        patch(widget, old_kids[i], new_child, i)
                        final_widgets[i] = old_widget
                        found_existing = True
            
            if not found_existing:
                # Create new child
                final_widgets[i] = create_element(new_child, widget)
    
    # Reorder widgets if necessary (pack order matters)
    # For simplicity, we'll repack all children in the correct order
    for w in final_widgets:
        if w and w.winfo_exists():
            w.pack_forget()
            w.pack()

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