import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

def start_scheduler():
    """
    Start the background scheduler for periodic data updates and email delivery.
    """
    logger.info("Starting background scheduler")
    
    scheduler = BackgroundScheduler()
    
    # Import functions here to avoid circular imports
    from binance_api import fetch_latest_binance_data
    from data_processor import save_price_data, save_price_data_as_excel
    
    def scheduled_data_update():
        """Function to run on schedule for updating data."""
        try:
            # When running as a job, get fresh app_context to avoid "Working outside of application context" error
            from app import app
            with app.app_context():
                try:
                    logger.info("Running scheduled data update")
                    # Fetch latest data
                    latest_data = fetch_latest_binance_data()
                    
                    # Save to price history
                    save_price_data(latest_data)
                    
                    # Save to Excel once a day (every 24 hours)
                    current_hour = int(latest_data["timestamp"].split()[1].split(":")[0])
                    if current_hour == 0:  # Midnight
                        save_price_data_as_excel(latest_data)
                        logger.info("Generated daily Excel report")
                    
                    logger.info("Scheduled data update completed successfully")
                except Exception as e:
                    logger.error(f"Error in scheduled data update: {e}")
        except Exception as e:
            logger.error(f"Error creating app context in scheduler: {e}")
    
    def upload_hourly_to_drive():
        """Function to upload the price history JSON file to Google Drive every hour."""
        try:
            # When running as a job, get fresh app_context to avoid "Working outside of application context" error
            from app import app
            with app.app_context():
                try:
                    # Import here to avoid circular imports
                    from google_drive import upload_price_history_to_drive
                    
                    logger.info("Uploading hourly price history to Google Drive")
                    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')  # Get folder ID from environment variables
                    
                    success = upload_price_history_to_drive(folder_id=folder_id)
                    if success:
                        logger.info("Hourly price history uploaded to Google Drive successfully")
                    else:
                        logger.error("Failed to upload hourly price history to Google Drive")
                except Exception as e:
                    logger.error(f"Error in uploading to Google Drive: {e}")
        except Exception as e:
            logger.error(f"Error creating app context in Google Drive upload scheduler: {e}")
    
    # Schedule the data update job to run every 5 minutes
    scheduler.add_job(
        scheduled_data_update,
        trigger=IntervalTrigger(minutes=5),
        id='data_update_job',
        name='Update price data every 5 minutes',
        replace_existing=True
    )
    
    # Schedule the Google Drive upload job to run hourly (at the start of each hour)
    scheduler.add_job(
        upload_hourly_to_drive,
        trigger=CronTrigger(minute=0),  # Run at the 0th minute of every hour
        id='hourly_drive_job',
        name='Upload price history to Google Drive hourly',
        replace_existing=True
    )
    
    # Run the data update job immediately for the first time
    scheduler.add_job(
        scheduled_data_update,
        trigger='date',
        id='initial_data_update',
        name='Initial data update'
    )
    
    # Run the Google Drive upload job immediately for testing
    scheduler.add_job(
        upload_hourly_to_drive,
        trigger='date',
        id='initial_drive_job',
        name='Initial Google Drive upload test'
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Background scheduler started")
    
    return scheduler
