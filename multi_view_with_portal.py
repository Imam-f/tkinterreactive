# multi_view_with_portal.py - Modified child components
from vdom import h, Portal, mount_vdom
from scheduler import Scheduler
from memo import create_memo, memo_key_from
from typing import Callable


def TabNavigation(vdom_ref, request_render_immediate: Callable):
    """Tab navigation component that populates vdom_ref"""
    state_holder = {}

    def on_switch(k):
        if state_holder["state"]["active"] != k:
            state_holder["state"]["active"] = k
            request_render_immediate()

    def render(current_state):
        mk = memo_key_from([current_state["active"]])
        vdom = h(
            "div",
            {"class": "tabs"},
            [
                h(
                    "button",
                    {"text": "Counter", "command": lambda: on_switch("counter")},
                ),
                h(
                    "button",
                    {"text": "List", "command": lambda: on_switch("list")},
                ),
            ],
            memo_key=mk,
        )
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom

    def render_closure():
        if "state" in state_holder:
            return render(state_holder["state"])
        return h("div")

    update, unmount = mount_vdom(vdom_ref, render_closure)

    try:
        parent_state = yield
        while True:
            state_holder["state"] = parent_state
            update()
            parent_state = yield
    except GeneratorExit:
        unmount()


def CounterView(vdom_ref, request_render_immediate: Callable):
    """Counter component that populates vdom_ref"""
    state_holder = {}

    def on_inc():
        state_holder["state"]["counter"]["count"] += 1
        request_render_immediate()

    def on_dec():
        state_holder["state"]["counter"]["count"] -= 1
        request_render_immediate()

    def render(current_state):
        parent_tick = current_state["parent_tick"]
        count = current_state["counter"]["count"]
        mk = memo_key_from(["counter", parent_tick, count])
        vdom = h(
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
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom

    def render_closure():
        if "state" in state_holder:
            return render(state_holder["state"])
        return h("div")

    update, unmount = mount_vdom(vdom_ref, render_closure)

    try:
        parent_state = yield
        while True:
            state_holder["state"] = parent_state
            update()
            parent_state = yield
    except GeneratorExit:
        unmount()


def ListFilter(vdom_ref, request_render_immediate: Callable):
    """List filter component that populates vdom_ref"""
    state_holder = {}

    def on_filter(e):
        val = e.widget.get()
        state_holder["state"]["list"]["filter"] = val
        request_render_immediate()

    def on_add():
        current_state = state_holder["state"]
        parent_tick = current_state["parent_tick"]
        new_item = f"Item {len(current_state['list']['items']) + 1} @t{parent_tick}"
        current_state["list"]["items"] = current_state["list"]["items"] + [new_item]
        request_render_immediate()

    def render(current_state):
        filt = current_state["list"]["filter"]
        mk = memo_key_from(["filter", filt])
        vdom = h(
            "div",
            {"class": "list-controls"},
            [
                h("input", {"value": filt, "on_input": on_filter}),
                h("button", {"text": "Add", "command": on_add}),
            ],
            memo_key=mk,
        )
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom

    def render_closure():
        if "state" in state_holder:
            return render(state_holder["state"])
        return h("div")

    update, unmount = mount_vdom(vdom_ref, render_closure)

    try:
        parent_state = yield
        while True:
            state_holder["state"] = parent_state
            update()
            parent_state = yield
    except GeneratorExit:
        unmount()


def ListView(vdom_ref, request_render_immediate: Callable):
    """List view component that populates vdom_ref"""
    memo_filtered = create_memo()
    state_holder = {}

    filter_vdom_ref = []
    child_filter = ListFilter(filter_vdom_ref, request_render_immediate)
    next(child_filter)

    def get_filtered(current_state):
        items = tuple(current_state["list"]["items"])
        filt = current_state["list"]["filter"]
        return memo_filtered(
            lambda: [x for x in items if filt.lower() in x.lower()], [items, filt]
        )

    def render(current_state):
        filt = current_state["list"]["filter"]
        items = current_state["list"]["items"]
        mk = memo_key_from(["list", filt, len(items)])
        filtered_items = get_filtered(current_state)

        try:
            child_filter.send(current_state)
        except StopIteration:
            pass

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

    def render_closure():
        if "state" in state_holder:
            return render(state_holder["state"])
        return h("div")

    update, unmount = mount_vdom(vdom_ref, render_closure)

    try:
        parent_state = yield
        while True:
            state_holder["state"] = parent_state
            update()
            parent_state = yield
    except GeneratorExit:
        unmount()
        child_filter.close()


def StatusBar(vdom_ref, portal_host):
    """Status bar component that populates vdom_ref"""
    state_holder = {}

    def render(current_state):
        status = current_state["status"]
        status_text = (
            f"Active: {status['active']} | "
            f"Tick: {status['parent_tick']} | "
            f"Count: {status['counter_count']} | "
            f"Items: {status['items_count']}"
        )
        status_content = h(
            "div", {"class": "status"}, [h("span", {"text": status_text})]
        )
        vdom = Portal(portal_host, status_content, key=status_text)
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom

    def render_closure():
        if "state" in state_holder:
            return render(state_holder["state"])
        return h("div")

    update, unmount = mount_vdom(vdom_ref, render_closure)

    try:
        parent_state = yield
        while True:
            state_holder["state"] = parent_state
            update()
            parent_state = yield
    except GeneratorExit:
        unmount()


def Header(vdom_ref):
    """Header component that populates vdom_ref"""
    memo_header = create_memo()
    state_holder = {}

    def render(current_state):
        title = current_state["title"]
        active = current_state["active"]
        parent_tick = current_state["parent_tick"]
        header_text = memo_header(
            lambda: f"{title} – {active} (t{parent_tick})",
            [title, active, parent_tick],
        )
        vdom = h("h2", {"text": header_text})
        vdom_ref.clear()
        vdom_ref.append(vdom)
        return vdom

    def render_closure():
        if "state" in state_holder:
            return render(state_holder["state"])
        return h("div")

    update, unmount = mount_vdom(vdom_ref, render_closure)

    try:
        parent_state = yield
        while True:
            state_holder["state"] = parent_state
            update()
            parent_state = yield
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

    state = {
        "active": "counter",
        "parent_tick": 0,
        "title": args["title"],
        "counter": {"count": 0},
        "list": {"items": [], "filter": ""},
        "status": {
            "active": "counter",
            "parent_tick": 0,
            "counter_count": 0,
            "items_count": 0,
        },
    }

    child_contexts = []

    def init_child(component_factory, extra_args=None):
        vdom_ref = []
        init_args = [vdom_ref]
        if extra_args:
            init_args.extend(extra_args)

        instance = component_factory(*init_args)
        next(instance)

        context = {
            "id": component_factory.__name__,
            "instance": instance,
            "vdom_ref": vdom_ref,
        }
        child_contexts.append(context)
        return context

    def request_immediate():
        global pump
        import sys

        pump = sys.modules["__main__"].pump
        app = pump.__closure__[0].cell_contents

        host_parent = host.winfo_toplevel()
        host_parent.after(1, lambda: app.send({"type": "immediate"}))

    init_child(Header)
    init_child(TabNavigation, extra_args=[request_immediate])
    init_child(CounterView, extra_args=[request_immediate])
    init_child(ListView, extra_args=[request_immediate])
    init_child(StatusBar, extra_args=[portal_host])

    def update_children():
        state["status"]["active"] = state["active"]
        state["status"]["parent_tick"] = state["parent_tick"]
        state["status"]["counter_count"] = state["counter"]["count"]
        state["status"]["items_count"] = len(state["list"]["items"])

        for child in child_contexts:
            child["instance"].send(state)

    def get_child_vdom(component_id):
        for child in child_contexts:
            if child["id"] == component_id:
                return child["vdom_ref"][0] if child["vdom_ref"] else h("div")
        return h("div")

    def root_view():
        if state["active"] == "counter":
            current_view = get_child_vdom("CounterView")
        else:
            current_view = get_child_vdom("ListView")

        return h(
            "section",
            {"class": "multi-view-with-portal"},
            [
                get_child_vdom("Header"),
                get_child_vdom("TabNavigation"),
                current_view,
                get_child_vdom("StatusBar"),
            ],
            memo_key=memo_key_from(
                [
                    state["title"],
                    state["active"],
                    state["parent_tick"],
                    state["counter"]["count"],
                    len(state["list"]["items"]),
                    state["list"]["filter"],
                ]
            ),
        )

    update, unmount = mount_vdom(host, root_view)
    scheduler = Scheduler(update, host.winfo_toplevel())

    def request_render():
        update_children()
        scheduler.request()

    try:
        request_render()
        parent_msg = yield flush()
        while True:
            if parent_msg and isinstance(parent_msg, dict):
                if "tick" in parent_msg:
                    state["parent_tick"] = parent_msg["tick"]
                update_children()
                update()

            scheduler.flush()
            parent_msg = yield flush()
            scheduler.defer()
    finally:
        scheduler.cancel()
        unmount()
        for child in child_contexts:
            child["instance"].close()