from PIL import Image, ImageDraw, ImageFont
import os

# Create the ngos directory if it doesn't exist
os.makedirs('static/images/ngos', exist_ok=True)

# NGO names and their corresponding image filenames
ngos = {
    'helping-hands.jpg': 'Helping Hands Foundation',
    'green-earth.jpg': 'Green Earth Initiative',
    'women-empowerment.jpg': 'Women Empowerment Trust',
    'rural-development.jpg': 'Rural Development Society',
    'animal-welfare.jpg': 'Animal Welfare Association',
    'education-for-all.jpg': 'Education for All'
}

# Colors for different NGOs
colors = [
    (52, 152, 219),  # Blue
    (46, 204, 113),  # Green
    (155, 89, 182),  # Purple
    (230, 126, 34),  # Orange
    (231, 76, 60),   # Red
    (52, 73, 94)     # Dark Blue
]

# Create images
for i, (filename, name) in enumerate(ngos.items()):
    # Create a new image with a solid color background
    img = Image.new('RGB', (400, 300), colors[i % len(colors)])
    draw = ImageDraw.Draw(img)
    
    # Add NGO name
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_width = draw.textlength(name, font=font)
    text_position = ((400 - text_width) // 2, 150)
    
    # Draw text
    draw.text(text_position, name, fill='white', font=font)
    
    # Save the image
    img.save(f'static/images/ngos/{filename}')
    print(f'Created image for {name}')

print('All NGO placeholder images have been created!') 