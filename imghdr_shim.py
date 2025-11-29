"""
Compatibility shim for imghdr module removed in Python 3.13.
This provides basic image type detection needed by tweepy.
"""

import struct

tests = []

def test_jpeg(h, f):
    """JPEG data with JFIF or Exif markers"""
    if h[:2] == b'\xff\xd8':
        return 'jpeg'

def test_png(h, f):
    """PNG image"""
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'

def test_gif(h, f):
    """GIF image"""
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

def test_webp(h, f):
    """WebP image"""
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'

def test_bmp(h, f):
    """BMP image"""
    if h[:2] == b'BM':
        return 'bmp'

tests = [test_jpeg, test_png, test_gif, test_webp, test_bmp]

def what(file, h=None):
    """
    Determine the type of image contained in a file or bytes.
    
    Args:
        file: A filename (string), file-like object, or None
        h: Optional bytes to test (if file is None)
    
    Returns:
        A string describing the image type, or None if unknown
    """
    f = None
    try:
        if h is None:
            if isinstance(file, (str, bytes)):
                f = open(file, 'rb')
                h = f.read(32)
            else:
                location = file.tell()
                h = file.read(32)
                file.seek(location)
                f = None
        
        for tf in tests:
            res = tf(h, f)
            if res:
                return res
    finally:
        if f:
            f.close()
    
    return None

