import io
from PIL import Image, ImageChops
from django.core.files.base import ContentFile


def build_item_preview(item, max_size=(600, 600), quality=75):
    try:
        base = Image.open(item.color.image).convert("RGBA")
    except (FileNotFoundError, OSError):
        return None

    area = item.product.print_area or {}
    has_design = (
        item.design is not None
        and all(k in area for k in ("top", "left", "width", "height"))
    )

    if has_design:
        try:
            design = Image.open(item.design.image).convert("RGBA")
        except (FileNotFoundError, OSError):
            design = None

        if design is not None:
            base_w, base_h = base.size
            box_left = int(base_w * area["left"] / 100)
            box_top = int(base_h * area["top"] / 100)
            box_w = int(base_w * area["width"] / 100)
            box_h = int(base_h * area["height"] / 100)

            if box_w > 0 and box_h > 0:
                design.thumbnail((box_w, box_h), Image.LANCZOS)
                offset_x = box_left + (box_w - design.width) // 2
                offset_y = box_top + (box_h - design.height) // 2

                design_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
                design_layer.paste(design, (offset_x, offset_y), design)

                base_rgb = base.convert("RGB")
                design_rgb = design_layer.convert("RGB")
                design_alpha = design_layer.split()[-1]

                multiplied = ImageChops.multiply(base_rgb, design_rgb)
                final = base_rgb.copy()
                final.paste(multiplied, (0, 0), design_alpha)
            else:
                final = base.convert("RGB")
        else:
            final = base.convert("RGB")
    else:
        final = base.convert("RGB")

    final.thumbnail(max_size, Image.LANCZOS)

    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    return ContentFile(buf.getvalue())