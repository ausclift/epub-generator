from .helpers import Helpers
from .paths import Paths
from .write_files import WriteFiles

import os, shutil, uuid
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

        original_image_paths = sorted(
            file for file in source_path.rglob("*")
                if file.suffix.lower() in self.valid_extensions
        )
        original_image_paths = natsorted([str(file) for file in original_image_paths])
        if not original_image_paths:
            raise ValueError(f"No images found in '{source_folder}'.")
        
        return original_image_paths


    def copy_images(self, original_image_paths, read_order, loss_mode):
        """Copy and rename source images into `images` directory."""

        cover_extension = ''
        image_count = len(original_image_paths)
        current_progress = 0

        for i, image_path in enumerate(original_image_paths, start=1):
            image_filename = f'image-{i:04d}'
            _, ext = os.path.splitext(image_path)
            ext = ext.lower()

            if ext not in self.valid_extensions:
                continue

            # determine output format.
            if loss_mode == "lossless":
                out_extension = ".png"
            elif ext in {".jpg", ".jpeg"}:
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

                    if i == 1:
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

                    left_crop = img.crop((0, 0, mid_x, height))
                    right_crop = img.crop((mid_x + 1, 0, width, height))

                    if i != 1:
                        save_img(left_crop, left_path)
                        save_img(right_crop, right_path)

                    else:
                        if read_order == 0:
                            save_img(left_crop, left_path)
                            save_img(left_crop, Paths.IMAGES / f'cover{out_extension}')
                        else:
                            save_img(right_crop, right_path)
                            save_img(right_crop, Paths.IMAGES / f'cover{out_extension}')

                        cover_extension = out_extension

            # update progress (up to 50%)
            new_progress = ((i * 50) // image_count // 5) * 5

            if new_progress > current_progress:
                current_progress = new_progress
                self.progress_callback(current_progress)

        return cover_extension[1:]  # Strip leading dot for media type

    
    def create_image_epub(self, source_folder, loss_mode, read_order):
        """Initiate ePUB creation and track progress."""

        book_uuid = f'urn:uuid:{str(uuid.uuid4())}'
        WriteFiles.create_epub_structure()
        WriteFiles.write_mimetype()
        WriteFiles.write_container_xml()
        original_image_files = self.collect_images(source_folder)
        cover_extension = self.copy_images(original_image_files, read_order, loss_mode)

        image_files = self.collect_images(Paths.IMAGES)
        WriteFiles.write_content_opf(image_files[1:], book_uuid, cover_extension, read_order, source_folder)
        WriteFiles.write_toc_ncx(image_files[1:], book_uuid)
        WriteFiles.write_nav_xhtml(image_files[1:])
        WriteFiles.write_css_file()
        self.progress_callback(55)

        WriteFiles.add_html(image_files[1:], read_order)
        self.progress_callback(60)

        WriteFiles.create_epub(source_folder)
        self.progress_callback(100)

        # removes temporary files from local directory
        # remove for troubleshooting
        shutil.rmtree('EPUB')