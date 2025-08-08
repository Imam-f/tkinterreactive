# rtk.py - Framework utilities (static functions only)
from tkinter import ttk
from vdom import mount_vdom, ComponentVNode
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


def find_component_containers(widget):
    """Find all ComponentVNode containers in a widget tree"""
    containers = []
    if not widget or not hasattr(widget, 'winfo_children'):
        return containers
        
    try:
        for child in widget.winfo_children():
            if not child.winfo_exists():
                continue
                
            vnode = getattr(child, '_vnode', None)
            if isinstance(vnode, ComponentVNode):
                containers.append(child)
            containers.extend(find_component_containers(child))
    except Exception:
        # Widget might have been destroyed during traversal
        pass
    
    return containers


def init_components_from_host(host, components_dict):
    """
    Initialize any uninitialized ComponentVNodes found in host widget tree.
    Safe to call multiple times - only initializes missing components.
    Returns True if any new components were initialized.
    """
    if not host or not hasattr(host, 'winfo_exists') or not host.winfo_exists():
        return False
        
    new_components_found = False
    
    for container in find_component_containers(host):
        vnode = getattr(container, '_vnode', None)
        if not vnode or not vnode.key:
            continue
            
        # Only initialize if not already in components dict
        if vnode.key not in components_dict:
            try:
                factory = vnode.component_factory
                if hasattr(vnode, 'extra_args') and vnode.extra_args:
                    components_dict[vnode.key] = create_component(factory, container, *vnode.extra_args)
                else:
                    components_dict[vnode.key] = create_component(factory, container)
                new_components_found = True
            except Exception as e:
                print(f"Failed to initialize component {vnode.key}: {e}")
    
    return new_components_found


def cleanup_components_by_keys(components_dict, active_keys):
    """Clean up components whose keys are not in the active_keys set"""
    keys_to_remove = []
    for key in components_dict.keys():
        if key not in active_keys:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        cleanup_component(components_dict[key])
        del components_dict[key]
    
    return len(keys_to_remove) > 0  # Return if any components were cleaned up


def has_uninitialized_components(host, components_dict):
    """Check if there are ComponentVNodes in the widget tree that aren't initialized"""
    if not host or not hasattr(host, 'winfo_exists') or not host.winfo_exists():
        return False
        
    for container in find_component_containers(host):
        vnode = getattr(container, '_vnode', None)
        if vnode and vnode.key and vnode.key not in components_dict:
            return True
    
    return False


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