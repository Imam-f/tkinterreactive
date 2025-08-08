# multi_view_with_portal.py - With conditional component rendering

import rtk
from vdom import h, Portal, Component
from memo import create_memo, memo_key_from


# -------------------------
# Tab Navigation Component (unchanged)
# -------------------------
def TabNavigation(parent_container):
    """Tab navigation component using VDOM-provided container"""
    state = {"active": "counter"}

    def on_switch(tab):
        def handler():
            if state["active"] != tab:
                state["active"] = tab
                lifecycle['events'].append({"type": "tab_changed", "active": tab})
                lifecycle['scheduler'].request("high")
        return handler

    def render():
        mk = memo_key_from([state["active"]])
        return h("div", {"class": "tabs"}, [
            h("button", {"text": "Counter", "command": on_switch("counter")}),
            h("button", {"text": "List", "command": on_switch("list")}),
        ], memo_key=mk)

    def process_message(msg, state, update, scheduler, events):
        if "active" in msg and state["active"] != msg["active"]:
            state["active"] = msg["active"]
            scheduler.request()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            parent_msg = yield lifecycle['flush_events']()
    finally:
        lifecycle['cleanup']()


# -------------------------
# Counter View Component (visibility removed)
# -------------------------
def CounterView(parent_container):
    """Counter component - no longer handles visibility"""
    state = {
        "count": 0,
        "parent_tick": 0
    }

    def on_inc():
        state["count"] += 1
        lifecycle['events'].append({"type": "counter_changed", "count": state["count"]})
        lifecycle['scheduler'].request("high")

    def on_dec():
        state["count"] -= 1
        lifecycle['events'].append({"type": "counter_changed", "count": state["count"]})
        lifecycle['scheduler'].request("high")

    def render():
        mk = memo_key_from(["counter", state["parent_tick"], state["count"]])
        return h("div", {"class": "view counter"}, [
            h("span", {"text": f"Parent tick: {state['parent_tick']}"}),
            h("span", {"text": f"Count: {state['count']}"}),
            h("button", {"text": "Inc", "command": on_inc}),
            h("button", {"text": "Dec", "command": on_dec}),
        ], memo_key=mk)

    def process_message(msg, state, update, scheduler, events):
        updated = False
        
        if "parent_tick" in msg and state["parent_tick"] != msg["parent_tick"]:
            state["parent_tick"] = msg["parent_tick"]
            updated = True
        
        if updated:
            scheduler.request()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            parent_msg = yield lifecycle['flush_events']()
    finally:
        lifecycle['cleanup']()


# -------------------------
# List View Component (visibility removed)
# -------------------------
def ListView(parent_container):
    """List view component - no longer handles visibility"""
    state = {
        "items": [],
        "filter": "",
        "parent_tick": 0
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
            lifecycle['events'].append({"type": "filter_changed", "filter": val})
            lifecycle['scheduler'].request("high")

    def on_add():
        new_item = f"Item {len(state['items']) + 1} @t{state['parent_tick']}"
        state["items"] = state["items"] + [new_item]
        lifecycle['events'].append({"type": "item_added", "items": state["items"]})
        lifecycle['scheduler'].request("high")

    def render():
        mk = memo_key_from(["list", state["filter"], len(state["items"])])
        filtered_items = get_filtered()
        return h("div", {"class": "view list"}, [
            h("div", {"class": "list-controls"}, [
                h("input", {"value": state["filter"], "on_input": on_filter}),
                h("button", {"text": "Add", "command": on_add}),
            ]),
            h("ul", {}, filtered_items, memo_key=mk),
        ], memo_key=mk)

    def process_message(msg, state, update, scheduler, events):
        updated = False
        
        if "parent_tick" in msg and state["parent_tick"] != msg["parent_tick"]:
            state["parent_tick"] = msg["parent_tick"]
            updated = True
        
        if updated:
            scheduler.request()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            parent_msg = yield lifecycle['flush_events']()
    finally:
        lifecycle['cleanup']()


# -------------------------
# Status Bar Component (unchanged)
# -------------------------
def StatusBar(parent_container, portal_host):
    """Status bar component - listens to sibling events"""
    host = rtk.create_host(parent_container)
    host.pack_forget()

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
        return Portal(portal_host, h("div", {"class": "status"}, [
            h("span", {"text": status_text})
        ]), key="status")

    def process_message(msg, state, update, scheduler, events):
        updated = False
        
        for k in ("active", "parent_tick", "title"):
            if k in msg and state.get(k) != msg.get(k):
                state[k] = msg[k]
                updated = True
        
        if updated:
            scheduler.request()

    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            events = lifecycle['flush_events']()
            for event in events:
                if event.get("type") == "counter_changed":
                    if state["counter_count"] != event["count"]:
                        state["counter_count"] = event["count"]
                        lifecycle['scheduler'].request()
                elif event.get("type") == "item_added":
                    new_count = len(event["items"])
                    if state["items_count"] != new_count:
                        state["items_count"] = new_count
                        lifecycle['scheduler'].request()
            
            parent_msg = yield events
    finally:
        lifecycle['cleanup']()


# -------------------------
# Header Component (unchanged)
# -------------------------
def Header(parent_container):
    """Header component using VDOM-provided container"""
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

    def process_message(msg, state, update, scheduler, events):
        updated = False
        for k in ("title", "active", "parent_tick"):
            if k in msg and state.get(k) != msg.get(k):
                state[k] = msg[k]
                updated = True
        if updated:
            scheduler.request()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            parent_msg = yield lifecycle['flush_events']()
    finally:
        lifecycle['cleanup']()


# -------------------------
# Main Coordinator - With automatic component detection
# -------------------------
def MultiViewWithPortal(args, host, portal_host):
    """Main coordinator - automatically detects and manages components"""
    
    state = {
        "active": "counter",
        "parent_tick": 0,
        "title": args["title"],
    }
    
    components = {}

    def render():
        """Conditionally render components based on active state"""
        # Filter children to remove None values
        views_children = list(filter(None, [
            Component(CounterView, key="counter") if state["active"] == "counter" else None,
            Component(ListView, key="list") if state["active"] == "list" else None,
        ]))
        
        return h("div", {"class": "app"}, [
            Component(Header, key="header"),
            Component(TabNavigation, key="tabs"),
            h("div", {"class": "views"}, views_children),
            Component(lambda parent: StatusBar(parent, portal_host), key="status"),
        ])

    def handle_tab_changed(event):
        """Handle tab changes - update state and trigger re-render"""
        if state["active"] != event["active"]:
            state["active"] = event["active"]
            return True
        return False

    def process_message(msg, state, update, scheduler, events):
        updated = False
        
        if "tick" in msg:
            state["parent_tick"] = msg["tick"]
            updated = True
        
        # Auto-initialize any uninitialized components
        # This is safe to call multiple times
        new_components_found = rtk.init_components_from_host(host, components)
        if new_components_found and components:
            rtk.send_to_all_components(components, state)
        
        if components:
            child_events = rtk.send_to_all_components(components, {})
            for event in child_events:
                if event.get("type") == "tab_changed":
                    if handle_tab_changed(event):
                        updated = True
                events.append(event)
            
        if updated and components:
            # Clean up components that are no longer active
            active_keys = {
                "header", "tabs", "status",
                state["active"]  # Only keep the currently active view
            }
            rtk.cleanup_components_by_keys(components, active_keys)
            
            rtk.send_to_all_components(components, state)
            scheduler.request()

    lifecycle = rtk.component_lifecycle(host, render, host, state, process_message)

    try:
        lifecycle['update']()
        
        # Initial component initialization after first render
        rtk.init_components_from_host(host, components)
        if components:
            rtk.send_to_all_components(components, state)
        
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        for component in components.values():
            rtk.cleanup_component(component)
        lifecycle['cleanup']()
