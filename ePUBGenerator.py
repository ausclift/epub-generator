import os, threading, time, zipfile, shutil, uuid, tkinter
from tkinter import Tk, ttk, Label, Button, filedialog, messagebox, font, Checkbutton, Text
from datetime import datetime, timezone
from PIL import Image
from natsort import natsorted
from pathlib import Path

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

    def copy_images(self, image_files, reading_direction):
        """Copy and rename source images into `images` directory."""
        ltr = reading_direction.get()
        cover_extension = ''
        for i, image_path in enumerate(image_files):

            image_filename = f'image-{i+1:04d}'
            _, file_extension = os.path.splitext(image_path)
            if file_extension.lower() in {'.jpg', '.jpeg'}:
                file_extension = '.jpeg'
            elif file_extension.lower() == '.png':
                file_extension = '.png'
            elif file_extension.lower() == '.webp':
                file_extension = '.webp'

            with Image.open(image_path) as img:
                img = img.copy()
                width, height = img.size
        
            if width <= height:
                shutil.copy(image_path, f'EPUB/OEBPS/images/{image_filename}{file_extension}')

                # save extension of cover
                if i == 0:
                    shutil.copy(image_path, 'EPUB/OEBPS/images/cover{file_extension}')
                    cover_extension = file_extension
                
            # case for spreads
            else:
                mid_x = width // 2
                
                left_path = f'EPUB/OEBPS/images/{image_filename}-{'B' if ltr == 0 else 'A'}{file_extension}'
                right_path = f'EPUB/OEBPS/images/{image_filename}-{'A' if ltr == 0 else 'B'}{file_extension}'

                if i != 0:
                    image_left = img.crop((0, 0, mid_x, height))
                    image_left.save(left_path)
                    image_right = img.crop((mid_x+1, 0, width, height))
                    image_right.save(right_path)

                # case if spread is first image
                else:
                    # manga style (right-to-left)
                    if ltr == 0:
                        image_left = img.crop((0, 0, mid_x, height))
                        image_left.save(left_path)
                        shutil.copy(left_path, f"EPUB/OEBPS/images/cover{file_extension}")
                        cover_extension = file_extension

                    # comic style (left-to-right)
                    else:
                        image_right = img.crop((mid_x+1, 0, width, height))
                        image_right.save(right_path)
                        shutil.copy(right_path, f'EPUB/OEBPS/images/cover{file_extension}')
                        cover_extension = file_extension

        return cover_extension[1:]

    def write_content_opf(self, image_files, book_uuid, cover_extension, reading_direction):
        """Write the `content.opf` file including page-progression-direction metadata."""
        modified_time = datetime.now(timezone.utc).isoformat(timespec='seconds')
        modified_time = modified_time.replace('+00:00', 'Z')

        manifest_items = '\n'.join([
            f'    <item id="img{i+1}" href="{image_files[i][11:]}" media-type="image/{os.path.splitext(image_files[i])[1][1:]}" />\n'
            f'    <item id="html{i+1}" href="html/image-{i+1:04d}.html" media-type="application/xhtml+xml"/>'
            for i in range(len(image_files))
        ])

        spine_items = '\n'.join([
            f'    <itemref idref="html{i+1}"/>'
            for i in range(len(image_files))
        ])

        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rendition="http://www.idpf.org/2013/rendition">
    <dc:title>ePUB</dc:title>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">{book_uuid}</dc:identifier>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">portrait</meta>
    <meta property="dcterms:modified">{modified_time}</meta>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="html/style.css" media-type="text/css"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="cover-image" href="images/cover.{cover_extension}" media-type="image/{cover_extension}" properties="cover-image"/>
{manifest_items}
  </manifest>
  <spine toc="ncx" page-progression-direction="{'rtl' if reading_direction.get() == 0 else 'ltr'}">
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
      <content src="html/image-{i+1:04d}.html"/>
    </navPoint>''' for i in range(len(image_files))
        ])

        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
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
            f'        <li><a href="html/image-{i+1:04d}.html">Image {i+1}</a></li>'
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

    def add_html(self, image_files):
        """Write the `style.css` file and create an XHTML file for each image."""
        css = '''@page {
  margin: 0;
}

body {
  display: block;
  margin: 0;
  padding: 0;
}'''

        with open('EPUB/OEBPS/html/style.css', 'w', encoding='utf-8') as f:
            f.write(css)
        
        for i, image_path in enumerate(image_files):
            image_filename = os.path.basename(image_path)
            with Image.open(image_path) as img:
                width, height = img.size

            html_content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>image{i+1}</title>
    <link href="style.css" type="text/css" rel="stylesheet"/>
    <meta name="viewport" content="width={width}, height={height}"/>
  </head>
  <body>
    <div style="text-align:center;top:0.0%;">
    <img width="{width}" height="{height}" src="../images/{image_filename}" alt="{image_filename}"/>
    </div>
  </body>
</html>'''
            with open(f'EPUB/OEBPS/html/image-{i+1:04d}.html', 'w', encoding='utf-8') as f:
                f.write(html_content)

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

    def create_image_epub(self, source_folder, reading_direction):
        """Initiate ePUB creation and track progress."""
        book_uuid = f'urn:uuid:{str(uuid.uuid4())}'

        self.create_epub_structure()
        self.progress_callback(5)

        self.write_mimetype()
        self.write_container_xml()
        original_image_files = self.collect_images(source_folder)
        self.progress_callback(10)

        cover_extension = self.copy_images(original_image_files, reading_direction)
        self.progress_callback(50)

        epub_images_path = 'EPUB/OEBPS/images'
        image_files = self.collect_images(epub_images_path)
        self.write_content_opf(image_files[1:], book_uuid, cover_extension, reading_direction)
        self.write_toc_ncx(image_files[1:], book_uuid)
        self.write_nav_xhtml(image_files[1:])
        self.progress_callback(55)

        self.add_html(image_files[1:])
        self.progress_callback(60)

        self.create_epub(source_folder)
        self.progress_callback(99)

        # removes temporary files - comment-out for troubleshooting
        shutil.rmtree('EPUB')


class EPUBView:
    def __init__(self, root):
        self.root = root
        self.root.title('ePUB Converter')
        self.root.minsize(400, 200)
        
        self.model = ePUBModel()

        # create callback function by passing view method to the model
        self.model.set_progress_callback(self.update_progress)

        self.source_folder = ''

        # initiate UI widgets
        self.select_source_button = Button(root, text="Source Folder", command=self.select_source_folder)
        self.select_source_button.grid(row=0, column=0, columnspan=3, pady=(20,10))

        self.source = Label(root, text="None")
        self.source.grid(row=1, column=0, columnspan=3)

        self.start_button = Button(root, text="Create ePUB", command=self.start_process)
        self.start_button.grid(row=2, column=1, pady=(40,0))

        self.quit_button = Button(root, text="Quit", command=self.quit_program)
        self.quit_button.grid(row=2, column=2, pady=(40,0))

        # reading direction variable used in 
        self.reading_direction = tkinter.IntVar()
        self.change_reading_direction = Checkbutton(root, text="Manga", variable=self.reading_direction,
                                                    offvalue=1, onvalue=0, command=self.update_checkbutton_text)
        self.change_reading_direction.grid(row=2, column=0, pady=(40,0))
        self.change_reading_direction.select()

        self.desc_text = tkinter.StringVar()
        self.checkbutton_desc = Label(root, font=self.create_desc_font(), textvariable=self.desc_text)
        self.checkbutton_desc.grid(row=3, column=0)
        self.update_checkbutton_text()
        
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)

        self.progress = tkinter.IntVar()
        self.progress_bar = ttk.Progressbar(variable=self.progress)

    def update_checkbutton_text(self):
        if self.reading_direction.get() == 0:
            self.desc_text.set("right-to-left")
        else:
            self.desc_text.set("left-to-right")

    def create_italic_font(self):
        """Create a new font based on the default font but with italic slant."""
        # Retrieve the default font
        default_font = font.nametofont("TkDefaultFont")
        italic_font = font.Font(family=default_font.actual("family"),
                                size=default_font.actual("size"),
                                weight=default_font.actual("weight"),
                                slant="italic",
                                underline=default_font.actual("underline"),
                                overstrike=default_font.actual("overstrike"))
        return italic_font

    def create_desc_font(self):
        """Create a new font based on the default font but smol."""
        # Retrieve the default font
        default_font = font.nametofont("TkDefaultFont")
        smol_font = font.Font(family=default_font.actual("family"),
                                size=int(default_font.actual("size") // 1.2),
                                weight=default_font.actual("weight"),
                                slant="italic",
                                underline=default_font.actual("underline"),
                                overstrike=default_font.actual("overstrike"))
        return smol_font

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
            # Disable buttons (reenabled in 'create_epub()')
            self.select_source_button.config(state="disabled")
            self.start_button.config(state="disabled")
            self.change_reading_direction.config(state="disabled")

            threading.Thread(target=self.create_epub).start()
            
    def update_progress(self, prog):
        self.progress.set(prog)
        
    def create_epub(self):

        try:
            self.progress.set(0)
            self.progress_bar.grid(row=3, column=0, padx=0, columnspan=2)
            # Run the model's create method
            self.model.create_image_epub(self.source_folder, self.reading_direction)
            self.update_progress(99)
            # Sleep allows progress bar to funtion properly
            time.sleep(0.1)
            messagebox.showinfo("Success", "ePUB created!")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            # Enable buttons (disabled in 'start_process()')
            self.select_source_button.config(state="normal")
            self.start_button.config(state="normal")
            self.change_reading_direction.config(state="normal")

        self.progress_bar.grid_remove()
        

    # Define 'QUIT' button
    def quit_program(self):
        self.root.destroy()


# Start
root = Tk()
app = EPUBView(root)
root.mainloop()