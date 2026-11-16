from PIL import Image

img = Image.open("docs/fase_1_7/screenshots/01_ct_a_ticket_passive_first_person.png")
extrema = img.getextrema()
print("Extrema (min, max per channel RGBA):", extrema)
