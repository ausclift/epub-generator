# ePUB Generator

ePUB Generator is an application for Mac OS that converts a folder of images to an ePUB file. A distributable can be generated using py2app:
1. Install all packages (py2app, PIL, natsort, etc.)
2. Use the command '$ python setup.py py2app' to create the application file

## Most Recent Build (Jan. 17, 2025)

As of version 0.1, the application converts a folder of images into a manga-style ePUB.  It can accommodate .jpg, .png, and .webp images. Spreads (defined as a "landscape" image) are automatically split. If the first image of a set is a spread, it is assumed to be the cover of the book. The left side of the spread is used as the first page; the right side (back cover) is not preserved.

## TODO

- improve/test error handling
- create additional custom graphics
- look into compatibility issues with Calibre / verify .zip structure

## Changelog

Jan 22, 2025 - Not Yet Built
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
