import os
import logging
from flask import Flask, render_template, jsonify
from scheduler import start_scheduler

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Import routes after app is created to avoid circular imports
from binance_api import fetch_latest_binance_data, fetch_multi_asset_data
from data_processor import get_price_history, save_price_data_as_excel

@app.route('/')
def index():
    """Render the main dashboard page."""
    try:
        # Get the latest data for initial page load
        latest_data = fetch_latest_binance_data()
        return render_template('index.html', latest_data=latest_data)
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        return render_template('index.html', error=str(e))

@app.route('/api/latest-data')
def get_latest_data():
    """API endpoint to get the latest price data."""
    try:
        from flask import request
        
        # Get asset and fiat if provided
        asset = request.args.get('asset', 'USDT')
        fiat = request.args.get('fiat', 'SDG')
        
        latest_data = fetch_latest_binance_data(asset, fiat)
        return jsonify(latest_data)
    except Exception as e:
        logger.error(f"Error fetching latest data: {e}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/multi-asset-data')
def get_multi_asset_data():
    """API endpoint to get data for multiple assets."""
    try:
        multi_data = fetch_multi_asset_data()
        return jsonify(multi_data)
    except Exception as e:
        logger.error(f"Error fetching multi-asset data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/price-history')
def price_history():
    """API endpoint to get historical price data."""
    try:
        history = get_price_history()
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error fetching price history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download-excel', methods=['GET'])
def download_excel():
    """Trigger the generation of an Excel file with historical data, filtered by time period if specified."""
    try:
        from flask import request
        
        # Get time period parameter from query string (if provided)
        time_period = request.args.get('period')
        
        # Fetch latest data and save to Excel with appropriate filtering
        latest_data = fetch_latest_binance_data()
        excel_path = save_price_data_as_excel(latest_data, time_period)
        
        # Make sure the Excel file was created successfully
        if not os.path.exists(excel_path) or os.path.getsize(excel_path) == 0:
            raise Exception("فشل في إنشاء ملف Excel. يرجى المحاولة مرة أخرى.")
        
        # Create appropriate message based on time period
        period_message = ""
        if time_period == 'hour':
            period_message = " (آخر ساعة)"
        elif time_period == 'day':
            period_message = " (آخر 24 ساعة)"
        elif time_period == 'month':
            period_message = " (آخر 30 يوم)"
        
        # Return success message with the path where the Excel file was saved
        relative_path = excel_path.replace(os.getcwd(), '').lstrip('/')
        return jsonify({
            "success": True, 
            "message": f"تم حفظ ملف Excel{period_message} بنجاح في {relative_path}",
            "path": relative_path
        })
    except Exception as e:
        logger.error(f"Error generating Excel file: {e}")
        return jsonify({"error": f"حدث خطأ: {str(e)}"}), 500

@app.route('/api/upload-to-drive')
def upload_to_drive():
    """API endpoint to manually trigger uploading the price history JSON file to Google Drive."""
    try:
        # Import here to avoid circular imports
        from google_drive import upload_price_history_to_drive
        
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        success = upload_price_history_to_drive(folder_id=folder_id)
        
        if success:
            return jsonify({
                "success": True, 
                "message": "تم رفع ملف التاريخ بنجاح إلى Google Drive"
            })
        else:
            return jsonify({
                "success": False, 
                "message": "فشل في رفع الملف إلى Google Drive. تحقق من الإعدادات."
            }), 500
    except Exception as e:
        logger.error(f"Error uploading to Google Drive: {e}")
        return jsonify({"error": f"حدث خطأ: {str(e)}"}), 500

# No longer need to initialize mail service as we're using Google Drive now

# Start the scheduler when the app starts
with app.app_context():
    start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
