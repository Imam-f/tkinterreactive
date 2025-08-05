# runner.py
from collections import deque

def run_component(component_gen):
    gen = component_gen
    events_queue = deque()

    try:
        first_batch = next(gen)
        if first_batch:
            events_queue.append(first_batch)
    except StopIteration:
        pass

    class App:
        def get_events(self):
            out = []
            while events_queue:
                out.append(events_queue.popleft())
            return out

        def send(self, msg):
            try:
                ev_batch = gen.send(msg)
                if ev_batch:
                    events_queue.append(ev_batch)
            except StopIteration:
                pass

        def close(self):
            try:
                gen.close()
            except Exception:
                pass

    return App()