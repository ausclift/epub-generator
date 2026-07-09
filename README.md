# ePUB Generator

ePUB Generator is an application for MacOS that converts a folder of images to a manga- or comic-style ePUB file. A distributable can be generated using py2app:

1. Install the required packages with `pip install Pillow` and `pip install natsort`
2. Install Nuitka with `$ pip install nuitka ordered-set zstandard`
3. Use the following command to create the application:
``` 
$ python -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --enable-plugin=tk-inter \
    --macos-app-name="ePUB Neko" \
    --macos-app-icon=icon.icns \
    --output-dir=dist \
    ePUBNeko.py
```

## Functionality
The application converts a folder of images into an ePUB.  It can accommodate JPG, PNG, and WEBP images. To ensure compatibility with older devices, WEBP images are converted to PNGs. Spreads (width > height) are automatically split. If the first image is a spread, it is assumed to be the front and back cover of the book. In this case, only the front cover is preserved, determined by the selected reading direction.

ePUB Neko can create both manga and comic-style ePUBs. It also provides three image quality options. 'Lossless' converts all images to PNGs if the book is intended for archival purposes.

To fully uninstall the program, simply delete the application file and remove the nekoconfig.json file from /User.

## TODO

- Create temp files in the correct location (currently uses app folder)
- Test/check error handling
- Better UI

## Changelog

Jul 9, 2026
- Fixed duplicate image for cover

Jul 7, 2026
- Now using Nuitka instead of py2app for packaging, see updated instructions
- New build is ~36% smaller (53 mb) and 15-20% more efficient

Jul 6, 2026
- Began complete refactor: organizing codebase into more folders, files, and classes.
- Now should exclusively use pathlib
- Fixed bug that caused any previously selected folder to be internally removed when hitting 'cancel'

Jul 4, 2026
- Added quality options for 75%, 90%, and lossless
- Fixed progress bar not updating properly

Mar 23, 2026
- Refactored font-handling functions
- Fixed title metadata to use folder name
- Added author metadata

Dec 27, 2025
- WEBP images are now converted to PNG for better compatibility (this increases processing time and file size for WEBP ePUBs)
- Resolved some validation issues within content.opf and toc.ncx
- Now creates nekoconfig.json file in /User to persist the last-accessed directory

Nov 11, 2025
- Changed application name from 'ePub Generator' to 'ePUB Neko'

Jan 30, 2025
- Found bug with py2app preventing distributable builds while using Conda on silicon Macs

Jan 28, 2025
- Fix: Images were getting cropped if the first image (cover) was a different aspect ratio. Now, the aspect ratio and view size are determined by the maximum image dimensions. All images are then resized and aligned with the spine to account for width variations.
- Implemented checkbox to toggle manga mode (default ON)
- Added dynamic checkbox description
- Removed "QUIT" button
- Code refactoring

Jan 16, 2025
- Added a progress bar to track ePUB generation
- Resolved timestamp formatting error: "+0:00" to "Z"
- Simplified and reformatted UI

Previous
- Added WEBP compatibility
- Now prevents user input while processing
- Limited length of folder names to avoid text overflow
