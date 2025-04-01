import os
import json
import pandas as pd
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Path to store data files
DATA_DIR = "static/data"
HISTORY_FILE = os.path.join(DATA_DIR, "price_history.json")
EXCEL_DIR = "excel_exports"

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXCEL_DIR, exist_ok=True)

def save_price_data(data):
    """
    Save the latest price data to the price history JSON file.
    
    Args:
        data (dict): The latest price data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get existing history
        history = get_price_history()
        
        # Add new data point
        new_data_point = {
            "timestamp": data["timestamp"],
            "buy_price": data["buy_price"],
            "sell_price": data["sell_price"],
            "spread": data["spread"]
        }
        
        history.append(new_data_point)
        
        # Keep only the last 168 data points (7 days of hourly data)
        if len(history) > 168:
            history = history[-168:]
        
        # Save back to file
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            
        logger.debug(f"Saved price data point for {data['timestamp']}")
        return True
    except Exception as e:
        logger.error(f"Error saving price data: {e}")
        return False

def get_price_history():
    """
    Get the price history from the JSON file.
    
    Returns:
        list: List of historical price data points
    """
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        logger.error(f"Error reading price history: {e}")
        return []

def save_price_data_as_excel(data, time_period=None):
    """
    Save all the available price data to an Excel file, with option to filter by time period.
    
    Args:
        data (dict): The current price data to save
        time_period (str, optional): Time period to filter by ('hour', 'day', 'month', or None for all)
        
    Returns:
        str: Path to the saved Excel file
    """
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(EXCEL_DIR):
            os.makedirs(EXCEL_DIR)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Add time period to filename if specified
        time_label = ""
        if time_period == 'hour':
            time_label = "hourly"
        elif time_period == 'day':
            time_label = "daily"
        elif time_period == 'month':
            time_label = "monthly"
        else:
            time_label = "complete"
            
        filename = f"USDT_SDG_prices_{time_label}_{timestamp}.xlsx"
        filepath = os.path.join(EXCEL_DIR, filename)
        
        # Create DataFrames for current buy and sell offers
        buy_offers_data = []
        for offer in data.get("buy_offers", []):
            try:
                advertiser = offer.get("advertiser", {})
                adv = offer.get("adv", {})
                
                # Convert data types to string to avoid type issues
                buy_offers_data.append({
                    "Timestamp": str(data.get("timestamp", "N/A")),
                    "Advertiser": str(advertiser.get("nickName", "N/A")),
                    "Price": str(adv.get("price", "N/A")),
                    "Available Quantity": str(adv.get("tradableQuantity", "N/A")),
                    "Min Order": str(adv.get("minSingleTransAmount", "N/A")),
                    "Max Order": str(adv.get("maxSingleTransAmount", "N/A")),
                    "Payment Methods": str(", ".join([str(pm.get("payType", "N/A")) for pm in adv.get("tradeMethods", [])])),
                    "Is Merchant": "Yes" if advertiser.get("userType") == "merchant" else "No"
                })
            except Exception as e:
                logger.error(f"Error processing buy offer: {e}")
                continue
            
        sell_offers_data = []
        for offer in data.get("sell_offers", []):
            try:
                advertiser = offer.get("advertiser", {})
                adv = offer.get("adv", {})
                
                # Convert data types to string to avoid type issues
                sell_offers_data.append({
                    "Timestamp": str(data.get("timestamp", "N/A")),
                    "Advertiser": str(advertiser.get("nickName", "N/A")),
                    "Price": str(adv.get("price", "N/A")),
                    "Available Quantity": str(adv.get("tradableQuantity", "N/A")),
                    "Min Order": str(adv.get("minSingleTransAmount", "N/A")),
                    "Max Order": str(adv.get("maxSingleTransAmount", "N/A")),
                    "Payment Methods": str(", ".join([str(pm.get("payType", "N/A")) for pm in adv.get("tradeMethods", [])])),
                    "Is Merchant": "Yes" if advertiser.get("userType") == "merchant" else "No"
                })
            except Exception as e:
                logger.error(f"Error processing sell offer: {e}")
                continue
        
        buy_df = pd.DataFrame(buy_offers_data)
        sell_df = pd.DataFrame(sell_offers_data)
        
        # Get ALL historical data
        history = get_price_history()
        
        # Create a more comprehensive summary DataFrame with all historical data points
        summary_data = []
        for point in history:
            try:
                # Convert numeric values to strings to avoid type issues
                summary_data.append({
                    "Timestamp": str(point.get("timestamp", "N/A")),
                    "Buy Price (SDG)": str(point.get("buy_price", "N/A")),
                    "Sell Price (SDG)": str(point.get("sell_price", "N/A")),
                    "Spread (SDG)": str(point.get("spread", "N/A")),
                })
            except Exception as e:
                logger.error(f"Error processing history point: {e}")
                continue
        
        # Add current data point if not already in history
        if not any(item.get("Timestamp") == str(data.get("timestamp")) for item in summary_data):
            summary_data.append({
                "Timestamp": str(data.get("timestamp", "N/A")),
                "Buy Price (SDG)": str(data.get("buy_price", "N/A")),
                "Sell Price (SDG)": str(data.get("sell_price", "N/A")),
                "Spread (SDG)": str(data.get("spread", "N/A")),
            })
            
        # Sort by timestamp
        summary_data.sort(key=lambda x: x["Timestamp"])
        
        # Filter data by time period if specified
        if time_period:
            from datetime import datetime, timedelta
            
            # Convert timestamps to datetime objects for comparison
            filtered_data = []
            current_time = datetime.now()
            
            for item in summary_data:
                try:
                    # Parse timestamp string to datetime
                    item_time = datetime.strptime(item["Timestamp"], "%Y-%m-%d %H:%M:%S")
                    
                    # Filter based on time period
                    if time_period == 'hour' and item_time >= (current_time - timedelta(hours=1)):
                        filtered_data.append(item)
                    elif time_period == 'day' and item_time >= (current_time - timedelta(days=1)):
                        filtered_data.append(item)
                    elif time_period == 'month' and item_time >= (current_time - timedelta(days=30)):
                        filtered_data.append(item)
                except Exception as e:
                    logger.error(f"Error parsing timestamp for filtering: {e}")
                    # Include items with invalid timestamps
                    filtered_data.append(item)
            
            # Use filtered data
            summary_data = filtered_data
            
        summary_df = pd.DataFrame(summary_data)
        
        # Current data summary for quick reference
        current_summary_data = [{
            "Timestamp": str(data.get("timestamp", "N/A")),
            "Average Buy Price (SDG)": str(data.get("buy_price", "N/A")),
            "Average Sell Price (SDG)": str(data.get("sell_price", "N/A")),
            "Spread (SDG)": str(data.get("spread", "N/A")),
            "Buy Offers Count": str(data.get("buy_offers_count", 0)),
            "Sell Offers Count": str(data.get("sell_offers_count", 0))
        }]
        current_summary_df = pd.DataFrame(current_summary_data)
        
        # Create Excel file with multiple sheets
        try:
            # Create a writer object with explicit engine specification
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # First sheet - Historical data (with period in name if filtered)
                sheet_name = 'Historical Data'
                if time_period == 'hour':
                    sheet_name = 'Last Hour Data'
                elif time_period == 'day':
                    sheet_name = 'Last 24 Hours Data'
                elif time_period == 'month':
                    sheet_name = 'Last 30 Days Data'
                    
                summary_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Second sheet - Current summary
                current_summary_df.to_excel(writer, sheet_name='Current Summary', index=False)
                
                # Buy and sell offers
                buy_df.to_excel(writer, sheet_name='Current Buy Offers', index=False)
                sell_df.to_excel(writer, sheet_name='Current Sell Offers', index=False)
            
            # Verify the file was created successfully
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"Saved complete price data to Excel file: {filepath}")
                return filepath
            else:
                logger.error("Excel file was not created successfully")
                raise Exception("Excel file was not created successfully")
        except Exception as excel_error:
            logger.error(f"Error writing Excel file: {excel_error}")
            raise
    except Exception as e:
        logger.error(f"Error saving to Excel: {e}")
        raise
