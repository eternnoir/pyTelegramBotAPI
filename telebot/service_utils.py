import random
import string
from io import BytesIO

try:
    # noinspection PyPackageRequirements
    from PIL import Image
    pil_imported = True
except ImportError:
    pil_imported = False


def is_string(var) -> bool:
    """
    Returns True if the given object is a string.
    """
    return isinstance(var, str)


def is_dict(var) -> bool:
    """
    Returns True if the given object is a dictionary.

    :param var: object to be checked
    :type var: :obj:`object`

    :return: True if the given object is a dictionary.
    :rtype: :obj:`bool`
    """
    return isinstance(var, dict)


def is_bytes(var) -> bool:
    """
    Returns True if the given object is a bytes object.

    :param var: object to be checked
    :type var: :obj:`object`

    :return: True if the given object is a bytes object.
    :rtype: :obj:`bool`
    """
    return isinstance(var, bytes)


def is_pil_image(var) -> bool:
    """
    Returns True if the given object is a PIL.Image.Image object.

    :param var: object to be checked
    :type var: :obj:`object`

    :return: True if the given object is a PIL.Image.Image object.
    :rtype: :obj:`bool`
    """
    return pil_imported and isinstance(var, Image.Image)


def pil_image_to_file(image, extension='JPEG', quality='web_low'):
    if pil_imported:
        photoBuffer = BytesIO()
        image.convert('RGB').save(photoBuffer, extension, quality=quality)
        photoBuffer.seek(0)

        return photoBuffer
    else:
        raise RuntimeError('PIL module is not imported')


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    # https://stackoverflow.com/a/312464/9935473
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def generate_random_token() -> str:
    """
    Generates a random token consisting of letters and digits, 16 characters long.

    :return: a random token
    :rtype: :obj:`str`
    """
    return ''.join(random.sample(string.ascii_letters, 16))
