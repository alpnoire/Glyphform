import numpy as np
from PIL import Image, ImageDraw, ImageFont


def generate_text_mask(
    text: str,
    width: int = 100,
    height: int = 40,
    density: int = 2,
) -> np.ndarray:
    """Generate a centred Boolean mask containing the requested text."""

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    if width <= 0 or height <= 0 or density <= 0:
        raise ValueError("Dimensions and density must be positive.")

    if density > min(width, height):
        raise ValueError("Density cannot exceed the image dimensions.")

    image = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default(size=max(1, int(height * 0.65)))

    # Fit the text inside the available image area.
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    scale = min(
        1.0,
        (width * 0.9) / max(1, text_width),
        (height * 0.9) / max(1, text_height),
    )

    if scale < 1.0:
        font = ImageFont.load_default(
            size=max(1, int(height * 0.65 * scale))
        )
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2 - bbox[0]
    y = (height - text_height) // 2 - bbox[1]

    draw.text((x, y), text, fill=255, font=font)

    # Density controls how closely spaced the sampled particles are.
    pixels = np.array(image)
    mask = pixels > 127

    if density > 1:
        sampled = np.zeros_like(mask)
        sampled[::density, ::density] = mask[::density, ::density]
        mask = sampled

    return mask


def generate_text_points(
    text: str,
    width: int = 100,
    height: int = 40,
    density: int = 2,
) -> np.ndarray:
    """Convert a text mask into particle coordinates."""

    mask = generate_text_mask(text, width, height, density)

    y_coords, x_coords = np.where(mask)

    return np.column_stack((x_coords, y_coords)).astype(float)