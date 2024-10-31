import os
import zipfile
import shutil
import uuid
from datetime import datetime
from glob import glob
from PIL import Image
from natsort import natsorted
from tkinter import Tk, Label, Button, filedialog, messagebox
from pathlib import Path

# Collect all images in the source folder
def collect_images(source_folder):
    source_path = Path(source_folder)
    
    original_image_files = sorted(source_path.glob("*.jpg")) + \
                           sorted(source_path.glob("*.jpeg")) + \
                           sorted(source_path.glob("*.png")) + \
                           sorted(source_path.glob("*.JPG")) + \
                           sorted(source_path.glob("*.JPEG")) + \
                           sorted(source_path.glob("*.PNG"))
    
    original_image_files = natsorted([str(file) for file in original_image_files])
    
    if not original_image_files:
        raise ValueError(f"No images found in source: {source_folder}.")
    
    return original_image_files

# Define ePUB structure
def create_epub_structure():
    os.makedirs("EPUB/META-INF", exist_ok=True)
    os.makedirs("EPUB/OEBPS/images", exist_ok=True)
    os.makedirs("EPUB/OEBPS/html", exist_ok=True)

# Write the `mimetype` file
def write_mimetype():
    with open("EPUB/mimetype", "w") as f:
        f.write("application/epub+zip")

# Write the `container.xml` file
def write_container_xml():
    container_content = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
    with open("EPUB/META-INF/container.xml", "w", encoding="utf-8") as f:
        f.write(container_content)

# Duplicate/rename source images into 'images' directory
def copy_images(image_files):
    cover_extension = ""
    for i, image_path in enumerate(image_files):

        image_filename = f"image-{i+1:04d}"
        _, file_extension = os.path.splitext(image_path)
        if file_extension.lower() in {".jpg", ".jpeg"}:
            file_extension = ".jpeg"
        if file_extension.lower() == ".png":
            file_extension = ".png"

        with Image.open(image_path) as img:
            img = img.copy()
            width, height = img.size
        
        # Case for spreads
        if width > height:
            mid_x = width // 2
            
            image_left = img.crop((0, 0, mid_x, height))
            left_path = f"EPUB/OEBPS/images/{image_filename}-B{file_extension}"
            image_left.save(left_path)

            if i != 0:
                # Right side
                image_right = img.crop((mid_x+1, 0, width, height))
                right_path = f"EPUB/OEBPS/images/{image_filename}-A{file_extension}"
                image_right.save(right_path)

            else:
                shutil.copy(left_path, f"EPUB/OEBPS/images/cover{file_extension}")
                cover_extension = file_extension
        
        # Case for non-spreads
        else:
            shutil.copy(image_path, f"EPUB/OEBPS/images/{image_filename}{file_extension}")

            if i == 0:
                shutil.copy(image_path, f"EPUB/OEBPS/images/cover{file_extension}")
                cover_extension = file_extension

    return cover_extension[1:]

# Write the `content.opf` file with manga mode metadata
def write_content_opf(image_files, book_uuid, cover_extension):
    modified_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    manifest_items = "\n".join([
        f'    <item id="img{i+1}" href="{image_files[i][11:]}" media-type="image/{os.path.splitext(image_files[i])[1][1:]}" />\n'
        f'    <item id="html{i+1}" href="html/image-{i+1:04d}.html" media-type="application/xhtml+xml"/>'
        for i in range(len(image_files))
    ])
    
    spine_items = "\n".join([
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
  <spine toc="ncx" page-progression-direction="rtl">
{spine_items}
  </spine>
</package>'''
    with open("EPUB/OEBPS/content.opf", "w", encoding="utf-8") as f:
        f.write(content_opf)

# Write the `toc.ncx` file
def write_toc_ncx(image_files, book_uuid):
    nav_points = "\n".join([
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
    with open("EPUB/OEBPS/toc.ncx", "w", encoding="utf-8") as f:
        f.write(toc_ncx)

def write_nav_xhtml(image_files):
    nav_items = "\n".join([
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
    
    with open("EPUB/OEBPS/nav.xhtml", "w", encoding="utf-8") as f:
        f.write(nav_xhtml)

# Copy images and create XHTML files for each image with exact dimensions
def add_html(image_files):
    css = '''@page {
  margin: 0;
}

body {
  display: block;
  margin: 0;
  padding: 0;
}'''

    with open("EPUB/OEBPS/html/style.css", "w", encoding="utf-8") as f:
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
        with open(f"EPUB/OEBPS/html/image-{i+1:04d}.html", "w", encoding="utf-8") as f:
            f.write(html_content)

# Zip into ePUB file (leaving 'mimetype' uncompressed)
def create_epub(epub_name):
    with zipfile.ZipFile(f"{epub_name}.epub", "w") as epub:
        epub.write("EPUB/mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk("EPUB"):
            for file in files:
                filepath = os.path.join(root, file)
                if filepath.endswith("mimetype"):
                    continue
                epub.write(filepath, filepath.replace("EPUB/", ""), compress_type=zipfile.ZIP_DEFLATED)

# Main function to create the ePUB
def create_image_epub(source_folder):
    book_uuid = f"urn:uuid:{str(uuid.uuid4())}"
            
    create_epub_structure()
    write_mimetype()
    write_container_xml()
    
    original_image_files = collect_images(source_folder)
    cover_extension = copy_images(original_image_files)

    epub_images_path = "EPUB/OEBPS/images"
    
    image_files = collect_images(epub_images_path)
        
    write_content_opf(image_files[1:], book_uuid, cover_extension)
    write_toc_ncx(image_files[1:], book_uuid)
    write_nav_xhtml(image_files[1:])
    add_html(image_files[1:])
    create_epub(source_folder)

    # Comment out for troubleshooting
    shutil.rmtree("EPUB")
    
    messagebox.showinfo("ePUB Created Successfully", f"'{os.path.basename(source_folder)}.epub' " \
                        f"has been created in '{os.path.dirname(source_folder)}'.")

def limit_label_length(label):
    if len(label) > 32:
        label = label[:32] + '...'
        
    return label
    

# GUI setup
def select_source_folder():
    global source_folder
    source_folder = filedialog.askdirectory(title="Select Source Folder")
    if source_folder:
        source_label.config(text=f"Source:\n{limit_label_length(os.path.basename(source_folder))}")

def start_process():
    if not source_folder:
        messagebox.showwarning("Input Required", "Please select a source folder.")
    else:
        try:
            create_image_epub(source_folder)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def quit_program():
    root.destroy()

# Initialize the GUI
root = Tk()
root.title("Image to ePUB Converter")
root.geometry("400x200")
root.minsize(400, 200)

source_folder = ""
select_source_button = Button(root, text="Select Source Folder", command=select_source_folder)
select_source_button.grid(row=0, column=0, columnspan=2, pady=20)
source_label = Label(root, text="Source:\nNone")
source_label.grid(row=1, column=0, columnspan=2)

start_button = Button(root, text="Create ePUB", command=start_process)
start_button.grid(row=2, column=0, padx=0, pady=30)

quit_button = Button(root, text="Quit", command=quit_program)
quit_button.grid(row=2, column=1, padx=0, pady=30)

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

root.mainloop()
