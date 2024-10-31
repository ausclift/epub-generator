# ePUB Generator

ePUB Generator is an application for Mac OS that converts a folder of images to an ePUB file. The most recent version can be found in '/dist'.

## Current Version Limitations (Oct. 31, 2024)

As of version 0.1, the application converts a folder of images into a manga-style ePUB.  It can accommodate jpg/jpeg and png images. Mixed cased files types may not be recognized– e.g. jPEG, PnG. Spreads (image width > height) are automatically split. If the first image of a set is a spread, the left side of the spread is used as the first page and cover. Oftentimes, this first-image spread is the cover of the manga where the left is the front cover and the right is the back cover. The back cover is not currently preserved.

## TODO

- currently only converts manga (right-to-left): create an option that allows switching between right-to-left and left-to-right formatting
- improve error handling and implement basic tests
- prevent inputs while ebook is generating and provide loading bar or other feedback
- overhaul UI and add custom (themed?) graphics
- look into potential compatibility issues with Calibre
- add .webp compatibility