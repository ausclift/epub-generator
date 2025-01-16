# ePUB Generator

ePUB Generator is an application for Mac OS that converts a folder of images to an ePUB file. The most recent version can be found in '/dist'.

## Current Version Limitations (Oct. 31, 2024) - **Not Yet Built**

As of version 0.1, the application converts a folder of images into a manga-style ePUB.  It can accommodate jpg, png, and webp images. Spreads (defined as a "landscape" image) are automatically split. If the first image of a set is a spread, it is assumed to be the cover of the book. The left side of the spread is used as the first page; the right side (back cover) is not preserved.

## TODO

- create an option that allows switching between right-to-left and left-to-right formatting
- improve error handling and implement basic tests
- add custom (themed?) graphics
- look into compatibility issues with Calibre

## Change Log

Jan 16, 2025
- Added a progress bar to track ePUB generation
- Resolved timestamp formatting error: "+0:00" to "Z"
- Simplified and reformatted UI

Previous
- Added .webp compatibility
- Now prevents user input while processing
- Limited length of folder names to avoid text overflow
