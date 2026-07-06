from .paths import Paths
import os, zipfile, shutil, uuid
from datetime import datetime, timezone
from PIL import Image
from natsort import natsorted
from pathlib import Path

class Model:

    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

    def __init__(self):
        self.source_folder = ''
        self.progress_callback = None

    def set_progress_callback(self, function):
        """Create callback function to send progress updates."""
        self.progress_callback = function

    def collect_images(self, source_folder):
        """Collect images in the source folder."""
        source_path = Path(source_folder)

        original_image_files = sorted(
            file for file in source_path.rglob("*")
                if file.suffix.lower() in self.valid_extensions
        )
        original_image_files = natsorted([str(file) for file in original_image_files])
        if not original_image_files:
            raise ValueError(f"No images found in '{source_folder}'.")
        
        return original_image_files

    def create_epub_structure(self):
        """Define ePUB Structure by creating the required folders."""
        os.makedirs(Paths.META, exist_ok=True)
        os.makedirs(Paths.IMAGES, exist_ok=True)
        os.makedirs(Paths.HTML, exist_ok=True)

    def write_mimetype(self):
        """Write the `mimetype` file that defines the folder structure as an ePUB."""
        with open(Paths.MIM, 'w') as f:
            f.write('application/epub+zip')

    def write_container_xml(self):
        """Write the `container.xml` file."""
        container_content = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        with open(Paths.META / 'container.xml', 'w', encoding='utf-8') as f:
            f.write(container_content)

    def copy_images(self, image_files, read_order, loss_mode):
        """Copy and rename source images into `images` directory."""

        cover_extension = ''

        for i, image_path in enumerate(image_files):
            image_filename = f'image-{i+1:04d}'
            _, ext = os.path.splitext(image_path)
            ext = ext.lower()

            if ext not in self.valid_extensions:
                continue

            # determine output format
            if loss_mode == "lossless":
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
                    if loss_mode == "ultra" and path.suffix == ".jpeg":
                        im.save(path, quality=90, optimize=True)
                    else:
                        im.save(path)

                # portrait / single page
                if width <= height:
                    out_path = Paths.IMAGES / f'{image_filename}{out_extension}'
                    save_img(img, out_path)

                    if i == 0:
                        cover_path = Paths.IMAGES / f'cover{out_extension}'
                        save_img(img, cover_path)
                        cover_extension = out_extension

                # landscape / spread
                else:
                    mid_x = width // 2

                    left_label = 'B' if read_order == 0 else 'A'
                    right_label = 'A' if read_order == 0 else 'B'

                    left_path = Paths.IMAGES / f'{image_filename}-{left_label}{out_extension}'
                    right_path = Paths.IMAGES / f'{image_filename}-{right_label}{out_extension}'

                    if i != 0:
                        img.crop((0, 0, mid_x, height)).save(left_path)
                        img.crop((mid_x + 1, 0, width, height)).save(right_path)

                    else:
                        if read_order == 0:
                            left_crop = img.crop((0, 0, mid_x, height))
                            save_img(left_crop, left_path)
                            save_img(left_crop, Paths.IMAGES / f'cover{out_extension}')
                        else:
                            right_crop = img.crop((mid_x + 1, 0, width, height))
                            save_img(right_crop, right_path)
                            save_img(right_crop, Paths.IMAGES / f'cover{out_extension}')

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
  <spine toc="ncx" page-progression-direction="{'rtl' if read_order == 0 else 'ltr'}">
{spine_items}
  </spine>
</package>'''
        
        with open(Paths.OEBPS / 'content.opf', 'w', encoding='utf-8') as f:
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
        
        with open(Paths.OEBPS / 'toc.ncx', 'w', encoding='utf-8') as f:
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
        
        with open(Paths.OEBPS / 'nav.xhtml', 'w', encoding='utf-8') as f:
            f.write(nav_xhtml)

    def write_css_file(self):
        """Write the `CSS` file."""
        css_path = Paths.HTML / 'style.css'
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
        return 'right' if (even_page and direction == 0) or (not even_page and direction == 1) else 'left'

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

        output_dir = Paths.HTML

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

        epub_path = Path(f"{epub_name}.epub")

        with zipfile.ZipFile(epub_path, "w") as epub:
            # Write uncompressed mimetype first
            epub.write(Paths.MIM, "mimetype", compress_type=zipfile.ZIP_STORED)

            # Add the remaining files
            for filepath in Paths.ROOT.rglob("*"):
                if filepath.is_dir():
                    continue

                if filepath == Paths.MIM:
                    continue

                epub.write(filepath, filepath.relative_to(Paths.ROOT), compress_type=zipfile.ZIP_DEFLATED)

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

        image_files = self.collect_images(Paths.IMAGES)
        self.write_content_opf(image_files[1:], book_uuid, cover_extension, read_order, source_folder)
        self.write_toc_ncx(image_files[1:], book_uuid)
        self.write_nav_xhtml(image_files[1:])
        self.write_css_file()
        self.progress_callback(55)

        self.add_html(image_files[1:], read_order)
        self.progress_callback(60)

        self.create_epub(source_folder)
        self.progress_callback(100)

        # removes temporary files from local directory
        # remove for troubleshooting
        shutil.rmtree('EPUB')