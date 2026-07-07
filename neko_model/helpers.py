from PIL import Image

class Helpers:
    

  @staticmethod
  def get_optimal_image_size(img_width, img_height, view_width, view_height):
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
  

  @staticmethod
  def calculate_max_dimensions(image_paths):
    """Calculate maximum width and height of the images."""

    max_width = 0
    max_height = 0
    for image_path in image_paths:
      with Image.open(image_path) as img:
        width, height = img.size
        max_width = max(max_width, width)
        max_height = max(max_height, height)

    return max_width, max_height


  @staticmethod
  def get_alignment(index, direction):
    """Determine alignment based on reading direction and page index."""

    RTL = 1  # right-to-left (manga style)

    even_page = index % 2 == 0
    
    if direction == RTL:  # right-to-left
      return 'left' if even_page else 'right'
      
    else:                 # left-to-right
      return 'right' if even_page else 'left'
