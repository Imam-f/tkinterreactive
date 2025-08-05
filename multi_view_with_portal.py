# multi_view_with_portal.py
import tkinter as tk
from vdom import h, Portal, mount_vdom
from scheduler import Scheduler
from memo import create_memo, memo_key_from

# Generator component (no classes)
def MultiViewWithPortal(args, host, portal_host):
    out = []

    def push(evt):
        out.append(evt)

    def flush():
        batch = out[:]
        out.clear()
        return batch

    state = {"active": "counter", "parent_tick": 0}
    counter = {"count": 0}
    lst = {"items": [], "filter": ""}

    memo_header = create_memo()
    memo_filtered = create_memo()

    def header_text():
        # return f"{args['title']} – {state['active']} (t{state['parent_tick']})"
        # return f"{args['title']}"
        return memo_header(
            lambda: f"{args['title']} – {state['active']} (t{state['parent_tick']})",
            [args["title"], state["active"], state["parent_tick"]],
        )

    def get_filtered():
        # return [
        #         x for x in lst["items"] if lst["filter"].lower() in x.lower()
        #     ]
        return memo_filtered(
            lambda: [
                x for x in lst["items"] if lst["filter"].lower() in x.lower()
            ],
            [tuple(lst["items"]), lst["filter"]],
        )

    def on_switch(k):
        if state["active"] != k:
            state["active"] = k
            push({"type": "switched", "payload": k})
            request_render()

    def on_inc():
        counter["count"] += 1
        push({"type": "changed", "payload": counter["count"]})
        request_render()

    def on_dec():
        counter["count"] -= 1
        push({"type": "changed", "payload": counter["count"]})
        request_render()

    def on_add():
        v = f"Item {len(lst['items']) + 1} @t{state['parent_tick']}"
        lst["items"] = lst["items"] + [v]
        request_render()

    def on_filter(e):
        val = e.widget.get()
        lst["filter"] = val
        push({"type": "filtered", "payload": val})
        request_render()

    def tabs():
        mk = memo_key_from([state["active"]])
        return h(
            "div",
            {},
            [
                h(
                    "button",
                    {"text": "Counter", "command": lambda: on_switch("counter")},
                    memo_key=mk,
                ),
                h(
                    "button",
                    {"text": "List", "command": lambda: on_switch("list")},
                    memo_key=mk,
                ),
            ],
            memo_key=mk,
        )

    def counter_view():
        pt = state["parent_tick"]
        cnt = counter["count"]
        mk = memo_key_from(["counter", pt, cnt])
        return h(
            "div",
            {"class": "view counter"},
            [
                h("span", {"text": f"Parent tick: {pt}"}),
                h("span", {"text": f"Count: {cnt}"}),
                h("button", {"text": "Inc", "command": on_inc}),
                h("button", {"text": "Dec", "command": on_dec}),
            ],
            memo_key=mk,
        )

    def list_view():
        mk = memo_key_from(["list", lst["filter"], len(lst["items"]), counter["count"]])
        filtered = get_filtered()
        return h(
            "div",
            {"class": "view list"},
            [
                h(
                    "div",
                    {},
                    [
                        h("input", {"value": lst["filter"], "on_input": on_filter}),
                        h("button", {"text": "Add", "command": on_add}),
                    ],
                    memo_key=mk,
                ),
                h("ul", {}, filtered, memo_key=mk),
            ],
            memo_key=mk,
        )

    def status_bar():
        text = (
            f"Active: {state['active']} | "
            f"Tick: {state['parent_tick']} | "
            f"Count: {counter['count']} | "
            f"Items: {len(lst['items'])}"
        )
        print(text)
        span = h("span", {"text": text})
        # return Portal(portal_host, h("div", {"class": "status"}, [span]), key="status")
        return Portal(portal_host, h("div", {"class": "status"}, [span]), key=text)

    def root_view():
        return h(
            "section",
            {"class": "multi-view-with-portal"},
            [
                h("h2", {"text": header_text()}),
                tabs(),
                (counter_view() if state["active"] == "counter" else list_view()),
                status_bar(),
            ],
            memo_key=memo_key_from([args["title"], state["active"], state["parent_tick"], counter["count"], len(lst["items"]), lst["filter"]]),
        )

    update, unmount = mount_vdom(host, root_view)
    scheduler = Scheduler(update, host.winfo_toplevel())

    def request_render():
        # print("late bind")
        scheduler.request()

    try:
        request_render()
        parent_msg = yield flush()
        while True:
            if parent_msg and isinstance(parent_msg, dict) and "tick" in parent_msg:
                state["parent_tick"] = parent_msg["tick"]
                request_render()
            parent_msg = yield flush()
    finally:
        scheduler.cancel()
        unmount()