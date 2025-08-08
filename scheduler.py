# scheduler.py
class Scheduler:
    def __init__(self, flush_fn, tk_root):
        self.flush_fn = flush_fn
        self.root = tk_root
        self.high_priority_queued = False
        self.low_priority_queued = False
        self.deferred = False
        self.pending_high_job_id = None
        self.pending_low_job_id = None
        
        # Timing configuration
        self.high_priority_delay = 0  # Immediate (after_idle)
        self.low_priority_delay = 16  # ~60fps (16ms delay)

    def request(self, priority="low"):
        """Request a render update with specified priority
        
        Args:
            priority: "high" for immediate response, "low" for batched updates
        """
        if priority == "high":
            self._request_high_priority()
            return
        
        if self.deferred:
            # In deferred mode, don't schedule anything
            return
        
        self._request_low_priority()

    def _request_high_priority(self):
        """Request immediate high priority render"""
        if self.high_priority_queued:
            return
        
        # Cancel any pending low priority render since high priority takes precedence
        if self.pending_low_job_id is not None:
            try:
                self.root.after_cancel(self.pending_low_job_id)
            except Exception:
                pass
            self.pending_low_job_id = None
            self.low_priority_queued = False
        
        self.high_priority_queued = True
        # Use after_idle for immediate execution
        self.pending_high_job_id = self.root.after_idle(self._run_high_priority)

    def _request_low_priority(self):
        """Request batched low priority render"""
        if self.low_priority_queued or self.high_priority_queued:
            return  # Don't queue if already queued or high priority is pending
        
        self.low_priority_queued = True
        # Use after with delay for batched execution
        self.pending_low_job_id = self.root.after(
            self.low_priority_delay, 
            self._run_low_priority
        )

    def request_immediate(self):
        """Convenience method for high priority requests"""
        # self.request("high")
        global pump
        import sys

        pump = sys.modules["__main__"].pump
        app = pump.__closure__[0].cell_contents
        app.send({"type": "immediate"})

    def request_batched(self):
        """Convenience method for low priority requests"""
        self.request("low")

    def defer(self):
        """Enter deferred mode - stops all rendering until flush() is called"""
        self.deferred = True
        
        # Cancel any pending renders
        if self.pending_high_job_id is not None:
            try:
                self.root.after_cancel(self.pending_high_job_id)
            except Exception:
                pass
            self.pending_high_job_id = None
        
        if self.pending_low_job_id is not None:
            try:
                self.root.after_cancel(self.pending_low_job_id)
            except Exception:
                pass
            self.pending_low_job_id = None
        
        self.high_priority_queued = False
        self.low_priority_queued = False

    def flush(self):
        """Exit deferred mode and immediately execute a render"""
        was_deferred = self.deferred
        had_pending = self.high_priority_queued or self.low_priority_queued
        
        self.deferred = False
        
        # Cancel any pending render jobs
        if self.pending_high_job_id is not None:
            try:
                self.root.after_cancel(self.pending_high_job_id)
            except Exception:
                pass
            self.pending_high_job_id = None
        
        if self.pending_low_job_id is not None:
            try:
                self.root.after_cancel(self.pending_low_job_id)
            except Exception:
                pass
            self.pending_low_job_id = None
        
        self.high_priority_queued = False
        self.low_priority_queued = False
        
        # If we were in deferred mode or had pending renders, execute now
        if was_deferred or had_pending:
            self.flush_fn()

    def _run_high_priority(self):
        """Internal method to execute high priority flush"""
        self.high_priority_queued = False
        self.pending_high_job_id = None
        
        # Don't run if we're in deferred mode
        if self.deferred:
            return
            
        self.flush_fn()

    def _run_low_priority(self):
        """Internal method to execute low priority flush"""
        self.low_priority_queued = False
        self.pending_low_job_id = None
        
        # Don't run if we're in deferred mode
        if self.deferred:
            return
            
        self.flush_fn()

    def cancel(self):
        """Cancel any pending renders and exit deferred mode"""
        self.deferred = False
        self.high_priority_queued = False
        self.low_priority_queued = False
        
        if self.pending_high_job_id is not None:
            try:
                self.root.after_cancel(self.pending_high_job_id)
            except Exception:
                pass
            self.pending_high_job_id = None
        
        if self.pending_low_job_id is not None:
            try:
                self.root.after_cancel(self.pending_low_job_id)
            except Exception:
                pass
            self.pending_low_job_id = None

    def is_deferred(self):
        """Check if scheduler is in deferred mode"""
        return self.deferred

    def is_queued(self, priority=None):
        """Check if there's a pending render
        
        Args:
            priority: "high", "low", or None for any priority
        """
        if priority == "high":
            return self.high_priority_queued
        elif priority == "low":
            return self.low_priority_queued
        else:
            return self.high_priority_queued or self.low_priority_queued

    def set_low_priority_delay(self, delay_ms):
        """Configure the delay for low priority renders (default: 16ms)"""
        self.low_priority_delay = max(0, delay_ms)