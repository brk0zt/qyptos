from PIL import Image, ImageDraw, ImageFont

def add_watermark(input_image_path, output_image_path, username):
    try:
        # Görüntüyü aç
        image = Image.open(input_image_path).convert("RGBA")
        
        # Şeffaf bir katman oluştur
        watermark = Image.new('RGBA', image.size, (255, 255, 255, 0))
        
        # Yazı fontu ve boyutu
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        draw = ImageDraw.Draw(watermark)
        text = f"© {username}"
        
        # Metin boyutunu al (yeni yöntem)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Metin konumu (sağ alt köşe)
        x = image.width - text_width - 10
        y = image.height - text_height - 10
        
        # Metni çiz
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
        
        # Orijinal görüntüyle birleştir
        watermarked = Image.alpha_composite(image, watermark)
        
        # JPEG formatında kaydetmek için RGB'ye çevir
        if watermarked.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', watermarked.size, (255, 255, 255))
            background.paste(watermarked, mask=watermarked.split()[-1])
            watermarked = background
        
        watermarked.save(output_image_path, "JPEG", quality=95)
        
    except Exception as e:
        raise Exception(f"Watermark eklenirken hata oluştu: {str(e)}")
