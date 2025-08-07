# multi_view_with_portal.py - User code using rtk framework
import rtk
from vdom import h, Portal
from memo import create_memo, memo_key_from

def TabNavigation(parent_container):
    """Tab navigation component using rtk framework"""
    host = rtk.create_host(parent_container, {"fill": "x", "pady": (0, 10)})
    
    state = {
        "active": "counter"
    }
    
    def on_switch(tab):
        def handler():
            if state["active"] != tab:
                state["active"] = tab
                lifecycle['events'].append({"type": "tab_changed", "active": tab})
                lifecycle['scheduler'].request("high")
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
    
    def process_message(msg, state, update, scheduler, events):
        if "active" in msg:
            state["active"] = msg["active"]
            update()
    
    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)
    
    try:
        lifecycle['update']()  # Initial render
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


def CounterView(parent_container):
    """Counter component using rtk framework"""
    host = rtk.create_host(parent_container)  # No initial pack - controlled by show/hide
    
    state = {
        "count": 0,
        "parent_tick": 0,
        "visible": False
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
    
    def process_message(msg, state, update, scheduler, events):
        if "parent_tick" in msg:
            state["parent_tick"] = msg["parent_tick"]
            update()
        if "show" in msg and msg["show"]:
            show()
        if "hide" in msg and msg["hide"]:
            hide()
    
    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)
    
    try:
        lifecycle['update']()  # Initial render
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


def ListView(parent_container):
    """List view component using rtk framework"""
    host = rtk.create_host(parent_container)  # No initial pack - controlled by show/hide
    
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
    
    def process_message(msg, state, update, scheduler, events):
        if "parent_tick" in msg:
            state["parent_tick"] = msg["parent_tick"]
            update()
        if "show" in msg and msg["show"]:
            show()
        if "hide" in msg and msg["hide"]:
            hide()
    
    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)
    
    try:
        lifecycle['update']()  # Initial render
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


def StatusBar(parent_container, portal_host):
    """Status bar component using rtk framework"""
    host = rtk.create_host(parent_container)  # Hidden dummy for portal
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
        status_content = h(
            "div", {"class": "status"}, [h("span", {"text": status_text})]
        )
        return Portal(portal_host, status_content, key="status")
    
    def process_message(msg, state, update, scheduler, events):
        updated = False
        if "active" in msg and state["active"] != msg["active"]:
            state["active"] = msg["active"]
            updated = True
        if "parent_tick" in msg and state["parent_tick"] != msg["parent_tick"]:
            state["parent_tick"] = msg["parent_tick"]
            updated = True
        if "counter_count" in msg and state["counter_count"] != msg["counter_count"]:
            state["counter_count"] = msg["counter_count"]
            updated = True
        if "items_count" in msg and state["items_count"] != msg["items_count"]:
            state["items_count"] = msg["items_count"]
            updated = True
        
        if updated:
            update()
    
    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)
    
    try:
        lifecycle['update']()  # Initial render
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


def Header(parent_container):
    """Header component using rtk framework"""
    host = rtk.create_host(parent_container, {"fill": "x", "pady": (0, 10)})
    
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
        if "title" in msg and state["title"] != msg["title"]:
            state["title"] = msg["title"]
            updated = True
        if "active" in msg and state["active"] != msg["active"]:
            state["active"] = msg["active"]
            updated = True
        if "parent_tick" in msg and state["parent_tick"] != msg["parent_tick"]:
            state["parent_tick"] = msg["parent_tick"]
            updated = True
        
        if updated:
            update()
    
    lifecycle = rtk.component_lifecycle(host, render, parent_container, state, process_message)
    
    try:
        lifecycle['update']()  # Initial render
        parent_msg = yield lifecycle['flush_events']()
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                lifecycle['process_message'](parent_msg)
            
            lifecycle['scheduler'].flush()
            parent_msg = yield lifecycle['flush_events']()
            lifecycle['scheduler'].defer()
    finally:
        lifecycle['cleanup']()


def MultiViewWithPortal(args, host, portal_host):
    """Main coordinator app using rtk framework"""
    # Application state (user-defined)
    app_state = {
        "active": "counter",
        "parent_tick": 0,
        "title": args["title"],
        "counter_count": 0,
        "items_count": 0,
    }
    
    # Initialize child components using rtk
    components = {
        "header": rtk.create_component(Header, host),
        "tabs": rtk.create_component(TabNavigation, host),
        "counter": rtk.create_component(CounterView, host),
        "list": rtk.create_component(ListView, host),
        "status": rtk.create_component(StatusBar, host, portal_host),
    }
    
    # Event handlers (user-defined business logic)
    def handle_tab_changed(event, app_state, components):
        if app_state["active"] != event["active"]:
            app_state["active"] = event["active"]
            # Show/hide views using rtk
            if app_state["active"] == "counter":
                rtk.show_view(components["counter"])
                rtk.hide_view(components["list"])
            else:
                rtk.show_view(components["list"])
                rtk.hide_view(components["counter"])
            
            # Notify all components of the change
            rtk.send_to_all_components(components, {"active": app_state["active"]})
            return {"type": "view_changed", "active": app_state["active"]}
    
    def handle_counter_changed(event, app_state, components):
        app_state["counter_count"] = event["count"]
        # Update status bar
        rtk.send_to_component(components["status"], {"counter_count": app_state["counter_count"]})
        return event
    
    def handle_item_added(event, app_state, components):
        app_state["items_count"] = len(event["items"])
        # Update status bar
        rtk.send_to_component(components["status"], {"items_count": app_state["items_count"]})
        return event
    
    # Event handler mapping (user-defined)
    event_handlers = {
        "tab_changed": handle_tab_changed,
        "counter_changed": handle_counter_changed,
        "item_added": handle_item_added,
        "filter_changed": lambda event, app_state, components: event,  # Pass through
    }
    
    # Initial setup using rtk
    rtk.show_view(components["counter"])
    rtk.hide_view(components["list"])
    
    # Send initial state to all children
    initial_state = {
        "title": app_state["title"],
        "active": app_state["active"],
        "parent_tick": app_state["parent_tick"],
        "counter_count": app_state["counter_count"],
        "items_count": app_state["items_count"],
    }
    child_events = rtk.send_to_all_components(components, initial_state)
    processed_events = rtk.process_standard_events(child_events, app_state, components, event_handlers)
    
    try:
        parent_msg = yield processed_events
        
        while True:
            all_events = []
            
            if parent_msg and isinstance(parent_msg, dict):
                if "tick" in parent_msg:
                    app_state["parent_tick"] = parent_msg["tick"]
                    # Send tick to all children using rtk
                    child_events = rtk.send_to_all_components(components, {"parent_tick": app_state["parent_tick"]})
                    all_events.extend(rtk.process_standard_events(child_events, app_state, components, event_handlers))
                    
                    # Update status bar with new tick
                    rtk.send_to_component(components["status"], {"parent_tick": app_state["parent_tick"]})
                
                elif parent_msg.get("type") == "immediate":
                    # Collect any pending events from children using rtk
                    child_events = rtk.send_to_all_components(components, {})
                    all_events.extend(rtk.process_standard_events(child_events, app_state, components, event_handlers))
            
            parent_msg = yield all_events
    
    finally:
        # Clean up all child components using rtk
        for component in components.values():
            rtk.cleanup_component(component)