# ePUB Generator

ePUB Generator is an application for Mac OS that converts a folder of images to an ePUB file. A distributable can be generated using py2app:

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
The application converts a folder of images into a manga-style ePUB.  It can accommodate .jpg, .png, and .webp images. To ensure compatibility with older devices, WEBP images are converted to PNGs. Spreads (width > height) are automatically split. If the first image is a spread, it is assumed to be the front and back cover of the book. In this case only the front cover is preserved, determined based on the selected reading direction.

To fully uninstall the program, simply delete the application file. If applicable, remove the .nekoconfig.json file which generates in /User.

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
- Now should excusively use pathlib
- Fixed bug that caused any previously selected folder to be internally removed when hitting "cancel"

Jul 4, 2026
- Added quality options for 75%, 90%, and lossless
- Fixed progress bar not updating properly

Mar 23, 2026
- Refactored font-handling functions
- Fixed title metadata to use folder name
- Added author metadata

Dec 27, 2025
- .webp images are now converted to .png for better compatibility (this increases processing time and file size for .webp ePUBs)
- Resolved some validation issues within content.opf and toc.ncx
- Now creates .nekoconfig.json file in /User to persist the last-accessed directory

Nov 11, 2025
- Changed application name from 'ePub Generator' to 'ePub Neko'

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
- Added .webp compatibility
- Now prevents user input while processing
- Limited length of folder names to avoid text overflow
