import os
import logging
from flask_mail import Mail, Message
from flask import current_app
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask-Mail
mail = Mail()

def init_mail(app):
    """
    Initialize the mail extension with the Flask app
    """
    # Configure mail settings
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

    # Initialize mail
    mail.init_app(app)
    logger.info("Mail extension initialized")

def send_price_history_email(recipient="1mujmax@gmail.com"):
    """
    Send the price_history.json file as an attachment to the specified email address
    
    Args:
        recipient (str): The email address to send the file to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        price_history_path = os.path.join('static', 'data', 'price_history.json')
        
        # Check if the file exists and is not empty
        if not os.path.exists(price_history_path) or os.path.getsize(price_history_path) == 0:
            logger.error(f"Price history file not found or empty at {price_history_path}")
            return False
        
        # Read the file to make sure it's valid JSON
        with open(price_history_path, 'r') as f:
            json_data = json.load(f)
            if not json_data:
                logger.error("Price history file contains empty JSON data")
                return False
        
        # Create email message
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        msg = Message(
            subject=f"USDT/SDG Price History Data - {timestamp}",
            recipients=[recipient],
            body=f"Please find attached the latest USDT/SDG price history data as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
        
        # Attach the file
        with open(price_history_path, 'rb') as f:
            msg.attach(
                filename=f"price_history_{timestamp}.json",
                content_type="application/json",
                data=f.read()
            )
        
        # Send the email
        mail.send(msg)
        logger.info(f"Price history file sent successfully to {recipient}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending price history email: {str(e)}")
        return False