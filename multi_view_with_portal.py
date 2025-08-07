# multi_view_with_portal.py - Components create their own hosts
from vdom import h, Portal, mount_vdom
from scheduler import Scheduler
from memo import create_memo, memo_key_from
from tkinter import ttk

def TabNavigation(parent_container):
    """Standalone tab navigation app that creates its own host"""
    # Create own host
    host = ttk.Frame(parent_container)
    host.pack(fill="x", pady=(0, 10))
    
    state = {
        "active": "counter"
    }
    
    def on_switch(tab):
        def handler():
            if state["active"] != tab:
                state["active"] = tab
                events.append({"type": "tab_changed", "active": tab})
                scheduler.request("high")
        return handler
    
    def render():
        mk = memo_key_from([state["active"]])
        return h(
            "div",
            {"class": "tabs"},
            [
                h("button", {
                    "text": "Counter", 
                    "command": on_switch("counter")
                }),
                h("button", {
                    "text": "List", 
                    "command": on_switch("list")
                }),
            ],
            memo_key=mk,
        )
    
    update, unmount = mount_vdom(host, render)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    events = []
    
    def flush_events():
        batch = events[:]
        events.clear()
        return batch
    
    def cleanup():
        scheduler.cancel()
        unmount()
        if host.winfo_exists():
            host.destroy()
    
    try:
        update()  # Initial render
        parent_msg = yield flush_events()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "active" in parent_msg:
                    state["active"] = parent_msg["active"]
                    update()
            
            scheduler.flush()
            parent_msg = yield flush_events()
            scheduler.defer()
    finally:
        cleanup()


def CounterView(parent_container):
    """Standalone counter app that creates its own host"""
    # Create own host
    host = ttk.Frame(parent_container)
    # Initially hidden - parent will show/hide as needed
    
    state = {
        "count": 0,
        "parent_tick": 0,
        "visible": False
    }
    
    def on_inc():
        state["count"] += 1
        events.append({"type": "counter_changed", "count": state["count"]})
        scheduler.request("high")
    
    def on_dec():
        state["count"] -= 1
        events.append({"type": "counter_changed", "count": state["count"]})
        scheduler.request("high")
    
    def render():
        mk = memo_key_from(["counter", state["parent_tick"], state["count"]])
        return h(
            "div",
            {"class": "view counter"},
            [
                h("span", {"text": f"Parent tick: {state['parent_tick']}"}),
                h("span", {"text": f"Count: {state['count']}"}),
                h("button", {"text": "Inc", "command": on_inc}),
                h("button", {"text": "Dec", "command": on_dec}),
            ],
            memo_key=mk,
        )
    
    def show():
        if not state["visible"]:
            state["visible"] = True
            host.pack(fill="both", expand=True)
    
    def hide():
        if state["visible"]:
            state["visible"] = False
            host.pack_forget()
    
    update, unmount = mount_vdom(host, render)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    events = []
    
    def flush_events():
        batch = events[:]
        events.clear()
        return batch
    
    def cleanup():
        scheduler.cancel()
        unmount()
        if host.winfo_exists():
            host.destroy()
    
    try:
        update()  # Initial render
        parent_msg = yield flush_events()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "parent_tick" in parent_msg:
                    state["parent_tick"] = parent_msg["parent_tick"]
                    update()
                if "show" in parent_msg and parent_msg["show"]:
                    show()
                if "hide" in parent_msg and parent_msg["hide"]:
                    hide()
            
            scheduler.flush()
            parent_msg = yield flush_events()
            scheduler.defer()
    finally:
        cleanup()


def ListView(parent_container):
    """Standalone list view app that creates its own host"""
    # Create own host
    host = ttk.Frame(parent_container)
    # Initially hidden - parent will show/hide as needed
    
    state = {
        "items": [],
        "filter": "",
        "parent_tick": 0,
        "visible": False
    }
    
    memo_filtered = create_memo()
    
    def get_filtered():
        items = tuple(state["items"])
        filt = state["filter"]
        return memo_filtered(
            lambda: [x for x in items if filt.lower() in x.lower()],
            [items, filt]
        )
    
    def on_filter(e):
        val = e.widget.get()
        if state["filter"] != val:
            state["filter"] = val
            events.append({"type": "filter_changed", "filter": val})
            scheduler.request("high")
    
    def on_add():
        new_item = f"Item {len(state['items']) + 1} @t{state['parent_tick']}"
        state["items"] = state["items"] + [new_item]
        events.append({"type": "item_added", "items": state["items"]})
        scheduler.request("high")
    
    def render():
        mk = memo_key_from(["list", state["filter"], len(state["items"])])
        filtered_items = get_filtered()
        
        return h(
            "div",
            {"class": "view list"},
            [
                h("div", {"class": "list-controls"}, [
                    h("input", {"value": state["filter"], "on_input": on_filter}),
                    h("button", {"text": "Add", "command": on_add}),
                ]),
                h("ul", {}, filtered_items, memo_key=mk),
            ],
            memo_key=mk,
        )
    
    def show():
        if not state["visible"]:
            state["visible"] = True
            host.pack(fill="both", expand=True)
    
    def hide():
        if state["visible"]:
            state["visible"] = False
            host.pack_forget()
    
    update, unmount = mount_vdom(host, render)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    events = []
    
    def flush_events():
        batch = events[:]
        events.clear()
        return batch
    
    def cleanup():
        scheduler.cancel()
        unmount()
        if host.winfo_exists():
            host.destroy()
    
    try:
        update()  # Initial render
        parent_msg = yield flush_events()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "parent_tick" in parent_msg:
                    state["parent_tick"] = parent_msg["parent_tick"]
                    update()
                if "show" in parent_msg and parent_msg["show"]:
                    show()
                if "hide" in parent_msg and parent_msg["hide"]:
                    hide()
            
            scheduler.flush()
            parent_msg = yield flush_events()
            scheduler.defer()
    finally:
        cleanup()


def StatusBar(parent_container, portal_host):
    """Standalone status bar app using portal"""
    # Create own host (dummy since we use portal)
    host = ttk.Frame(parent_container)
    host.pack_forget()  # Hidden dummy
    
    state = {
        "active": "counter",
        "parent_tick": 0,
        "counter_count": 0,
        "items_count": 0
    }
    
    def render():
        status_text = (
            f"Active: {state['active']} | "
            f"Tick: {state['parent_tick']} | "
            f"Count: {state['counter_count']} | "
            f"Items: {state['items_count']}"
        )
        status_content = h(
            "div", {"class": "status"}, [h("span", {"text": status_text})]
        )
        return Portal(portal_host, status_content, key="status")
    
    update, unmount = mount_vdom(host, render)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    events = []
    
    def flush_events():
        batch = events[:]
        events.clear()
        return batch
    
    def cleanup():
        scheduler.cancel()
        unmount()
        if host.winfo_exists():
            host.destroy()
    
    try:
        update()  # Initial render
        parent_msg = yield flush_events()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                updated = False
                if "active" in parent_msg and state["active"] != parent_msg["active"]:
                    state["active"] = parent_msg["active"]
                    updated = True
                if "parent_tick" in parent_msg and state["parent_tick"] != parent_msg["parent_tick"]:
                    state["parent_tick"] = parent_msg["parent_tick"]
                    updated = True
                if "counter_count" in parent_msg and state["counter_count"] != parent_msg["counter_count"]:
                    state["counter_count"] = parent_msg["counter_count"]
                    updated = True
                if "items_count" in parent_msg and state["items_count"] != parent_msg["items_count"]:
                    state["items_count"] = parent_msg["items_count"]
                    updated = True
                
                if updated:
                    update()
            
            scheduler.flush()
            parent_msg = yield flush_events()
            scheduler.defer()
    finally:
        cleanup()


def Header(parent_container):
    """Standalone header app that creates its own host"""
    # Create own host
    host = ttk.Frame(parent_container)
    host.pack(fill="x", pady=(0, 10))
    
    state = {
        "title": "App",
        "active": "counter",
        "parent_tick": 0
    }
    
    memo_header = create_memo()
    
    def render():
        header_text = memo_header(
            lambda: f"{state['title']} – {state['active']} (t{state['parent_tick']})",
            [state["title"], state["active"], state["parent_tick"]],
        )
        return h("h2", {"text": header_text})
    
    update, unmount = mount_vdom(host, render)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    events = []
    
    def flush_events():
        batch = events[:]
        events.clear()
        return batch
    
    def cleanup():
        scheduler.cancel()
        unmount()
        if host.winfo_exists():
            host.destroy()
    
    try:
        update()  # Initial render
        parent_msg = yield flush_events()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                updated = False
                if "title" in parent_msg and state["title"] != parent_msg["title"]:
                    state["title"] = parent_msg["title"]
                    updated = True
                if "active" in parent_msg and state["active"] != parent_msg["active"]:
                    state["active"] = parent_msg["active"]
                    updated = True
                if "parent_tick" in parent_msg and state["parent_tick"] != parent_msg["parent_tick"]:
                    state["parent_tick"] = parent_msg["parent_tick"]
                    updated = True
                
                if updated:
                    update()
            
            scheduler.flush()
            parent_msg = yield flush_events()
            scheduler.defer()
    finally:
        cleanup()


def MultiViewWithPortal(args, host, portal_host):
    """Main coordinator app - just coordinates child components"""
    # Application state
    app_state = {
        "active": "counter",
        "parent_tick": 0,
        "title": args["title"],
        "counter_count": 0,
        "items_count": 0,
    }
    
    # Initialize child components - they create their own hosts
    child_components = {}
    
    def init_component(name, component_factory, *extra_args):
        args_list = [host] + list(extra_args)
        component = component_factory(*args_list)
        next(component)  # Initialize
        child_components[name] = {
            "instance": component,
            "events": []
        }
        return component
    
    # Start all child components - they create their own containers
    init_component("header", Header)
    init_component("tabs", TabNavigation)
    init_component("counter", CounterView)
    init_component("list", ListView)
    init_component("status", StatusBar, portal_host)
    
    def send_to_all_children(message):
        """Send message to all child components and collect their events"""
        all_events = []
        for name, child_data in child_components.items():
            try:
                events = child_data["instance"].send(message)
                if events:
                    all_events.extend(events)
            except StopIteration:
                pass
        return all_events
    
    def send_to_child(child_name, message):
        """Send message to specific child component"""
        if child_name in child_components:
            try:
                events = child_components[child_name]["instance"].send(message)
                return events or []
            except StopIteration:
                pass
        return []
    
    def show_view(view_name):
        """Show/hide views by sending show/hide messages"""
        if view_name == "counter":
            send_to_child("counter", {"show": True})
            send_to_child("list", {"hide": True})
        else:
            send_to_child("list", {"show": True})
            send_to_child("counter", {"hide": True})
    
    def process_child_events(events):
        """Process events from child components"""
        app_events = []
        
        for event in events:
            if event["type"] == "tab_changed":
                if app_state["active"] != event["active"]:
                    app_state["active"] = event["active"]
                    show_view(app_state["active"])
                    # Notify all children of the change
                    send_to_all_children({"active": app_state["active"]})
                    app_events.append({"type": "view_changed", "active": app_state["active"]})
            
            elif event["type"] == "counter_changed":
                app_state["counter_count"] = event["count"]
                # Update status bar
                send_to_child("status", {"counter_count": app_state["counter_count"]})
                app_events.append(event)
            
            elif event["type"] == "item_added" or event["type"] == "filter_changed":
                if event["type"] == "item_added":
                    app_state["items_count"] = len(event["items"])
                    # Update status bar
                    send_to_child("status", {"items_count": app_state["items_count"]})
                app_events.append(event)
        
        return app_events
    
    # Initial setup
    show_view(app_state["active"])
    
    # Send initial state to all children
    initial_state = {
        "title": app_state["title"],
        "active": app_state["active"],
        "parent_tick": app_state["parent_tick"],
        "counter_count": app_state["counter_count"],
        "items_count": app_state["items_count"],
    }
    child_events = send_to_all_children(initial_state)
    processed_events = process_child_events(child_events)
    
    try:
        parent_msg = yield processed_events
        
        while True:
            all_events = []
            
            if parent_msg and isinstance(parent_msg, dict):
                if "tick" in parent_msg:
                    app_state["parent_tick"] = parent_msg["tick"]
                    # Send tick to all children
                    child_events = send_to_all_children({"parent_tick": app_state["parent_tick"]})
                    all_events.extend(process_child_events(child_events))
                    
                    # Update status bar with new tick
                    send_to_child("status", {"parent_tick": app_state["parent_tick"]})
                
                elif parent_msg.get("type") == "immediate":
                    # Collect any pending events from children
                    child_events = send_to_all_children({})
                    all_events.extend(process_child_events(child_events))
            
            parent_msg = yield all_events
    
    finally:
        # Clean up all child components (they handle their own host destruction)
        for child_data in child_components.values():
            try:
                child_data["instance"].close()
            except Exception:
                pass