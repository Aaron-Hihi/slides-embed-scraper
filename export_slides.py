import os
import time
import shutil
import pytesseract
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

tesseract_local_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_local_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_local_path
elif shutil.which("tesseract"):
    pytesseract.pytesseract.tesseract_cmd = "tesseract"

def main():
    target_url = os.environ.get("SLIDE_URL")
    custom_name = os.environ.get("PDF_NAME", "output")
    
    if not custom_name.lower().endswith(".pdf"):
        custom_name += ".pdf"

    chrome_options = Options()
    chrome_options.add_argument("--headless") # Required for GitHub
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    pdf_canvas = None

    try:
        driver.get(target_url)
        print(f"Starting export for: {target_url}")
        time.sleep(10)
        
        last_url = ""
        count = 0

        while True:
            current_url = driver.current_url
            if current_url == last_url and count > 0:
                break
            
            print(f"Baking Slide {count + 1}...")
            png_data = driver.get_screenshot_as_png()
            img = Image.open(BytesIO(png_data))
            w, h = img.size
            pdf_w, pdf_h = w * 0.75, h * 0.75
            
            if pdf_canvas is None:
                pdf_canvas = canvas.Canvas(custom_name, pagesize=(pdf_w, pdf_h))
            else:
                pdf_canvas.setPageSize((pdf_w, pdf_h))

            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            img_reader = ImageReader(img)
            pdf_canvas.drawImage(img_reader, 0, 0, width=pdf_w, height=pdf_h)
            
            pdf_canvas.saveState()
            pdf_canvas.setFillAlpha(0) 
            for j in range(len(ocr_data['text'])):
                word = ocr_data['text'][j].strip()
                if word:
                    x = ocr_data['left'][j] * 0.75
                    y = pdf_h - (ocr_data['top'][j] * 0.75) - (ocr_data['height'][j] * 0.75)
                    font_size = max(1, ocr_data['height'][j] * 0.75)
                    pdf_canvas.setFont("Helvetica", font_size)
                    pdf_canvas.drawString(x, y, word)
            
            pdf_canvas.restoreState()
            pdf_canvas.showPage()
            
            last_url = current_url
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.RIGHT)
            time.sleep(3)
            count += 1

        if pdf_canvas:
            pdf_canvas.save()
            print(f"SUCCESS: {custom_name} created with {count} slides.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()