# multi_view_with_portal.py
from vdom import h, Portal, mount_vdom
from scheduler import Scheduler
from memo import create_memo, memo_key_from

# Tab Navigation Component (Coroutine)
def TabNavigation(initial_active="counter"):
    """Tab navigation component with its own state"""
    state = {"active": initial_active}
    
    def push_event(event_type, payload):
        return {"type": event_type, "payload": payload, "source": "tabs"}
    
    def on_switch(k):
        if state["active"] != k:
            state["active"] = k
            return push_event("tab_switched", k)
        return None
    
    def render():
        mk = memo_key_from([state["active"]])
        return h(
            "div",
            {"class": "tabs"},
            [
                h(
                    "button",
                    {
                        "text": "Counter", 
                        "command": lambda: events.append(on_switch("counter"))
                    },
                    memo_key=mk,
                ),
                h(
                    "button",
                    {
                        "text": "List", 
                        "command": lambda: events.append(on_switch("list"))
                    },
                    memo_key=mk,
                ),
            ],
            memo_key=mk,
        )
    
    events = []
    
    try:
        # Initial render
        parent_msg = yield {"vdom": render(), "events": []}
        
        while True:
            # Update state from parent if needed
            if parent_msg and isinstance(parent_msg, dict):
                if "active_tab" in parent_msg:
                    state["active"] = parent_msg["active_tab"]
            
            # Collect and clear events
            out_events = [e for e in events if e is not None]
            events.clear()
            
            # Yield updated render and events
            parent_msg = yield {"vdom": render(), "events": out_events}
    except GeneratorExit:
        pass

# Counter View Component (Coroutine)
def CounterView():
    """Counter component with its own state"""
    state = {"count": 0}
    parent_tick = 0
    
    def push_event(event_type, payload):
        return {"type": event_type, "payload": payload, "source": "counter"}
    
    def on_inc():
        state["count"] += 1
        return push_event("counter_changed", state["count"])
    
    def on_dec():
        state["count"] -= 1
        return push_event("counter_changed", state["count"])
    
    def render():
        mk = memo_key_from(["counter", parent_tick, state["count"]])
        return h(
            "div",
            {"class": "view counter"},
            [
                h("span", {"text": f"Parent tick: {parent_tick}"}),
                h("span", {"text": f"Count: {state['count']}"}),
                h("button", {"text": "Inc", "command": lambda: events.append(on_inc())}),
                h("button", {"text": "Dec", "command": lambda: events.append(on_dec())}),
            ],
            memo_key=mk,
        )
    
    events = []
    
    try:
        # Initial render
        parent_msg = yield {"vdom": render(), "events": []}
        
        while True:
            # Update from parent
            if parent_msg and isinstance(parent_msg, dict):
                if "parent_tick" in parent_msg:
                    parent_tick = parent_msg["parent_tick"]
                if "count" in parent_msg:
                    state["count"] = parent_msg["count"]
            
            # Collect and clear events
            out_events = [e for e in events if e is not None]
            events.clear()
            
            # Yield updated render and events
            parent_msg = yield {"vdom": render(), "events": out_events}
    except GeneratorExit:
        pass

# List Filter Component (Coroutine)
def ListFilter():
    """List filter component with its own state"""
    state = {"filter": ""}
    
    def push_event(event_type, payload):
        return {"type": event_type, "payload": payload, "source": "list_filter"}
    
    def on_filter(e):
        val = e.widget.get()
        state["filter"] = val
        return push_event("filter_changed", val)
    
    def on_add():
        return push_event("item_add_requested", None)
    
    def render():
        mk = memo_key_from(["filter", state["filter"]])
        return h(
            "div",
            {"class": "list-controls"},
            [
                h("input", {
                    "value": state["filter"], 
                    "on_input": lambda e: events.append(on_filter(e))
                }),
                h("button", {
                    "text": "Add", 
                    "command": lambda: events.append(on_add())
                }),
            ],
            memo_key=mk,
        )
    
    events = []
    
    try:
        # Initial render
        parent_msg = yield {"vdom": render(), "events": []}
        
        while True:
            # Update from parent
            if parent_msg and isinstance(parent_msg, dict):
                if "filter" in parent_msg:
                    state["filter"] = parent_msg["filter"]
            
            # Collect and clear events
            out_events = [e for e in events if e is not None]
            events.clear()
            
            # Yield updated render and events
            parent_msg = yield {"vdom": render(), "events": out_events}
    except GeneratorExit:
        pass

# List View Component (Coroutine)
def ListView():
    """List view component with its own state"""
    state = {"items": [], "filter": ""}
    parent_tick = 0
    memo_filtered = create_memo()
    
    def push_event(event_type, payload):
        return {"type": event_type, "payload": payload, "source": "list_view"}
    
    def get_filtered():
        return memo_filtered(
            lambda: [
                x for x in state["items"] if state["filter"].lower() in x.lower()
            ],
            [tuple(state["items"]), state["filter"]],
        )
    
    def render():
        mk = memo_key_from([
            "list", 
            state["filter"], 
            len(state["items"])
        ])
        
        filtered_items = get_filtered()
        
        # Create child filter component
        filter_component = ListFilter()
        filter_result = next(filter_component)
        
        return h(
            "div",
            {"class": "view list"},
            [
                filter_result["vdom"],
                h("ul", {}, filtered_items, memo_key=mk),
            ],
            memo_key=mk,
        ), filter_component
    
    events = []
    child_filter = None
    
    try:
        # Initial render
        vdom, child_filter = render()
        parent_msg = yield {"vdom": vdom, "events": []}
        
        while True:
            # Update from parent
            if parent_msg and isinstance(parent_msg, dict):
                if "parent_tick" in parent_msg:
                    parent_tick = parent_msg["parent_tick"]
                if "items" in parent_msg:
                    state["items"] = parent_msg["items"]
                if "filter" in parent_msg:
                    state["filter"] = parent_msg["filter"]
            
            # Update child filter component
            if child_filter:
                try:
                    child_msg = {"filter": state["filter"]}
                    child_result = child_filter.send(child_msg)
                    
                    # Handle child events
                    for event in child_result["events"]:
                        if event["type"] == "filter_changed":
                            state["filter"] = event["payload"]
                            events.append(push_event("filter_changed", event["payload"]))
                        elif event["type"] == "item_add_requested":
                            new_item = f"Item {len(state['items']) + 1} @t{parent_tick}"
                            state["items"] = state["items"] + [new_item]
                            events.append(push_event("item_added", new_item))
                except StopIteration:
                    child_filter = None
            
            # Collect and clear events
            out_events = [e for e in events if e is not None]
            events.clear()
            
            # Re-render
            vdom, child_filter = render()
            
            # Yield updated render and events
            parent_msg = yield {"vdom": vdom, "events": out_events}
    except GeneratorExit:
        if child_filter:
            child_filter.close()

# Status Bar Component (Coroutine)
def StatusBar(portal_host):
    """Status bar component rendered in portal"""
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
        
        print(status_text)  # Debug output
        
        status_content = h(
            "div", 
            {"class": "status"}, 
            [h("span", {"text": status_text})]
        )
        
        return Portal(portal_host, status_content, key=status_text)
    
    try:
        # Initial render
        parent_msg = yield {"vdom": render(), "events": []}
        
        while True:
            # Update from parent
            if parent_msg and isinstance(parent_msg, dict):
                if "active" in parent_msg:
                    state["active"] = parent_msg["active"]
                if "parent_tick" in parent_msg:
                    state["parent_tick"] = parent_msg["parent_tick"]
                if "counter_count" in parent_msg:
                    state["counter_count"] = parent_msg["counter_count"]
                if "items_count" in parent_msg:
                    state["items_count"] = parent_msg["items_count"]
            
            # Status bar doesn't generate events, only displays state
            parent_msg = yield {"vdom": render(), "events": []}
    except GeneratorExit:
        pass

# Header Component (Coroutine)
def Header():
    """Header component with memoized title"""
    state = {"title": "", "active": "counter", "parent_tick": 0}
    memo_header = create_memo()
    
    def render():
        header_text = memo_header(
            lambda: f"{state['title']} – {state['active']} (t{state['parent_tick']})",
            [state["title"], state["active"], state["parent_tick"]],
        )
        
        return h("h2", {"text": header_text})
    
    try:
        # Initial render
        parent_msg = yield {"vdom": render(), "events": []}
        
        while True:
            # Update from parent
            if parent_msg and isinstance(parent_msg, dict):
                if "title" in parent_msg:
                    state["title"] = parent_msg["title"]
                if "active" in parent_msg:
                    state["active"] = parent_msg["active"]
                if "parent_tick" in parent_msg:
                    state["parent_tick"] = parent_msg["parent_tick"]
            
            # Header doesn't generate events, only displays state
            parent_msg = yield {"vdom": render(), "events": []}
    except GeneratorExit:
        pass

# Main Multi-View Component (Coroutine)
def MultiViewWithPortal(args, host, portal_host):
    out = []

    def push(evt):
        out.append(evt)

    def flush():
        batch = out[:]
        out.clear()
        return batch

    # Main component state
    state = {"active": "counter", "parent_tick": 0}
    
    # Shared state that children need
    shared_counter = {"count": 0}
    shared_list = {"items": [], "filter": ""}

    # Child components
    header_comp = Header()
    tabs_comp = TabNavigation(state["active"])
    counter_comp = CounterView()
    list_comp = ListView()
    status_comp = StatusBar(portal_host)
    
    # Initialize child components
    header_result = next(header_comp)
    tabs_result = next(tabs_comp)
    counter_result = next(counter_comp)
    list_result = next(list_comp)
    status_result = next(status_comp)

    def update_children():
        nonlocal header_result, tabs_result, counter_result, list_result, status_result
        
        # Update header
        header_msg = {
            "title": args["title"],
            "active": state["active"],
            "parent_tick": state["parent_tick"]
        }
        header_result = header_comp.send(header_msg)
        
        # Update tabs
        tabs_msg = {"active_tab": state["active"]}
        tabs_result = tabs_comp.send(tabs_msg)
        
        # Process tab events
        for event in tabs_result["events"]:
            if event["type"] == "tab_switched":
                state["active"] = event["payload"]
                push({"type": "switched", "payload": event["payload"]})
        
        # Update counter
        counter_msg = {
            "parent_tick": state["parent_tick"],
            "count": shared_counter["count"]
        }
        counter_result = counter_comp.send(counter_msg)
        
        # Process counter events
        for event in counter_result["events"]:
            if event["type"] == "counter_changed":
                shared_counter["count"] = event["payload"]
                push({"type": "changed", "payload": event["payload"]})
        
        # Update list
        list_msg = {
            "parent_tick": state["parent_tick"],
            "items": shared_list["items"],
            "filter": shared_list["filter"]
        }
        list_result = list_comp.send(list_msg)
        
        # Process list events
        for event in list_result["events"]:
            if event["type"] == "filter_changed":
                shared_list["filter"] = event["payload"]
                push({"type": "filtered", "payload": event["payload"]})
            elif event["type"] == "item_added":
                shared_list["items"] = list_result["events"][0]["payload"] if list_result["events"] else shared_list["items"]
        
        # Update status
        status_msg = {
            "active": state["active"],
            "parent_tick": state["parent_tick"],
            "counter_count": shared_counter["count"],
            "items_count": len(shared_list["items"])
        }
        status_result = status_comp.send(status_msg)

    def root_view():
        # Select current view
        if state["active"] == "counter":
            current_view = counter_result["vdom"]
        else:
            current_view = list_result["vdom"]

        return h(
            "section",
            {"class": "multi-view-with-portal"},
            [
                header_result["vdom"],
                tabs_result["vdom"],
                current_view,
                status_result["vdom"],
            ],
            memo_key=memo_key_from([
                args["title"], 
                state["active"], 
                state["parent_tick"], 
                shared_counter["count"], 
                len(shared_list["items"]), 
                shared_list["filter"]
            ]),
        )

    # Setup VDOM mounting and scheduler
    update, unmount = mount_vdom(host, root_view)
    scheduler = Scheduler(update, host.winfo_toplevel())

    def request_render():
        update_children()
        scheduler.request()

    # Component lifecycle
    try:
        request_render()
        parent_msg = yield flush()
        while True:
            if parent_msg and isinstance(parent_msg, dict) and "tick" in parent_msg:
                state["parent_tick"] = parent_msg["tick"]
                request_render()
            scheduler.defer()
            parent_msg = yield flush()
            scheduler.flush()
    finally:
        scheduler.cancel()
        unmount()
        # Close child components
        header_comp.close()
        tabs_comp.close()
        counter_comp.close()
        list_comp.close()
        status_comp.close()