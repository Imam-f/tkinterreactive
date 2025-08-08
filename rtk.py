# rtk.py - Framework utilities (static functions only)
from tkinter import ttk
from vdom import mount_vdom
from scheduler import Scheduler


def create_host(parent_container, pack_options=None):
    """Create a standard host container. Only for top-level or special cases."""
    host = ttk.Frame(parent_container)
    if pack_options:
        host.pack(**pack_options)
    return host


def create_component(component_factory, parent_container, *extra_args):
    """Initialize a component generator."""
    args_list = [parent_container] + list(extra_args)
    component = component_factory(*args_list)
    next(component)  # Initialize to first yield
    return component


def send_to_component(component, message):
    """Send message to a specific component and return its events"""
    try:
        events = component.send(message)
        return events or []
    except StopIteration:
        return []


def send_to_all_components(components_dict, message):
    """Send the same message to all components and collect their events"""
    all_events = []
    for name, component in components_dict.items():
        events = send_to_component(component, message)
        if events:
            all_events.extend(events)
    return all_events


def cleanup_component(component):
    """Clean up a component by closing its generator."""
    try:
        component.close()
    except Exception:
        pass


def create_component_mount(host, render_fn, parent_container):
    """Create mount_vdom and scheduler for a component"""
    update, unmount = mount_vdom(host, render_fn)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    return update, unmount, scheduler


def component_lifecycle(
    host, render_fn, parent_container, state, process_message_fn
):
    """Standard component lifecycle. Host is now managed by parent VDOM."""
    update, unmount, scheduler = create_component_mount(
        host, render_fn, parent_container
    )
    events = []

    def flush_events():
        batch = events[:]
        events.clear()
        return batch

    def cleanup():
        scheduler.cancel()
        unmount()
        # DO NOT destroy host. The parent VDOM that created it is responsible
        # for its lifecycle.

    return {
        "update": update,
        "scheduler": scheduler,
        "events": events,
        "flush_events": flush_events,
        "cleanup": cleanup,
        "process_message": lambda msg: process_message_fn(
            msg, state, update, scheduler, events
        ),
    }


def process_standard_events(events, app_state, components, event_handlers):
    """Process events using provided handlers"""
    app_events = []

    for event in events:
        event_type = event.get("type")
        if event_type in event_handlers:
            result = event_handlers[event_type](event, app_state, components)
            if result:
                app_events.extend(
                    result if isinstance(result, list) else [result]
                )
        else:
            app_events.append(event)  # Pass through unknown events

    return app_events