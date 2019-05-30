from PIL import Image
import numpy as np


def read_image(input_file: str, scale_factor: float=100) -> np.ndarray:
    """
    Reading an image and returning it as a numpy.ndarray.

    Args:
        input_file: str: Path and name of the image to read
        scale_factor: float: factor for resizing the image in percent. 100 means the original image size, 50
                            would mean to reduce the size by half.
    Returns:
        3D numpy array with dimensions (width, height, color)
    """

    image_raw = Image.open(input_file)
    x_size_raw = image_raw.size[0]
    y_size_raw = image_raw.size[1]
    set_scale_factor = (scale_factor / 100.)

    new_size = (x_size_raw * set_scale_factor, y_size_raw * set_scale_factor)
    image_raw.thumbnail(new_size, Image.ANTIALIAS)

    image_array = np.asarray(image_raw, order='F')
    image_array.setflags(write=True)

    return image_array
