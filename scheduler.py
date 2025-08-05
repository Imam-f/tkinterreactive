# scheduler.py
class Scheduler:
    def __init__(self, flush_fn, tk_root):
        self.flush = flush_fn
        self.root = tk_root
        self.queued = False

    def request(self):
        if self.queued:
            return
        self.queued = True
        self.root.after_idle(self._run)

    def _run(self):
        self.queued = False
        self.flush()

    def cancel(self):
        self.queued = False