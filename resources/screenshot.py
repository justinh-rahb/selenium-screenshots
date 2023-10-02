from flask import request, send_file, abort
from flask_restful import Resource
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile
import logging
import time  # Importing the time module
from utilities import authenticate, validate_url

logging.basicConfig(level=logging.INFO)

class ScreenshotAPI(Resource):
    def get(self):
        # Authenticate
        authenticate()
        
        # Input validation
        url = request.args.get('url')
        if not url or not validate_url(url):
            abort(400, "Invalid or missing URL")
        
        viewport = request.args.get('viewport', '800x600')
        try:
            width, height = map(int, viewport.split('x'))
        except ValueError:
            abort(400, "Invalid viewport format. It should be <width>x<height>")
        
        format = request.args.get('format', 'png')
        if format not in ['png', 'jpg', 'jpeg']:
            abort(400, "Invalid format. Supported formats are png, jpg, jpeg")

        # Adding a delay
        delay = request.args.get('delay', default=0, type=int)
        if delay < 0:
            abort(400, "Invalid delay. Delay must be a non-negative integer")

        # Setup Selenium with headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        driver = webdriver.Chrome(options=chrome_options)

        try:
            driver.get(url)
            time.sleep(delay)  # Adding a delay here
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
            driver.save_screenshot(temp_file.name)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            abort(500, "An error occurred while taking the screenshot")
        finally:
            driver.quit()

        # Serve the screenshot file
        try:
            response = send_file(temp_file.name, mimetype=f'image/{format}', as_attachment=True)
            response.headers["Content-Disposition"] = f"attachment; filename=screenshot.{format}"
            return response
        except Exception as e:
            logging.error(f"An error occurred while sending the file: {str(e)}")
            abort(500, "An error occurred while sending the file")