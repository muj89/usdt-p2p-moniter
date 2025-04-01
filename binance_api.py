import requests
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def fetch_binance_p2p_data(asset, fiat, trade_type, rows=20):
    """
    Fetch data from Binance P2P API.
    
    Args:
        asset (str): The cryptocurrency asset (e.g., 'USDT')
        fiat (str): The fiat currency (e.g., 'SDG')
        trade_type (str): 'BUY' or 'SELL'
        rows (int): Number of rows to fetch
        
    Returns:
        list: List of advertisements
    """
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    payload = {
        "asset": asset,
        "fiat": fiat,
        "merchantCheck": False,
        "page": 1,
        "rows": rows,
        "tradeType": trade_type
    }
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        result = response.json()
        if "data" in result:
            return result["data"]
        else:
            logger.error(f"Unexpected response format: {result}")
            return []
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Binance P2P API: {e}")
        raise

def filter_offers(offers):
    """
    Filter offers to include only those where the advertiser is a merchant or the tradable quantity is greater than 1000.
    
    Args:
        offers (list): List of advertisements
        
    Returns:
        list: Filtered list of advertisements
    """
    filtered_offers = []
    
    for offer in offers:
        advertiser = offer.get("advertiser", {})
        adv_details = offer.get("adv", {})
        
        is_merchant = advertiser.get("userType") == "merchant"
        tradable_quantity = float(adv_details.get("tradableQuantity", 0))
        
        if is_merchant or tradable_quantity > 1000:
            filtered_offers.append(offer)
    
    return filtered_offers

def calculate_average_price(offers):
    """
    Calculate the average price from a list of offers.
    
    Args:
        offers (list): List of advertisements
        
    Returns:
        float: Average price
    """
    if not offers:
        return 0
    
    total_price = 0
    for offer in offers:
        adv_details = offer.get("adv", {})
        price = float(adv_details.get("price", 0))
        total_price += price
    
    return total_price / len(offers)

def fetch_latest_binance_data(asset="USDT", fiat="SDG"):
    """
    Fetch and process the latest data from Binance P2P.
    
    Args:
        asset (str): The cryptocurrency asset (e.g., 'USDT', 'BTC', 'ETH', etc.)
        fiat (str): The fiat currency (e.g., 'SDG', 'USD', 'EUR', etc.)
    
    Returns:
        dict: Processed data containing buy and sell prices, trends, etc.
    """
    # Fetch data for both BUY and SELL
    buy_offers = fetch_binance_p2p_data(asset, fiat, "BUY")
    sell_offers = fetch_binance_p2p_data(asset, fiat, "SELL")
    
    # Filter offers
    filtered_buy_offers = filter_offers(buy_offers)
    filtered_sell_offers = filter_offers(sell_offers)
    
    # Calculate average prices
    avg_buy_price = calculate_average_price(filtered_buy_offers)
    avg_sell_price = calculate_average_price(filtered_sell_offers)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Return processed data
    return {
        "timestamp": timestamp,
        "asset": asset,
        "fiat": fiat,
        "buy_price": avg_buy_price,
        "sell_price": avg_sell_price,
        "spread": avg_sell_price - avg_buy_price,
        "buy_offers_count": len(filtered_buy_offers),
        "sell_offers_count": len(filtered_sell_offers),
        "buy_offers": filtered_buy_offers[:5],  # Include top 5 buy offers
        "sell_offers": filtered_sell_offers[:5],  # Include top 5 sell offers
    }

def fetch_multi_asset_data():
    """
    Fetch data for multiple cryptocurrency assets against the SDG.
    
    Returns:
        dict: Data for multiple assets including USDT, BTC, and others
    """
    # Define assets to fetch
    assets = ["USDT", "BTC", "ETH", "BNB"]
    fiat = "SDG"
    
    # Get current timestamp for all assets
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Fetch and process data for each asset
    assets_data = {}
    for asset in assets:
        try:
            data = fetch_latest_binance_data(asset, fiat)
            assets_data[asset] = data
        except Exception as e:
            logger.error(f"Error fetching data for {asset}/{fiat}: {e}")
            # Add empty data with zeros to maintain structure
            assets_data[asset] = {
                "timestamp": timestamp,
                "asset": asset,
                "fiat": fiat,
                "buy_price": 0,
                "sell_price": 0,
                "spread": 0,
                "buy_offers_count": 0,
                "sell_offers_count": 0,
                "buy_offers": [],
                "sell_offers": []
            }
    
    # Return all data
    return {
        "timestamp": timestamp,
        "assets_data": assets_data,
        "primary_asset": "USDT"  # The default asset for the main display
    }
