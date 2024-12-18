import os
import threading
from tkinter import Tk, Label, Button, filedialog, messagebox
from ePUBModel import ePUBModel

class EPUBView:
    def __init__(self, root):
        # Set up tkinter
        self.root = root
        self.root.title("ePUB Converter")
        self.root.minsize(400, 200)
        
        # Initiate fields
        self.model = ePUBModel()
        self.source_folder = ""

        # Initiate UI elements
        self.select_source_button = Button(root, text="Select Source Folder", command=self.select_source_folder)
        self.select_source_button.grid(row=0, column=0, columnspan=2, pady=20)

        self.source_label = Label(root, text="Source:\nNone")
        self.source_label.grid(row=1, column=0, columnspan=2)

        self.start_button = Button(root, text="Create ePUB", command=self.start_process)
        self.start_button.grid(row=2, column=0, padx=0, pady=30)

        self.quit_button = Button(root, text="Quit", command=self.quit_program)
        self.quit_button.grid(row=2, column=1, padx=0, pady=30)

        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

    def limit_label_length(self, label):
        if len(label) > 32:
            label = label[:32] + '...'
        return label

    # Define 'SELECT SOURCE' button
    def select_source_folder(self):
        self.source_folder = filedialog.askdirectory(title="Select Source Folder")
        if self.source_folder:
            self.source_label.config(text=f"Source:\n{self.limit_label_length(os.path.basename(self.source_folder))}")

    # Define 'START' button
    def start_process(self):
        if not self.source_folder:
            messagebox.showwarning("Input Required", "Please select a source folder.")
        else:
            # Disable buttons
            self.select_source_button.config(state="disabled")
            self.start_button.config(state="disabled")
            
            threading.Thread(target=self.create_epub).start()

    def create_epub(self):
        try:
            # Run the model's create method
            self.model.create_image_epub(self.source_folder)
            messagebox.showinfo("Success", "ePUB created!")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            # Enable buttons
            self.select_source_button.config(state="normal")
            self.start_button.config(state="normal")

    # Define 'QUIT' button
    def quit_program(self):
        self.root.destroy()

# Start
root = Tk()
app = EPUBView(root)
root.mainloop()
