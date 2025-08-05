# multi_view_with_portal.py - Modified child components
from vdom import h, Portal, mount_vdom
from scheduler import Scheduler
from memo import create_memo, memo_key_from

import time

def TabNavigation(vdom_ref, initial_active="counter"):
    """Tab navigation component that populates vdom_ref"""
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
        vdom = h(
            "div",
            {"class": "tabs"},
            [
                h(
                    "button",
                    {
                        "text": "Counter", 
                        "command": lambda: events.append(on_switch("counter"))
                    },
                ),
                h(
                    "button",
                    {
                        "text": "List", 
                        "command": lambda: events.append(on_switch("list"))
                    },
                ),
            ],
            memo_key=mk,
        )
        # Populate the reference
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom
    
    # Mount to the reference list
    update, unmount = mount_vdom(vdom_ref, render)
    events = []
    
    def request_render():
        update()
    
    try:
        # Initial render
        request_render()
        parent_msg = yield {"events": []}
        
        while True:
            # Update from parent
            if parent_msg and isinstance(parent_msg, dict):
                if "active_tab" in parent_msg:
                    state["active"] = parent_msg["active_tab"]
                    request_render()
            
            # Collect and clear events
            out_events = [e for e in events if e is not None]
            events.clear()
            
            # Yield only events
            parent_msg = yield {"events": out_events}
    except GeneratorExit:
        unmount()

def CounterView(vdom_ref):
    """Counter component that populates vdom_ref"""
    state = {"count": 0}
    parent_tick = 0
    events = []
    
    def push_event(event_type, payload):
        return {"type": event_type, "payload": payload, "source": "counter"}
    
    def on_inc():
        # print(state["count"], "increase")
        state["count"] += 1
        request_render()
        return push_event("counter_changed", state["count"])
    
    def on_dec():
        # print(state["count"], "decrease")
        state["count"] -= 1
        request_render()
        return push_event("counter_changed", state["count"])
    
    def render():
        # print("CounterView render")
        mk = memo_key_from(["counter", parent_tick, state["count"]])
        # print("mk:", mk, state["count"])
        vdom = h(
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
        # Populate the reference
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom
    
    update, unmount = mount_vdom(vdom_ref, render)
    
    def request_render():
        # print('request_render')
        update()
    
    try:
        request_render()
        parent_msg = yield {"events": []}
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "parent_tick" in parent_msg:
                    parent_tick = parent_msg["parent_tick"]
                # if "count" in parent_msg:
                #     state["count"] = parent_msg["count"]
                request_render()
            
            out_events = [e for e in events if e is not None]
            events.clear()
            
            # print("CounterView events:", out_events, state["count"])
            parent_msg = yield {"events": out_events}
            # print("back:", parent_msg)
            # time.sleep(0.5)
    except GeneratorExit:
        unmount()

def ListFilter(vdom_ref):
    """List filter component that populates vdom_ref"""
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
        vdom = h(
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
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom
    
    update, unmount = mount_vdom(vdom_ref, render)
    events = []
    
    def request_render():
        update()
    
    try:
        request_render()
        parent_msg = yield {"events": []}
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "filter" in parent_msg:
                    state["filter"] = parent_msg["filter"]
                    request_render()
            
            out_events = [e for e in events if e is not None]
            events.clear()
            
            parent_msg = yield {"events": out_events}
    except GeneratorExit:
        unmount()

def ListView(vdom_ref):
    """List view component that populates vdom_ref"""
    state = {"items": [], "filter": ""}
    parent_tick = 0
    memo_filtered = create_memo()
    
    # Create child filter component ONCE, outside of render
    filter_vdom_ref = []
    child_filter = ListFilter(filter_vdom_ref)
    next(child_filter)  # Initialize it once
    
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
        
        # Use the existing filter component's VDOM, don't create new one
        vdom = h(
            "div",
            {"class": "view list"},
            [
                filter_vdom_ref[0] if filter_vdom_ref else h("div"),
                h("ul", {}, filtered_items, memo_key=mk),
            ],
            memo_key=mk,
        )
        
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom
    
    update, unmount = mount_vdom(vdom_ref, render)
    events = []
    
    def request_render():
        update()
    
    try:
        request_render()
        parent_msg = yield {"events": []}
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "parent_tick" in parent_msg:
                    parent_tick = parent_msg["parent_tick"]
                if "items" in parent_msg:
                    state["items"] = parent_msg["items"]
                if "filter" in parent_msg:
                    state["filter"] = parent_msg["filter"]
                
                # Update child filter component with new state
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
                
                request_render()  # Re-render after updates
            
            out_events = [e for e in events if e is not None]
            events.clear()
            
            parent_msg = yield {"events": out_events}
    except GeneratorExit:
        unmount()
        if child_filter:
            child_filter.close()


def StatusBar(vdom_ref, portal_host):
    """Status bar component that populates vdom_ref"""
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
            "div", 
            {"class": "status"}, 
            [h("span", {"text": status_text})]
        )
        
        vdom = Portal(portal_host, status_content, key=status_text)
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom
    
    update, unmount = mount_vdom(vdom_ref, render)
    
    def request_render():
        update()
    
    try:
        request_render()
        parent_msg = yield {"events": []}
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "active" in parent_msg:
                    state["active"] = parent_msg["active"]
                if "parent_tick" in parent_msg:
                    state["parent_tick"] = parent_msg["parent_tick"]
                if "counter_count" in parent_msg:
                    state["counter_count"] = parent_msg["counter_count"]
                if "items_count" in parent_msg:
                    state["items_count"] = parent_msg["items_count"]
                request_render()
            
            parent_msg = yield {"events": []}
    except GeneratorExit:
        unmount()

def Header(vdom_ref):
    """Header component that populates vdom_ref"""
    state = {"title": "", "active": "counter", "parent_tick": 0}
    memo_header = create_memo()
    
    def render():
        header_text = memo_header(
            lambda: f"{state['title']} – {state['active']} (t{state['parent_tick']})",
            [state["title"], state["active"], state["parent_tick"]],
        )
        
        vdom = h("h2", {"text": header_text})
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom
    
    update, unmount = mount_vdom(vdom_ref, render)
    
    def request_render():
        update()
    
    try:
        request_render()
        parent_msg = yield {"events": []}
        
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "title" in parent_msg:
                    state["title"] = parent_msg["title"]
                if "active" in parent_msg:
                    state["active"] = parent_msg["active"]
                if "parent_tick" in parent_msg:
                    state["parent_tick"] = parent_msg["parent_tick"]
                request_render()
            
            parent_msg = yield {"events": []}
    except GeneratorExit:
        unmount()

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

    # VDOM references for children
    header_vdom_ref = []
    tabs_vdom_ref = []
    counter_vdom_ref = []
    list_vdom_ref = []
    status_vdom_ref = []

    # Child components with VDOM references
    header_comp = Header(header_vdom_ref)
    tabs_comp = TabNavigation(tabs_vdom_ref, state["active"])
    counter_comp = CounterView(counter_vdom_ref)
    list_comp = ListView(list_vdom_ref)
    status_comp = StatusBar(status_vdom_ref, portal_host)
    
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
                shared_list["items"] = shared_list["items"] + [event["payload"]]
        
        # Update status
        status_msg = {
            "active": state["active"],
            "parent_tick": state["parent_tick"],
            "counter_count": shared_counter["count"],
            "items_count": len(shared_list["items"])
        }
        status_result = status_comp.send(status_msg)

    def root_view():
        # Select current view from VDOM references
        if state["active"] == "counter":
            current_view = counter_vdom_ref[0] if counter_vdom_ref else h("div")
        else:
            current_view = list_vdom_ref[0] if list_vdom_ref else h("div")

        return h(
            "section",
            {"class": "multi-view-with-portal"},
            [
                header_vdom_ref[0] if header_vdom_ref else h("div"),
                tabs_vdom_ref[0] if tabs_vdom_ref else h("div"),
                current_view,
                status_vdom_ref[0] if status_vdom_ref else h("div"),
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
    global updater
    update, unmount = mount_vdom(host, root_view)
    updater = update
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
            scheduler.flush()
            parent_msg = yield flush()
            scheduler.defer()
    finally:
        scheduler.cancel()
        unmount()
        # Close child components
        header_comp.close()
        tabs_comp.close()
        counter_comp.close()
        list_comp.close()
        status_comp.close()
