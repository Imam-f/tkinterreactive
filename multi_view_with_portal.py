# multi_view_with_portal.py - Corrected with proper event pooling

import rtk
from vdom import h, Portal, Component, ComponentVNode
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
            update()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


# -------------------------
# Counter View Component (unchanged)
# -------------------------
def CounterView(parent_container):
    """Counter component using VDOM-provided container"""
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
            update()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


# -------------------------
# List View Component (unchanged)
# -------------------------
def ListView(parent_container):
    """List view component using VDOM-provided container"""
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
            update()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


# -------------------------
# Status Bar Component - Now listens to sibling events directly
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
        
        # Handle parent state updates (only parent's own state)
        for k in ("active", "parent_tick", "title"):
            if k in msg and state.get(k) != msg.get(k):
                state[k] = msg[k]
                updated = True
        
        if updated:
            update()

    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            # Listen for sibling events directly
            events = lifecycle['flush_events']()
            for event in events:
                if event.get("type") == "counter_changed":
                    if state["counter_count"] != event["count"]:
                        state["counter_count"] = event["count"]
                        lifecycle['update']()
                elif event.get("type") == "item_added":
                    new_count = len(event["items"])
                    if state["items_count"] != new_count:
                        state["items_count"] = new_count
                        lifecycle['update']()
            
            lifecycle['scheduler'].flush()
            parent_msg = yield events  # Pass events up to parent
            lifecycle['scheduler'].defer()
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
            update()

    lifecycle = rtk.component_lifecycle(parent_container, render, parent_container, state, process_message)

    try:
        lifecycle['update']()
        parent_msg = yield lifecycle['flush_events']()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


# -------------------------
# Main Coordinator - Fixed event pooling
# -------------------------
def MultiViewWithPortal(args, host, portal_host):
    """Main coordinator - properly pools children events"""
    
    state = {
        "active": "counter",
        "parent_tick": 0,
        "title": args["title"],
    }
    
    components = {}
    components_initialized = False

    def render():
        """Fixed render function - no None values"""
        views_children = []
        if state["active"] == "counter":
            views_children.append(Component(CounterView, key="counter"))
        elif state["active"] == "list":
            views_children.append(Component(ListView, key="list"))
        
        return h("div", {"class": "app"}, [
            Component(Header, key="header"),
            Component(TabNavigation, key="tabs"),
            h("div", {"class": "views"}, views_children),
            Component(lambda parent: StatusBar(parent, portal_host), key="status"),
        ])

    def init_components_if_needed():
        nonlocal components_initialized
        if components_initialized:
            return
        
        def find_component_containers(widget):
            containers = []
            for child in widget.winfo_children():
                vnode = getattr(child, '_vnode', None)
                if isinstance(vnode, ComponentVNode):
                    containers.append(child)
                containers.extend(find_component_containers(child))
            return containers
        
        for container in find_component_containers(host):
            vnode = getattr(container, '_vnode', None)
            if vnode and vnode.key not in components:
                factory = vnode.component_factory
                if hasattr(vnode, 'extra_args') and vnode.extra_args:
                    components[vnode.key] = rtk.create_component(factory, container, *vnode.extra_args)
                else:
                    components[vnode.key] = rtk.create_component(factory, container)
        
        components_initialized = True

    def handle_tab_changed(event):
        """Handle tab changes - affects parent's render"""
        if state["active"] != event["active"]:
            state["active"] = event["active"]
            lifecycle['update']()
            return True
        return False

    def process_message(msg, state, update, scheduler, events):
        """Process external messages and collect child events"""
        updated = False
        
        # Handle external messages
        if "tick" in msg:
            state["parent_tick"] = msg["tick"]
            updated = True
        
        # Always collect events from children (not just on "immediate")
        init_components_if_needed()
        if components:
            child_events = rtk.send_to_all_components(components, {})
            for event in child_events:
                if event.get("type") == "tab_changed":
                    if handle_tab_changed(event):
                        updated = True
                # Pass all events up to parent's caller
                events.append(event)
        
        # Send parent's state to children if updated
        if updated and components:
            rtk.send_to_all_components(components, state)
            update()

    lifecycle = rtk.component_lifecycle(host, render, host, state, process_message)

    try:
        lifecycle['update']()
        init_components_if_needed()
        
        # Send initial parent state to children
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