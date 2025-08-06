import tkinter as tk
from tkinter import ttk

class ManualTabSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Manual Tab System")
        self.root.geometry("600x400")
        
        # Create button frame for tabs
        self.button_frame = tk.Frame(root, bg="lightgray", height=40)
        self.button_frame.pack(fill="x", padx=5, pady=5)
        self.button_frame.pack_propagate(False)
        
        # Create main content frame
        self.content_frame = tk.Frame(root, bg="white")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create tab buttons
        self.tab1_button = tk.Button(
            self.button_frame,
            text="Tab 1",
            command=self.show_tab1,
            bg="lightblue",
            relief="raised",
            padx=20,
            pady=5
        )
        self.tab1_button.pack(side="left", padx=2, pady=2)
        
        self.tab2_button = tk.Button(
            self.button_frame,
            text="Tab 2",
            command=self.show_tab2,
            bg="lightgray",
            relief="raised",
            padx=20,
            pady=5
        )
        self.tab2_button.pack(side="left", padx=2, pady=2)
        
        self.tab3_button = tk.Button(
            self.button_frame,
            text="Tab 3",
            command=self.show_tab3,
            bg="lightgray",
            relief="raised",
            padx=20,
            pady=5
        )
        self.tab3_button.pack(side="left", padx=2, pady=2)
        
        # Create frames for each tab
        self.create_tab_frames()
        
        # Show first tab by default
        self.current_tab = None
        self.show_tab1()
    
    def create_tab_frames(self):
        # Tab 1 Frame
        self.tab1_frame = tk.Frame(self.content_frame, bg="white")
        tk.Label(self.tab1_frame, text="This is Tab 1", font=("Arial", 16), bg="white").pack(pady=20)
        tk.Label(self.tab1_frame, text="Content for the first tab", bg="white").pack(pady=10)
        
        # Add some widgets to tab 1
        tk.Entry(self.tab1_frame, width=30).pack(pady=10)
        tk.Button(self.tab1_frame, text="Tab 1 Button", bg="lightblue").pack(pady=5)
        
        # Tab 2 Frame
        self.tab2_frame = tk.Frame(self.content_frame, bg="white")
        tk.Label(self.tab2_frame, text="This is Tab 2", font=("Arial", 16), bg="white").pack(pady=20)
        tk.Label(self.tab2_frame, text="Content for the second tab", bg="white").pack(pady=10)
        
        # Add some widgets to tab 2
        tk.Checkbutton(self.tab2_frame, text="Option 1", bg="white").pack(pady=5)
        tk.Checkbutton(self.tab2_frame, text="Option 2", bg="white").pack(pady=5)
        tk.Scale(self.tab2_frame, from_=0, to=100, orient="horizontal").pack(pady=10)
        
        # Tab 3 Frame
        self.tab3_frame = tk.Frame(self.content_frame, bg="white")
        tk.Label(self.tab3_frame, text="This is Tab 3", font=("Arial", 16), bg="white").pack(pady=20)
        tk.Label(self.tab3_frame, text="Content for the third tab", bg="white").pack(pady=10)
        
        # Add some widgets to tab 3
        listbox = tk.Listbox(self.tab3_frame, height=6)
        for i in range(1, 11):
            listbox.insert(tk.END, f"Item {i}")
        listbox.pack(pady=10)
    
    def hide_all_frames(self):
        """Hide all tab frames"""
        for frame in [self.tab1_frame, self.tab2_frame, self.tab3_frame]:
            frame.pack_forget()
    
    def reset_button_styles(self):
        """Reset all buttons to inactive style"""
        for button in [self.tab1_button, self.tab2_button, self.tab3_button]:
            button.config(bg="lightgray", relief="raised")
    
    def show_tab1(self):
        """Show tab 1 and update button styles"""
        if self.current_tab != "tab1":
            self.hide_all_frames()
            self.reset_button_styles()
            
            self.tab1_frame.pack(fill="both", expand=True)
            self.tab1_button.config(bg="lightblue", relief="sunken")
            self.current_tab = "tab1"
    
    def show_tab2(self):
        """Show tab 2 and update button styles"""
        if self.current_tab != "tab2":
            self.hide_all_frames()
            self.reset_button_styles()
            
            self.tab2_frame.pack(fill="both", expand=True)
            self.tab2_button.config(bg="lightgreen", relief="sunken")
            self.current_tab = "tab2"
    
    def show_tab3(self):
        """Show tab 3 and update button styles"""
        if self.current_tab != "tab3":
            self.hide_all_frames()
            self.reset_button_styles()
            
            self.tab3_frame.pack(fill="both", expand=True)
            self.tab3_button.config(bg="lightcoral", relief="sunken")
            self.current_tab = "tab3"

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ManualTabSystem(root)
    root.mainloop()