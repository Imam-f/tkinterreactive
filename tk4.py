import tkinter as tk
import time

# Example 1: Using update() in a custom loop
def example_with_update():
    root = tk.Tk()
    root.minsize(560, 380)
    root.title("Custom Loop Example")
    
    label = tk.Label(root, text="Counter: 0")
    label.pack(pady=20)
    
    button = tk.Button(root, text="Click me!")
    button.pack(pady=10)
    
    counter = 0
    
    # Custom loop instead of mainloop()
    for i in range(100):  # Run for 100 iterations
        counter += 1
        label.config(text=f"Counter: {counter}")
        
        # Process pending GUI events
        root.update()
        
        # Do other work
        time.sleep(0.1)
        
        # Check if window was closed
        try:
            root.winfo_exists()
        except tk.TclError:
            break
    
    root.destroy()

# Example 2: Using update_idletasks() for non-blocking updates
def example_with_update_idletasks():
    root = tk.Tk()
    root.minsize(560, 380)
    root.title("Update Idle Tasks Example")
    
    progress_var = tk.StringVar(value="Starting...")
    label = tk.Label(root, textvariable=progress_var)
    label.pack(pady=20)
    
    root.update_idletasks()
    # Simulate some work with GUI updates
    for i in range(20):
        progress_var.set(f"Processing step {i+1}/10...")
        
        # Update only idle tasks (redraws, geometry changes)
        root.update_idletasks()
        
        # Simulate work
        time.sleep(1)
    
    progress_var.set("Complete!")
    root.update_idletasks()
    
    # Keep window open for a moment
    time.sleep(4)
    root.destroy()

# Example 3: One-time GUI creation and immediate destruction
def example_quick_gui():
    root = tk.Tk()
    root.minsize(560, 380)
    root.title("Quick GUI")
    
    # Create widgets
    tk.Label(root, text="This GUI appears briefly").pack(pady=20)
    
    # Force update to show the window
    root.update()
    
    # Do something else
    time.sleep(5)
    
    # Close without mainloop
    root.destroy()

# Example 4: Embedding in another event loop
class CustomEventLoop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.minsize(560, 380)
        self.root.title("Custom Event Loop")
        self.running = True
        
        tk.Label(self.root, text="Embedded in custom loop").pack(pady=20)
        tk.Button(self.root, text="Stop", command=self.stop).pack(pady=10)
        
        # Prevent window from being closed normally
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
    
    def stop(self):
        self.running = False
    
    def run_custom_loop(self):
        while self.running:
            # Process tkinter events
            try:
                self.root.update()
            except tk.TclError:
                break
            
            # Do other custom work here
            time.sleep(0.01)  # Small delay to prevent high CPU usage
        
        self.root.destroy()

# Example usage:
if __name__ == "__main__":
    print("Example 1: Custom loop with update()")
    try:
        example_with_update()
    except Exception:
        pass
    
    print("\nExample 2: Using update_idletasks()")
    try:
        example_with_update_idletasks()
    except Exception:
        pass
    
    print("\nExample 3: Quick GUI without mainloop")
    try:
        example_quick_gui()
    except Exception:
        pass
    
    print("\nExample 4: Custom event loop")
    try:
        custom_loop = CustomEventLoop()
        custom_loop.run_custom_loop()
    except Exception:
        pass
    
    print("All examples completed!")
