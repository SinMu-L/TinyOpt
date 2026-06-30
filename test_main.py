import os
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

# Mock PyQt5 before importing main (headless test env has no GUI)
_MOCK_MODULES = [
    "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui",
]
for mod_name in _MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from main import local_compress_image


@pytest.fixture
def rgb_image_bytes():
    img = Image.new("RGB", (200, 200), (255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def rgba_image_bytes():
    img = Image.new("RGBA", (200, 200), (255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_compress_jpeg(rgb_image_bytes):
    success, data, error = local_compress_image(rgb_image_bytes, ".jpg", quality=10)
    assert success, f"JPEG compression failed: {error}"
    assert len(data) > 0
    assert len(data) < len(rgb_image_bytes), "JPEG should be smaller after compression"


def test_compress_png(rgba_image_bytes):
    success, data, error = local_compress_image(rgba_image_bytes, ".png")
    assert success, f"PNG compression failed: {error}"
    assert len(data) > 0


def test_compress_webp(rgb_image_bytes):
    success, data, error = local_compress_image(rgb_image_bytes, ".jpg", target_format="webp", quality=50)
    assert success, f"WebP conversion failed: {error}"
    assert len(data) > 0
    with Image.open(BytesIO(data)) as img:
        assert img.format == "WEBP"


def test_convert_png_to_jpeg(rgba_image_bytes):
    success, data, error = local_compress_image(rgba_image_bytes, ".png", target_format="jpeg")
    assert success, f"PNG->JPEG conversion failed: {error}"
    with Image.open(BytesIO(data)) as img:
        assert img.format == "JPEG"


def test_convert_jpeg_to_png(rgb_image_bytes):
    success, data, error = local_compress_image(rgb_image_bytes, ".jpg", target_format="png")
    assert success, f"JPEG->PNG conversion failed: {error}"
    with Image.open(BytesIO(data)) as img:
        assert img.format == "PNG"


def test_compress_tiff(rgb_image_bytes):
    success, data, error = local_compress_image(rgb_image_bytes, ".jpg", target_format="tiff")
    assert success, f"TIFF conversion failed: {error}"
    assert len(data) > 0


def test_compress_gif(rgb_image_bytes):
    success, data, error = local_compress_image(rgb_image_bytes, ".jpg", target_format="gif")
    assert success, f"GIF conversion failed: {error}"
    assert len(data) > 0


def test_resize_fit(rgb_image_bytes):
    success, data, error = local_compress_image(
        rgb_image_bytes, ".jpg",
        resize_params={"method": "fit", "width": 100, "height": 100},
    )
    assert success, f"Resize fit failed: {error}"
    with Image.open(BytesIO(data)) as img:
        assert img.width <= 100
        assert img.height <= 100


def test_resize_scale(rgb_image_bytes):
    success, data, error = local_compress_image(
        rgb_image_bytes, ".jpg",
        resize_params={"method": "scale", "width": 50},
    )
    assert success, f"Resize scale failed: {error}"
    with Image.open(BytesIO(data)) as img:
        assert img.width == 100
        assert img.height == 100


def test_resize_cover(rgb_image_bytes):
    success, data, error = local_compress_image(
        rgb_image_bytes, ".jpg",
        resize_params={"method": "cover", "width": 50, "height": 50},
    )
    assert success, f"Resize cover failed: {error}"
    with Image.open(BytesIO(data)) as img:
        assert img.width == 50
        assert img.height == 50


def test_resize_thumb(rgb_image_bytes):
    success, data, error = local_compress_image(
        rgb_image_bytes, ".jpg",
        resize_params={"method": "thumb", "width": 50, "height": 80},
    )
    assert success, f"Resize thumb failed: {error}"
    with Image.open(BytesIO(data)) as img:
        assert img.width == 50
        assert img.height == 80


def test_invalid_format(rgb_image_bytes):
    success, data, error = local_compress_image(rgb_image_bytes, ".jpg", target_format="invalid")
    assert not success
    assert error is not None


def test_invalid_data():
    success, data, error = local_compress_image(b"not an image", ".jpg")
    assert not success


def test_quality_reduces_size():
    buf = BytesIO()
    img = Image.new("RGB", (1000, 1000), (255, 128, 64))
    img.save(buf, format="JPEG", quality=95)
    raw = buf.getvalue()

    _, high_data, _ = local_compress_image(raw, ".jpg", quality=90)
    _, low_data, _ = local_compress_image(raw, ".jpg", quality=10)

    assert len(low_data) < len(high_data), "Lower quality should produce smaller file"


def test_ico_conversion(rgba_image_bytes):
    success, data, error = local_compress_image(rgba_image_bytes, ".png", target_format="ico")
    assert success, f"ICO conversion failed: {error}"
    assert len(data) > 0
    assert data[:4] == b"\x00\x00\x01\x00"  # ICO header magic


def test_output_valid_image(rgb_image_bytes):
    for fmt in ("jpeg", "png", "webp", "gif", "tiff", "bmp"):
        success, data, error = local_compress_image(rgb_image_bytes, ".jpg", target_format=fmt)
        assert success, f"Format {fmt} failed: {error}"
        with Image.open(BytesIO(data)) as img:
            assert img.width > 0
            assert img.height > 0
