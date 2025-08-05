# scheduler.py
class Scheduler:
    def __init__(self, flush_fn, tk_root):
        self.flush_fn = flush_fn
        self.root = tk_root
        self.queued = False
        self.deferred = False
        self.pending_job_id = None

    def request(self):
        """Request a render update"""
        if self.deferred:
            # In deferred mode, don't schedule anything
            return
        
        if self.queued:
            return
        
        self.queued = True
        self.pending_job_id = self.root.after_idle(self._run)

    def defer(self):
        """Enter deferred mode - stops all rendering until flush() is called"""
        self.deferred = True
        # Cancel any pending render
        if self.pending_job_id is not None:
            try:
                self.root.after_cancel(self.pending_job_id)
            except Exception:
                pass  # Job might have already executed
            self.pending_job_id = None
        self.queued = False

    def flush(self):
        """Exit deferred mode and immediately execute a render"""
        was_deferred = self.deferred
        self.deferred = False
        
        # Cancel any pending render job
        if self.pending_job_id is not None:
            try:
                self.root.after_cancel(self.pending_job_id)
            except Exception:
                pass  # Job might have already executed
            self.pending_job_id = None
        
        self.queued = False
        
        # If we were in deferred mode or had a pending render, execute now
        if was_deferred or self.queued:
            self.flush_fn()

    def _run(self):
        """Internal method to execute the flush function"""
        self.queued = False
        self.pending_job_id = None
        
        # Don't run if we're in deferred mode
        if self.deferred:
            return
            
        self.flush_fn()

    def cancel(self):
        """Cancel any pending renders and exit deferred mode"""
        self.deferred = False
        self.queued = False
        
        if self.pending_job_id is not None:
            try:
                self.root.after_cancel(self.pending_job_id)
            except Exception:
                pass  # Job might have already executed
            self.pending_job_id = None

    def is_deferred(self):
        """Check if scheduler is in deferred mode"""
        return self.deferred

    def is_queued(self):
        """Check if there's a pending render"""
        return self.queued