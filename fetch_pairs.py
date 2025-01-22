import os
import ccxt
import requests

def fetch_top_coins_from_coinmarketcap(
    api_key,
    limit=100,
    convert='USD',
    sort='market_cap',
    sort_dir='desc'
):
    """
    Fetch top coins by market cap using CoinMarketCap's /cryptocurrency/listings/latest endpoint.
    
    :param api_key: Your CMC API key
    :param limit: How many coins to fetch (CoinMarketCap allows up to 5000, but free tiers may have other limits)
    :param convert: The fiat or crypto to convert the market cap/price (e.g. 'USD')
    :param sort: Sorting field. 'market_cap' is typical. See docs for other options (volume_24h, cmc_rank, etc.)
    :param sort_dir: 'asc' or 'desc'
    :return: A list of dicts, each containing (at least) { 'symbol': 'BTC', 'cmc_rank': 1, 'quote': {...} }
    """
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    # Required header to pass your CoinMarketCap API key
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    # Query parameters for /cryptocurrency/listings/latest
    params = {
        'start': '1',               # Start at rank 1
        'limit': str(limit),        # e.g. top 100
        'convert': convert,         # e.g. get all data in USD
        'sort': sort,               # sort by 'market_cap'
        'sort_dir': sort_dir,       # 'desc' = descending
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    if 'data' not in data:
        print("Warning: 'data' not found in CoinMarketCap response.")
        return []

    # The 'data' key is a list of coin objects
    return data['data']


def save_top_pairs_by_market_cap(
    cmc_api_key,
    filename='top_pairs.txt',
    limit=120,
    cmc_limit=300
):
    """
    1. Fetch the top cmc_limit coins by market cap from CoinMarketCap.
    2. Load Binance markets, filter only /USDT.
    3. Filter out stablecoin bases (e.g., USDC, FDUSD, etc.).
    4. Write up to 'limit' new pairs to the local file.
    
    :param cmc_api_key: Your CoinMarketCap API key (string)
    :param filename: File to store results
    :param limit: How many pairs to write at most
    :param cmc_limit: How many coins to retrieve from CoinMarketCap
    """
    # --- 1) Fetch top coins from CoinMarketCap ---
    cmc_coins = fetch_top_coins_from_coinmarketcap(
        api_key=cmc_api_key,
        limit=cmc_limit,      # how many coins to fetch from CMC
        convert='USD',
        sort='market_cap',    # sort by market cap
        sort_dir='desc'       # descending
    )

    # --- 2) Load Binance markets & filter for USDT pairs ---
    exchange = ccxt.binance({'enableRateLimit': True})
    exchange.load_markets()

    binance_markets = [m for m in exchange.markets if m.endswith("/USDT")]
    # We'll create a set of base symbols for quick membership checks
    binance_bases = {m.split("/")[0].upper() for m in binance_markets}

    # A set of stablecoin symbols (you can expand this as you see fit)
    stablecoins = {
        "USDT", "BUSD", "USDC", "TUSD", "USDP", 
        "DAI", "FDUSD", "PAX", "UST", "USDD"
    }

    # --- 3) Match CMC coins to Binance pairs and filter out stablecoin bases ---
    matched_pairs = []
    for coin in cmc_coins:
        symbol_upper = coin['symbol'].upper()  # e.g. "BTC"
        # 3a) Skip stablecoins like USDC, FDUSD, etc.
        if symbol_upper in stablecoins:
            continue

        # 3b) If it's on Binance as /USDT, add to matched pairs
        if symbol_upper in binance_bases:
            pair = f"{symbol_upper}/USDT"
            matched_pairs.append(pair)

    # Keep only the first 'limit' results
    matched_pairs = matched_pairs[:limit]

    # --- 4) Read existing pairs from the file (if it exists) ---
    existing_pairs = set()
    try:
        with open(filename, 'r') as file:
            existing_pairs = {line.strip() for line in file}
    except FileNotFoundError:
        print(f"No existing file found. Creating new file: {filename}")

    # Identify only new pairs
    new_pairs = [p for p in matched_pairs if p not in existing_pairs]

    # --- 5) Write new pairs to the file ---
    if new_pairs:
        with open(filename, 'a') as file:
            for pair in new_pairs:
                file.write(pair + '\n')
        print(f"Added {len(new_pairs)} new pairs to {filename}")
    else:
        print("No new pairs to add.")


if __name__ == '__main__':
    # Example usage:
    #  1) Set your CoinMarketCap API key
    #  2) Fetch top 300 coins by market cap from CMC
    #  3) Filter stablecoin bases & match to Binance /USDT
    #  4) Write the first 120 matched pairs to top_pairs.txt
    
    CMC_API_KEY = os.environ.get('CMC_API_KEY', 'xxxx')

    save_top_pairs_by_market_cap(
        cmc_api_key=CMC_API_KEY,
        filename='top_pairs.txt',
        limit=120,
        cmc_limit=300
    )
