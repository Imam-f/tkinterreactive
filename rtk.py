# rtk.py - Framework utilities (static functions only)
from tkinter import ttk
from vdom import mount_vdom
from scheduler import Scheduler

def create_host(parent_container, pack_options=None):
    """Create a standard host container"""
    host = ttk.Frame(parent_container)
    if pack_options:
        host.pack(**pack_options)
    return host

def create_component(component_factory, parent_container, *extra_args):
    """Initialize a component with standard lifecycle"""
    args_list = [parent_container] + list(extra_args)
    component = component_factory(*args_list)
    next(component)  # Initialize
    return component

def send_to_component(component, message):
    """Send message to a specific component and return its events"""
    try:
        events = component.send(message)
        return events or []
    except StopIteration:
        return []

def send_to_all_components(components_dict, message):
    """Send message to all components and collect their events"""
    all_events = []
    for name, component in components_dict.items():
        events = send_to_component(component, message)
        if events:
            all_events.extend(events)
    return all_events

def cleanup_component(component):
    """Clean up a component"""
    try:
        component.close()
    except:
        pass

def create_component_mount(host, render_fn, parent_container):
    """Create mount_vdom and scheduler for a component"""
    update, unmount = mount_vdom(host, render_fn)
    scheduler = Scheduler(update, parent_container.winfo_toplevel())
    return update, unmount, scheduler

def component_lifecycle(host, render_fn, parent_container, state, process_message_fn):
    """Standard component lifecycle - returns events list and cleanup function"""
    update, unmount, scheduler = create_component_mount(host, render_fn, parent_container)
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
    
    # Return the lifecycle functions that components can use
    return {
        'update': update,
        'scheduler': scheduler,
        'events': events,
        'flush_events': flush_events,
        'cleanup': cleanup,
        'process_message': lambda msg: process_message_fn(msg, state, update, scheduler, events)
    }

def show_view(component, message=None):
    """Send show message to component"""
    msg = message or {"show": True}
    return send_to_component(component, msg)

def hide_view(component, message=None):
    """Send hide message to component"""
    msg = message or {"hide": True}  
    return send_to_component(component, msg)

def process_standard_events(events, app_state, components, event_handlers):
    """Process events using provided handlers"""
    app_events = []
    
    for event in events:
        event_type = event.get("type")
        if event_type in event_handlers:
            result = event_handlers[event_type](event, app_state, components)
            if result:
                app_events.extend(result if isinstance(result, list) else [result])
        else:
            app_events.append(event)  # Pass through unknown events
    
    return app_events