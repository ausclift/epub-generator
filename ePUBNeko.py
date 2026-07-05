import os, threading, zipfile, shutil, uuid, json
from tkinter import Tk, ttk, Label, Button, filedialog, messagebox, font, Checkbutton, Radiobutton, StringVar, IntVar, Frame
from datetime import datetime, timezone
from PIL import Image
from natsort import natsorted
from pathlib import Path
CONFIG_PATH = os.path.expanduser("~/.nekoconfig.json")

class ePUBModel:

    def __init__(self):
        self.source_folder = ''
        self.progress_callback = None

    def set_progress_callback(self, function):
        """Create callback function to send progress updates."""
        self.progress_callback = function

    def collect_images(self, source_folder):
        """Collect images in the source folder."""
        source_path = Path(source_folder)

        # valid image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

        original_image_files = sorted(
            file for file in source_path.rglob("*")
                if file.suffix.lower() in image_extensions
        )
        original_image_files = natsorted([str(file) for file in original_image_files])
        if not original_image_files:
            raise ValueError(f"No images found in '{source_folder}'.")
        
        return original_image_files

    def create_epub_structure(self):
        """Define ePUB Structure by creating the required folders."""
        os.makedirs('EPUB/META-INF', exist_ok=True)
        os.makedirs('EPUB/OEBPS/images', exist_ok=True)
        os.makedirs('EPUB/OEBPS/html', exist_ok=True)

    def write_mimetype(self):
        """Write the `mimetype` file that defines the folder structure as an ePUB."""
        with open('EPUB/mimetype', 'w') as f:
            f.write('application/epub+zip')

    def write_container_xml(self):
        """Write the `container.xml` file."""
        container_content = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        with open('EPUB/META-INF/container.xml', 'w', encoding='utf-8') as f:
            f.write(container_content)

    def copy_images(self, image_files, read_order, loss_mode):
        """Copy and rename source images into `images` directory."""
        ltr = read_order.get()
        mode = loss_mode.get()

        cover_extension = ''

        for i, image_path in enumerate(image_files):
            image_filename = f'image-{i+1:04d}'
            _, ext = os.path.splitext(image_path)
            ext = ext.lower()

            if ext not in {'.jpg', '.jpeg', '.png', '.webp'}:
                continue

            # determine output format
            if mode == "lossless":
                out_extension = ".png"
            else:
                if ext in {'.jpg', '.jpeg'}:
                    out_extension = ".jpeg"
                else:
                    out_extension = ".png"

            with Image.open(image_path) as img:

                if ext == ".webp":
                    img = img.convert("RGBA")
                else:
                    img = img.copy()

                width, height = img.size

                def save_img(im, path):
                    if mode == "ultra" and path.endswith(".jpeg"):
                        im.save(path, quality=90, optimize=True)
                    else:
                        im.save(path)

                # portrait / single page
                if width <= height:
                    out_path = f'EPUB/OEBPS/images/{image_filename}{out_extension}'
                    save_img(img, out_path)

                    if i == 0:
                        cover_path = f'EPUB/OEBPS/images/cover{out_extension}'
                        save_img(img, cover_path)
                        cover_extension = out_extension

                # landscape / spread
                else:
                    mid_x = width // 2

                    left_label = 'B' if ltr == 0 else 'A'
                    right_label = 'A' if ltr == 0 else 'B'

                    left_path = f"EPUB/OEBPS/images/{image_filename}-{left_label}{out_extension}"
                    right_path = f"EPUB/OEBPS/images/{image_filename}-{right_label}{out_extension}"

                    if i != 0:
                        img.crop((0, 0, mid_x, height)).save(left_path)
                        img.crop((mid_x + 1, 0, width, height)).save(right_path)

                    else:
                        if ltr == 0:
                            left_crop = img.crop((0, 0, mid_x, height))
                            save_img(left_crop, left_path)
                            save_img(left_crop, f'EPUB/OEBPS/images/cover{out_extension}')
                        else:
                            right_crop = img.crop((mid_x + 1, 0, width, height))
                            save_img(right_crop, right_path)
                            save_img(right_crop, f'EPUB/OEBPS/images/cover{out_extension}')

                        cover_extension = out_extension

        return cover_extension[1:] # strip dot from extension for media-type

    def write_content_opf(self, image_files, book_uuid, cover_extension, read_order, folder_name):
        """Write the `content.opf` file including page-progression-direction metadata."""
        book_title = Path(folder_name).name

        time = datetime.now(timezone.utc).isoformat(timespec='seconds')
        time = time.replace('+00:00', 'Z')

        manifest_items = '\n'.join([
            f'    <item id="img{i+1}" href="{image_files[i][11:]}" media-type="image/{os.path.splitext(image_files[i])[1][1:]}" />\n'
            f'    <item id="xhtml{i+1}" href="html/image-{i+1:04d}.xhtml" media-type="application/xhtml+xml"/>'
            for i in range(len(image_files))
        ])

        spine_items = '\n'.join([
            f'    <itemref idref="xhtml{i+1}"/>'
            for i in range(len(image_files))
        ])

        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rendition="http://www.idpf.org/2013/rendition">
    <dc:title>{book_title}</dc:title>
    <dc:creator>ePUB Neko</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">{book_uuid}</dc:identifier>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">both</meta>
    <meta property="dcterms:modified">{time}</meta>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="html/style.css" media-type="text/css"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="cover-image" href="images/cover.{cover_extension}" media-type="image/{cover_extension}" properties="cover-image"/>
{manifest_items}
  </manifest>
  <spine toc="ncx" page-progression-direction="{'rtl' if read_order.get() == 0 else 'ltr'}">
{spine_items}
  </spine>
</package>'''
        
        with open('EPUB/OEBPS/content.opf', 'w', encoding='utf-8') as f:
            f.write(content_opf)

    def write_toc_ncx(self, image_files, book_uuid):
        """Write the `toc.ncx` file."""
        nav_points = '\n'.join([
            f'''    <navPoint id="navPoint-{i+1}" playOrder="{i+1}">
      <navLabel><text>image{i+1}</text></navLabel>
      <content src="html/image-{i+1:04d}.xhtml"/>
    </navPoint>''' for i in range(len(image_files))
        ])

        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_uuid}"/>
  </head>
  <docTitle><text>ePUB</text></docTitle>
  <navMap>
{nav_points}
  </navMap>
</ncx>'''
        
        with open('EPUB/OEBPS/toc.ncx', 'w', encoding='utf-8') as f:
            f.write(toc_ncx)

    def write_nav_xhtml(self, image_files):
        """Write the `nav.xhtml file.`"""
        nav_items = '\n'.join([
            f'        <li><a href="html/image-{i+1:04d}.xhtml">Image {i+1}</a></li>'
            for i in range(len(image_files))
        ])

        nav_xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>Navigation</title>
  </head>
  <body>
    <nav epub:type="toc" id="toc">
      <h1>Table of Contents</h1>
      <ol>
{nav_items}
      </ol>
    </nav>
  </body>
</html>'''
        
        with open('EPUB/OEBPS/nav.xhtml', 'w', encoding='utf-8') as f:
            f.write(nav_xhtml)

    def write_css_file(self):
        """Write the `CSS` file."""
        css_path = 'EPUB/OEBPS/html/style.css'
        css_content = '''@page {
  margin: 0;
}

body {
  display: block;
  margin: 0;
  padding: 0;
}'''
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)

    def calculate_max_dimensions(self, image_files):
        """Calculate maximum width and height of the images."""
        max_width = 0
        max_height = 0
        for image_path in image_files:
            with Image.open(image_path) as img:
                width, height = img.size
                max_width = max(max_width, width)
                max_height = max(max_height, height)

        return max_width, max_height

    def get_alignment(self, index, direction):
        """Determine alignment based on reading direction and page index."""
        even_page = index % 2 == 0
        return 'right' if (even_page and direction.get() == 0) or (not even_page and direction.get() == 1) else 'left'

    def create_html_file(self, image_index, image_path, width, height, max_width, max_height, alignment, output_dir):
        """Create an XHTML file for the given image."""
        image_filename = os.path.basename(image_path)

        html_content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>image{image_index + 1}</title>
    <link href="style.css" type="text/css" rel="stylesheet"/>
    <meta name="viewport" content="width={max_width}, height={max_height}"/>
  </head>
  <body>
    <div style="text-align:{alignment}; top:0.0%;">
      <img width="{width}" height="{height}" src="../images/{image_filename}" alt="{image_filename}"/>
    </div>
  </body>
</html>'''
        output_path = os.path.join(output_dir, f'image-{image_index + 1:04d}.xhtml')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def add_html(self, image_files, direction):
        """Generate the HTML files for all images."""
        output_dir = 'EPUB/OEBPS/html'

        # get max dimensions of all images
        max_width, max_height = self.calculate_max_dimensions(image_files)

        # create HTML file for each image
        for i, image_path in enumerate(image_files):
            with Image.open(image_path) as img:
                width, height = img.size

            # get image display size
            width, height = self.get_optimal_image_size(width, height, max_width, max_height)

            # get image alignment
            alignment = self.get_alignment(i, direction)

            # generate HTML file
            self.create_html_file(i, image_path, width, height, max_width, max_height, alignment, output_dir)

    def create_epub(self, epub_name):
        """Zip into ePUB file while leaving `mimetype` uncompressed."""
        with zipfile.ZipFile(f'{epub_name}.epub', 'w') as epub:
            epub.write('EPUB/mimetype', 'mimetype', compress_type=zipfile.ZIP_STORED)
            for root, _, files in os.walk('EPUB'):
                for file in files:
                    filepath = os.path.join(root, file)
                    if filepath.endswith('mimetype'):
                        continue
                    epub.write(filepath, filepath.replace('EPUB/', ''), compress_type=zipfile.ZIP_DEFLATED)

    def get_optimal_image_size(self, img_width, img_height, view_width, view_height):
        """Fit an image to view while maintaining aspect ratio."""
        # calculate the aspect ratios
        img_aspect_ratio = img_width / img_height
        box_aspect_ratio = view_width / view_height

        # image is wider than view
        if img_aspect_ratio > box_aspect_ratio:
            new_width = view_width
            new_height = int(view_width / img_aspect_ratio)

        # image is taller than or equal to view
        else:
            new_height = view_height
            new_width = int(view_height * img_aspect_ratio)

        return new_width, new_height

    def create_image_epub(self, source_folder, loss_mode, read_order):
        """Initiate ePUB creation and track progress."""
        book_uuid = f'urn:uuid:{str(uuid.uuid4())}'
        self.create_epub_structure()
        self.progress_callback(5)

        self.write_mimetype()
        self.write_container_xml()
        original_image_files = self.collect_images(source_folder)
        self.progress_callback(10)

        cover_extension = self.copy_images(original_image_files, read_order, loss_mode)
        self.progress_callback(50)

        epub_images_path = 'EPUB/OEBPS/images'
        image_files = self.collect_images(epub_images_path)
        self.write_content_opf(image_files[1:], book_uuid, cover_extension, read_order, source_folder)
        self.write_toc_ncx(image_files[1:], book_uuid)
        self.write_nav_xhtml(image_files[1:])
        self.write_css_file()
        self.progress_callback(55)

        self.add_html(image_files[1:], read_order)
        self.progress_callback(60)

        self.create_epub(source_folder)
        self.progress_callback(99)

        # removes temporary files - comment-out for troubleshooting
        shutil.rmtree('EPUB')


class EPUBView:

    def __init__(self, root):
        self.root = root
        root.title('ePUB Neko')
        root.minsize(400, 300)
        root.grid_columnconfigure(0, weight=1, uniform="cols")
        root.grid_columnconfigure(1, weight=1, uniform="cols")
        root.grid_columnconfigure(2, weight=1, uniform="cols")

        # set model and create callback function by passing method to the model
        self.model = ePUBModel()
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

    def enable_wigets(self, enabled: bool):
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
        self.source_folder = filedialog.askdirectory(title='Select Source Folder', initialdir=initial_dir)

        if self.source_folder:
            # persist last accessed folder
            self.save_last_folder()
            
            self.source.config(text=f'{self.limit_label_length(os.path.basename(self.source_folder))}', font=self.italic_font())

        root.focus_force()

    def start_process(self):
        """Define `CREATE ePUB` button."""
        if not self.source_folder:
            messagebox.showwarning('Input Required', 'Please select a source folder.')

        else:
            self.enable_wigets(False)

            threading.Thread(target=self.create_epub).start()
            
    def update_progress(self, prog):
        """Update progress bar. Called by the model."""
        self.progress.set(prog)
        
    def create_epub(self):
        """Create ePUB file by invoking the model."""
        try:
            self.progress_bar.grid(row=6, column=0, padx=20, columnspan=3, sticky="ew")

            self.model.create_image_epub(self.source_folder, self.loss_mode, self.read_order)

            messagebox.showinfo('Success', 'ePUB created!')

        except Exception as e:
            messagebox.showerror('Error', str(e))

        finally:
            self.progress.set(0)
            self.root.update_idletasks()
            self.progress_bar.grid_forget()
            self.root.event_generate("<Expose>")
            self.enable_wigets(True)
            
        root.focus_force()

# run application
root = Tk()
EPUBView(root)
root.mainloop()