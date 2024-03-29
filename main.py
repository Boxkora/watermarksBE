import matplotlib
matplotlib.use('Agg')

from flask import Flask, request, send_file
from flask_restful import Resource, Api
from flask_cors import CORS
from PIL import Image, ImageFilter , ImageDraw, ImageFont
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
import os
import io
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
api = Api(app)
CORS(app)

class EmbedWatermark(Resource):
    def post(self):
        file = request.files['file']
        watermark_text = request.form['text']
        
        if not ('.png' in file.filename or '.jpg' in file.filename):
            return "Invalid Input type. Please input .png , .jpg", 400
        
        img = Image.open(file.stream).convert("RGBA")
        txt = Image.new('RGBA', img.size, (255,255,255,0))
        font = ImageFont.truetype("arial", 15)
        d = ImageDraw.Draw(txt)
        
        left, top, right, bottom = font.getbbox(watermark_text)
        text_width = right - left
        text_height = bottom - top
        for i in range(0, img.width, text_width):
            for j in range(0, img.height, text_height):
                d.text((i, j), watermark_text, fill=(255,255,255,int(0.004*255)), font=font)

        watermarked = Image.alpha_composite(img, txt)
        byte_io = io.BytesIO()
        watermarked.save('watermarked_image.png', 'PNG')
        watermarked.save(byte_io, 'PNG')
        byte_io.seek(0)

        return send_file(byte_io, mimetype='image/png')

class ImageWatermark(Resource):
    
    def post(self):
        file = request.files['image']
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(file)
            image = image.convert('RGB')
            image = image.resize((800, 600))
            width, height = image.size

            # Original
            plt.subplot(2, 2, 1)
            plt.imshow(image)
            plt.title('Original Image')

            # MI 1
            image1 = image.copy()
            for i in range(width):
                for j in range(height):
                    r, g, b = image1.getpixel((i, j))
                    if r % 2 == 0:
                        image1.putpixel((i, j), (0, 0, 0))
                    else:
                        image1.putpixel((i, j), (255, 255, 255))
            plt.subplot(2, 2, 2)
            plt.imshow(image1)
            plt.title('Modified Image 1')

            # MI 2
            image2 = image.copy()
            for i in range(width):
                for j in range(height):
                    r, g, b = image2.getpixel((i, j))
                    voting = [r % 2, g % 2, b % 2]
                    vote_sum = sum(voting)
                    if vote_sum >= 2:
                        image2.putpixel((i, j), (255, 255, 255))
                    else:
                        image2.putpixel((i, j), (0, 0, 0))
            plt.subplot(2, 2, 3)
            plt.imshow(image2)
            plt.title('Modified Image 2')

            # MI 3
            image3 = image.copy()
            for _ in range(8):  
                image3 = image3.filter(ImageFilter.SHARPEN)
            plt.subplot(2, 2, 4)
            plt.imshow(image3)
            plt.title('Modified Image 3')


            # Save the entire plot as an image
            plot_filename = 'plot_' + file.filename
            plt.savefig(plot_filename)



            # Schedule the file removal
            scheduler = BackgroundScheduler()
            scheduler.add_job(func=lambda: os.remove(plot_filename), trigger='date', run_date=datetime.now() + timedelta(seconds=10))
            scheduler.start()

            # Return the filename or URL
            return send_file(plot_filename, mimetype='image/jpeg')
        else:
            return 'Invalid file type. Please upload a PNG or JPG file.', 400
    

api.add_resource(ImageWatermark, '/detect_watermark')
api.add_resource(EmbedWatermark, '/embed_watermark')

if __name__ == '__main__':
    app.run(debug=True)
