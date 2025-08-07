# multi_view_with_portal.py - Refactored with self-contained components

from vdom import h, Portal, mount_vdom, Component
from scheduler import Scheduler
from memo import create_memo, memo_key_from
from typing import Callable

class ComponentState:
    """Simple state management for components"""
    def __init__(self, initial_state=None):
        self.state = initial_state or {}
        self.listeners = []
    
    def update(self, updates):
        self.state.update(updates)
        for listener in self.listeners:
            listener()
    
    def subscribe(self, listener):
        self.listeners.append(listener)
    
    def unsubscribe(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

def TabNavigation(parent_state, on_change):
    """Self-contained tab navigation component"""
    def render():
        active = parent_state.get("active", "counter")
        mk = memo_key_from([active])
        
        def switch_to(tab):
            def handler():
                on_change({"active": tab})
            return handler
        
        return h(
            "div",
            {"class": "tabs"},
            [
                h("button", {
                    "text": "Counter", 
                    "command": switch_to("counter")
                }),
                h("button", {
                    "text": "List", 
                    "command": switch_to("list")
                }),
            ],
            memo_key=mk,
        )
    
    return render

def CounterView(parent_state, on_change):
    """Self-contained counter component"""
    def render():
        parent_tick = parent_state.get("parent_tick", 0)
        count = parent_state.get("counter", {}).get("count", 0)
        mk = memo_key_from(["counter", parent_tick, count])
        
        def on_inc():
            counter = parent_state.get("counter", {})
            counter["count"] = counter.get("count", 0) + 1
            on_change({"counter": counter})
        
        def on_dec():
            counter = parent_state.get("counter", {})
            counter["count"] = counter.get("count", 0) - 1
            on_change({"counter": counter})
        
        return h(
            "div",
            {"class": "view counter"},
            [
                h("span", {"text": f"Parent tick: {parent_tick}"}),
                h("span", {"text": f"Count: {count}"}),
                h("button", {"text": "Inc", "command": on_inc}),
                h("button", {"text": "Dec", "command": on_dec}),
            ],
            memo_key=mk,
        )
    
    return render

def ListView(parent_state, on_change):
    """Self-contained list view component"""
    memo_filtered = create_memo()
    
    def get_filtered():
        items = tuple(parent_state.get("list", {}).get("items", []))
        filt = parent_state.get("list", {}).get("filter", "")
        return memo_filtered(
            lambda: [x for x in items if filt.lower() in x.lower()],
            [items, filt]
        )
    
    def render():
        list_state = parent_state.get("list", {})
        filt = list_state.get("filter", "")
        items = list_state.get("items", [])
        mk = memo_key_from(["list", filt, len(items)])
        
        def on_filter(e):
            val = e.widget.get()
            new_list_state = list_state.copy()
            new_list_state["filter"] = val
            on_change({"list": new_list_state})
        
        def on_add():
            parent_tick = parent_state.get("parent_tick", 0)
            new_item = f"Item {len(items) + 1} @t{parent_tick}"
            new_list_state = list_state.copy()
            new_list_state["items"] = items + [new_item]
            on_change({"list": new_list_state})
        
        filtered_items = get_filtered()
        
        return h(
            "div",
            {"class": "view list"},
            [
                h("div", {"class": "list-controls"}, [
                    h("input", {"value": filt, "on_input": on_filter}),
                    h("button", {"text": "Add", "command": on_add}),
                ]),
                h("ul", {}, filtered_items, memo_key=mk),
            ],
            memo_key=mk,
        )
    
    return render

def StatusBar(parent_state, portal_host):
    """Status bar component using portal"""
    def render():
        status = parent_state.get("status", {})
        status_text = (
            f"Active: {status.get('active', 'none')} | "
            f"Tick: {status.get('parent_tick', 0)} | "
            f"Count: {status.get('counter_count', 0)} | "
            f"Items: {status.get('items_count', 0)}"
        )
        status_content = h(
            "div", {"class": "status"}, [h("span", {"text": status_text})]
        )
        return Portal(portal_host, status_content, key="status")
    
    return render

def Header(parent_state):
    """Header component"""
    memo_header = create_memo()
    
    def render():
        title = parent_state.get("title", "App")
        active = parent_state.get("active", "none")
        parent_tick = parent_state.get("parent_tick", 0)
        
        header_text = memo_header(
            lambda: f"{title} – {active} (t{parent_tick})",
            [title, active, parent_tick],
        )
        
        return h("h2", {"text": header_text})
    
    return render

def MultiViewWithPortal(args, host, portal_host):
    """Main component with enhanced self-contained child management"""
    out = []
    
    def push(evt):
        out.append(evt)
    
    def flush():
        batch = out[:]
        out.clear()
        return batch
    
    # Application state
    app_state = ComponentState({
        "active": "counter",
        "parent_tick": 0,
        "title": args["title"],
        "counter": {"count": 0},
        "list": {"items": [], "filter": ""},
    })
    
    def update_status():
        app_state.state["status"] = {
            "active": app_state.state["active"],
            "parent_tick": app_state.state["parent_tick"],
            "counter_count": app_state.state["counter"]["count"],
            "items_count": len(app_state.state["list"]["items"]),
        }
    
    def on_state_change(updates):
        app_state.update(updates)
        update_status()
        if scheduler:
            scheduler.request("high")  # Immediate update for user interactions
    
    # Create component renderers
    header_render = Header(app_state.state)
    tab_nav_render = TabNavigation(app_state.state, on_state_change)
    counter_render = CounterView(app_state.state, on_state_change)
    list_render = ListView(app_state.state, on_state_change)
    status_render = StatusBar(app_state.state, portal_host)
    
    def root_view():
        current_view = (
            counter_render() if app_state.state["active"] == "counter" 
            else list_render()
        )
        
        return h(
            "section",
            {"class": "multi-view-with-portal"},
            [
                header_render(),
                tab_nav_render(),
                current_view,
                status_render(),
            ],
            memo_key=memo_key_from([
                app_state.state["title"],
                app_state.state["active"],
                app_state.state["parent_tick"],
                app_state.state["counter"]["count"],
                len(app_state.state["list"]["items"]),
                app_state.state["list"]["filter"],
            ])
        )
    
    update, unmount = mount_vdom(host, root_view)
    scheduler = Scheduler(update, host.winfo_toplevel())
    
    def request_render():
        update_status()
        scheduler.request("low")  # Batched update for external changes
    
    try:
        request_render()
        parent_msg = yield flush()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "tick" in parent_msg:
                    app_state.update({"parent_tick": parent_msg["tick"]})
                    scheduler.request("low")
                elif parent_msg.get("type") == "immediate":
                    update()
            
            scheduler.flush()
            parent_msg = yield flush()
            scheduler.defer()
    finally:
        scheduler.cancel()
        unmount()