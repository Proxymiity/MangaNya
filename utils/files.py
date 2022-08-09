from pathlib import Path

import img2pdf
from PIL import Image

from zipfile import ZipFile, ZIP_BZIP2

from exceptions import TransformationError

img2pdf_exceptions = (img2pdf.UnsupportedColorspaceError, img2pdf.JpegColorspaceError,
                      img2pdf.AlphaChannelError, img2pdf.ImageOpenError, img2pdf.PdfTooLargeError)


def make_pdf(source: list[Path], destination: Path):
    # Get absolute, string-based filepaths, because img2pdf does not support Path-like objects
    files = [str(x) for x in source]
    try:  # Try a direct conversion. May not always be successful because of alpha channels
        with destination.open('wb') as d:
            d.write(img2pdf.convert(files))
    except img2pdf_exceptions:
        try:
            t_files = convert_images(files)  # Convert images to standard JPEG and retry
            with destination.open('wb') as d:
                d.write(img2pdf.convert(t_files))
        except img2pdf_exceptions:
            raise TransformationError  # This may only happen if one of the images wasn't an image


def convert_images(source):
    t_files = []
    for i in source:
        fg = Image.open(i)
        if fg.mode in ("P", "RGBA", "LA", "PA"):  # Usually indicates a problematic PNG image with alpha channels
            fg.load()
            bg = Image.new("RGB", fg.size, (255, 255, 255))
            try:
                bg.paste(fg, mask=fg.split()[3])
            except IndexError:
                bg.paste(fg)
            bg.save(f"{i}.conv.jpg", "JPEG", quality=100)
            t_files.append(f"{i}.conv.jpg")
        else:
            t_files.append(i)
    return t_files


def make_zip(source: list[Path], destination: Path):
    with ZipFile(destination, 'w', ZIP_BZIP2) as d:
        for f in source:
            d.write(f, f.name)
