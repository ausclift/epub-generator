import os, threading, json
from tkinter import ttk, Frame, Label, Button, Checkbutton, Radiobutton, filedialog, messagebox, font, StringVar, IntVar
CONFIG_PATH = os.path.expanduser("~/.nekoconfig.json")

class View:

    def __init__(self, root, model):
        self.root = root
        self.model = model
        root.title('ePUB Neko')
        root.minsize(400, 300)
        root.grid_columnconfigure(0, weight=1, uniform="cols")
        root.grid_columnconfigure(1, weight=1, uniform="cols")
        root.grid_columnconfigure(2, weight=1, uniform="cols")

        # create callback function by passing method to the model
        self.model.set_progress_callback(self.update_progress)

        # source folder button
        self.source_folder = ''
        self.select_source_button = Button(root, text='Source Folder', command=self.select_source_folder)
        self.select_source_button.grid(row=0, column=0, columnspan=3, pady=(10,10))

        # source folder label
        self.source = Label(root, text='None')
        self.source.grid(row=1, column=0, columnspan=3)

        # loss mode title
        self.loss_title = Label(root, text='Quality')
        self.loss_title.grid(row=2, column=0, pady=(20, 0))

        # loss mode selector
        self.loss_mode = StringVar(value="ultra")
        self.loss_frame = Frame(root)
        self.loss_frame.grid(row=3, column=0)
        self.loss_high = Radiobutton(self.loss_frame, text="High", variable=self.loss_mode, value="high", command=self.update_loss_text)
        self.loss_ultra = Radiobutton(self.loss_frame, text="Ultra", variable=self.loss_mode, value="ultra", command=self.update_loss_text)
        self.loss_lossless = Radiobutton(self.loss_frame, text="Lossless", variable=self.loss_mode, value="lossless", command=self.update_loss_text)
        self.loss_high.pack(anchor="w")
        self.loss_ultra.pack(anchor="w")
        self.loss_lossless.pack(anchor="w")

        # loss mode label
        self.loss_label = StringVar()
        self.loss_desc = Label(root, font=self.italic_font(0.8), textvariable=self.loss_label)
        self.loss_desc.grid(row=4, column=0)
        self.update_loss_text()

        # reading direction title
        self.direction_title = Label(root, text='Layout')
        self.direction_title.grid(row=2, column=1, pady=(20, 0))

        # reading direction checkbox 
        self.read_order = IntVar()
        self.read_order_checkbox = Checkbutton(root, text='Manga', variable=self.read_order, offvalue=1, onvalue=0, command=self.update_direction_text)
        self.read_order_checkbox.grid(row=3, column=1)
        self.read_order_checkbox.select()

        # reading direction label
        self.direction_label = StringVar()
        self.direction_desc = Label(root, font=self.italic_font(0.8), textvariable=self.direction_label)
        self.direction_desc.grid(row=4, column=1)
        self.update_direction_text()

        # placeholder title
        self.loss_title = Label(root, text='Placeholder')
        self.loss_title.grid(row=2, column=2, pady=(20, 0))

        # placeholder label
        self.loss_desc = Label(root, text='placeholder', font=self.italic_font(0.8))
        self.loss_desc.grid(row=4, column=2)

        # create ePUB button
        self.start_button = Button(root, text='Create ePUB', command=self.start_process)
        self.start_button.grid(row=5, column=0, columnspan=3, pady=(20,0))

        # progress bar
        self.progress = IntVar()
        self.progress_bar = ttk.Progressbar(variable=self.progress)

        root.focus_force()

    def toggle_widget_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.loss_high.config(state=state)
        self.loss_ultra.config(state=state)
        self.loss_lossless.config(state=state)
        self.select_source_button.config(state=state)
        self.start_button.config(state=state)
        self.read_order_checkbox.config(state=state)
    
    def save_last_folder(self):
        config = {"last_folder": os.path.dirname(self.source_folder)}
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)

    def load_last_folder(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                return config.get("last_folder", "")
            except Exception:
                return ""
        return ""
    
    def update_loss_text(self):
        mode = self.loss_mode.get()
        if mode == "high":
            self.loss_label.set("75% quality JPGs")
        elif mode == "ultra":
            self.loss_label.set("90% quality JPGs")
        elif mode == "lossless":
            self.loss_label.set("convert to PNGs")

    def update_direction_text(self):
        """Update checkbutton label based on the current reading direction."""
        if self.read_order.get() == 0:
            self.direction_label.set('right-to-left')
        else:
            self.direction_label.set('left-to-right')
    
    def italic_font(self, size=1.0):
        """Create a new font based on the default font but with italic slant."""
        default_font = font.nametofont('TkDefaultFont')
        italic_font = font.Font(family=default_font.actual('family'),
                                size=int(default_font.actual('size') * size),
                                weight=default_font.actual('weight'),
                                slant='italic',
                                underline=default_font.actual('underline'),
                                overstrike=default_font.actual('overstrike'))
        return italic_font

    def limit_label_length(self, label):
        """Limit length of the label to 48 characters."""
        if len(label) > 48:
            label = label[:48] + '...'

        return label

    def select_source_folder(self):
        """Define `SOURCE FOLDER` button."""
        initial_dir = self.load_last_folder() or os.path.expanduser("~")
        selected_folder = filedialog.askdirectory(title="Select Source Folder", initialdir=initial_dir)

        if selected_folder:
            self.source_folder = selected_folder

            # persist last accessed folder
            self.save_last_folder()

            self.source.config(text=self.limit_label_length(os.path.basename(self.source_folder)), font=self.italic_font())

        self.root.focus_force()

    def start_process(self):
        """Define `CREATE ePUB` button."""
        if not self.source_folder:
            messagebox.showwarning('Input Required', 'Please select a source folder.')

        else:
            self.toggle_widget_state(False)

            threading.Thread(target=self.create_epub).start()
            
    def update_progress(self, prog):
        """Update progress bar. Called by the model."""
        self.progress.set(prog)
        
    def create_epub(self):
        """Create ePUB file by invoking the model."""
        try:
            self.progress_bar.grid(row=6, column=0, padx=20, columnspan=3, sticky="ew")

            self.model.create_image_epub(self.source_folder, self.loss_mode.get(), self.read_order.get())

            messagebox.showinfo('Success', 'ePUB created!')

        except Exception as e:
            messagebox.showerror('Error', str(e))

        finally:
            self.progress.set(0)
            self.root.update_idletasks()
            self.progress_bar.grid_forget()
            self.root.event_generate("<Expose>")
            self.toggle_widget_state(True)
            
        self.root.focus_force()
