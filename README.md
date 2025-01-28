# ePUB Generator

ePUB Generator is an application for Mac OS that converts a folder of images to an ePUB file. A distributable can be generated using py2app:
1. Install all packages (py2app, PIL, natsort, etc.)
2. Use the command '$ python setup.py py2app' to create the application file

## Most Recent Version (Jan. 28, 2025)

As of version 0.1, the application converts a folder of images into a manga-style ePUB.  It can accommodate .jpg, .png, and .webp images. Spreads (a "landscape" image) are automatically split. If the first image is a spread, it is assumed to be the cover of the book. When generating a Manga-style ePUB, the left side of the spread is used as the first page and the right side (back cover) is not preserved. This is reversed in the case of generating a Comic-style ePUB.

## TODO

- testing for new image processing procedure
- refactor code
- improve/test error handling
- create additional custom graphics
- look into compatibility issues with Calibre / verify .zip structure

## Changelog

Jan 28, 2025 - Not Yet Built
- Fix: Images were getting cropped if the first image (cover) was a different aspect ratio. Now, the aspect ratio and view size are determined by the maximum image dimensions. All images are then resized and aligned with the spine to account for width variations.
- Implemented checkbox to toggle manga mode (default ON)
- Added dynamic checkbox description
- Removed "QUIT" button
- Standardized code comments/formatting

Jan 16, 2025 - Current Build
- Added a progress bar to track ePUB generation
- Resolved timestamp formatting error: "+0:00" to "Z"
- Simplified and reformatted UI

Previous
- Added .webp compatibility
- Now prevents user input while processing
- Limited length of folder names to avoid text overflow
