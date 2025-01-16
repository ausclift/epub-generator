import os
import threading
import time
import tkinter
from tkinter import Tk, ttk, Label, Button, filedialog, messagebox, font
from ePUBModel import ePUBModel

class EPUBView:
    def __init__(self, root):
        # Set up tkinter
        self.root = root
        self.root.title("ePUB Converter")
        self.root.minsize(400, 200)
        
        # Initiate fields
        self.model = ePUBModel()
        self.model.set_progress_callback(self.update_progress)
        self.source_folder = ""

        # Initiate UI elements
        self.select_source_button = Button(root, text="Source Folder", command=self.select_source_folder)
        self.select_source_button.grid(row=0, column=0, columnspan=2, pady=20)

        self.source = Label(root, text="None")
        self.source.grid(row=1, column=0, columnspan=2)

        self.start_button = Button(root, text="Create ePUB", command=self.start_process)
        self.start_button.grid(row=2, column=0, padx=0, pady=30)

        self.quit_button = Button(root, text="Quit", command=self.quit_program)
        self.quit_button.grid(row=2, column=1, padx=0, pady=30)

        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.progress = tkinter.IntVar()
        self.progress_bar = ttk.Progressbar(variable=self.progress)

    def create_italic_font(self):
        """Create a new font based on the default font but with italic slant."""
        # Retrieve the default font
        default_font = font.nametofont("TkDefaultFont")
    
        # Create a new font based on the default, with italic slant
        italic_font = font.Font(family=default_font.actual("family"),
                                size=default_font.actual("size"),
                                weight=default_font.actual("weight"),
                                slant="italic",
                                underline=default_font.actual("underline"),
                                overstrike=default_font.actual("overstrike"))
    
        return italic_font

    def limit_label_length(self, label):
        if len(label) > 32:
            label = label[:32] + '...'
        return label

    # Define 'SELECT SOURCE' button
    def select_source_folder(self):
        self.source_folder = filedialog.askdirectory(title="Select Source Folder")
        if self.source_folder:
            italic_font = self.create_italic_font()
            self.source.config(text=f"{self.limit_label_length(os.path.basename(self.source_folder))}", font=italic_font)

    # Define 'START' button
    def start_process(self):
        if not self.source_folder:
            messagebox.showwarning("Input Required", "Please select a source folder.")
        else:
            # Disable buttons
            self.select_source_button.config(state="disabled")
            self.start_button.config(state="disabled")
            
            threading.Thread(target=self.create_epub).start()
            
    def update_progress(self, prog):
        self.progress.set(prog)
        
    def create_epub(self):

        try:
            self.progress.set(0)
            self.progress_bar.grid(row=3, column=0, padx=0, columnspan=2)
            # Run the model's create method
            self.model.create_image_epub(self.source_folder)
            self.update_progress(99)
            time.sleep(0.1)
            messagebox.showinfo("Success", "ePUB created!")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            # Enable buttons
            self.select_source_button.config(state="normal")
            self.start_button.config(state="normal")

        self.progress_bar.grid_remove()
        

    # Define 'QUIT' button
    def quit_program(self):
        self.root.destroy()

# Start
root = Tk()
app = EPUBView(root)
root.mainloop()
