"""
Sticks images together.
"""

from PIL import Image, ImageDraw

output_x = 3840
output_y = 2160

background = Image.open("latest_weather_image.jpg")
foreground = Image.open("current_forecast.png")

# Crop background, from the top

original_x, original_y = background.size
left = (original_x - output_x) // 2
bottom = 0 #(original_y - output_y) // 2
right = left + output_x
top = bottom + output_y
cropped_background = background.crop((left, bottom, right, top))

# Composit together
pixels_offset = 64
output_extent = [pixels_offset, output_y - (foreground.size[1] + pixels_offset)]

rectangle_border = 10
# rectangle_size = [
#     pixels_offset - rectangle_border,
#     output_y - (foreground.size[1] + pixels_offset + rectangle_border),
#     foreground.size[0] + pixels_offset + rectangle_border,
#     pixels_offset - rectangle_border,
# ]
rectangle_size = [
    pixels_offset - rectangle_border,
    output_y - (pixels_offset - rectangle_border),
    foreground.size[0] + pixels_offset + rectangle_border,
    output_y - (foreground.size[1] + pixels_offset + rectangle_border),
]

rectangle = ImageDraw.Draw(cropped_background, "RGBA")
draw = rectangle.rectangle(rectangle_size, fill=(100, 100, 100, 100))

cropped_background.paste(
    foreground,
    box=output_extent,
    mask=foreground,
)

cropped_background.save(
    "composite.jpg"
)