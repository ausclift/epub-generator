# ePUB Generator

ePUB Generator is an application for Mac OS that converts a folder of images to an ePUB file. A distributable can be generated using py2app:
1. Install required packages (py2app, Pillow, natsort)
2. Use the command '$ python setup.py py2app' to create the application file
* If on silicon Mac with Conda installed, py2app cannot create distributable, but alias mode still works: '$ python setup.py py2app -A'

## Functionality

The application converts a folder of images into a manga-style ePUB.  It can accommodate .jpg, .png, and .webp images. Spreads (a "landscape" image) are automatically split. If the first image is a spread, it is assumed to be the cover of the book. When generating a manga-style ePUB, the left side of the spread is used as the first page and the right side (back cover) is not preserved. This is reversed in the case of generating a comic-style ePUB.

## TODO

- error handling
- custom graphics
- preview feature to view a small version of the resulting ebook

## Changelog

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
