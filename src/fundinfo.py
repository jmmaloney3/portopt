import yfinance as yf
import pandas as pd
import numpy as np
import argparse
from utils import write_table

def get_fund_info(tickers):
    # Initialize lists to store data
    data = []
    
    for ticker in tickers:
        try:
            # Fetch fund info
            fund = yf.Ticker(ticker)
            info = fund.info
            
            # Get fund type and category
            fund_type = info.get('quoteType', 'N/A')
            fund_name = info.get('shortName', 'N/A')
            category = info.get('category', 'N/A')
            
            # Get expense ratio
            exp_ratio = info.get('annualReportExpenseRatio', 
                               info.get('totalExpenseRatio', np.nan))
            if exp_ratio:
                exp_ratio = exp_ratio * 100  # Convert to percentage
            
            # Get historical performance and current price
            hist = fund.history(period="max")
            
            # Get current price (most recent price available)
            current_price = info.get('regularMarketPrice',  # Current price if market open
                                   info.get('previousClose',  # Previous close if market closed
                                          hist['Close'].iloc[-1]))  # Fallback to historical
            
            # Get inception date
            inception_date = hist.index[0].strftime('%Y-%m-%d')
            
            # Calculate returns for different periods
            periods = {
                '1Y': {'days': 252, 'years': 1},    # Trading days in 1 year
                '3Y': {'days': 756, 'years': 3},    # Trading days in 3 years
                '5Y': {'days': 1260, 'years': 5},   # Trading days in 5 years
                '10Y': {'days': 2520, 'years': 10}, # Trading days in 10 years
            }
            
            returns = {}
            for period, info in periods.items():
                if len(hist) >= info['days']:
                    old_price = hist['Close'].iloc[-info['days']]
                    total_return = (current_price - old_price) / old_price
                    # Convert to annualized return
                    annualized_return = (((1 + total_return) ** (1/info['years'])) - 1) * 100
                    returns[period] = annualized_return
                else:
                    returns[period] = np.nan
            
            # Calculate since inception return (annualized)
            first_price = hist['Close'].iloc[0]
            total_return = (current_price - first_price) / first_price
            years_since_inception = (hist.index[-1] - hist.index[0]).days / 365.25
            since_inception = (((1 + total_return) ** (1/years_since_inception)) - 1) * 100
            
            # Compile data using simplified column names
            fund_data = {
                'Ticker': ticker,
                'Name': fund_name,
                'Type': fund_type,
                'Category': category,
                'Price': current_price,  # Add price to the output
                'Inception': inception_date,
                'Exp': round(exp_ratio, 2) if not np.isnan(exp_ratio) else np.nan,
                '1Y': round(returns.get('1Y', np.nan), 2),
                '3Y': round(returns.get('3Y', np.nan), 2),
                '5Y': round(returns.get('5Y', np.nan), 2),
                '10Y': round(returns.get('10Y', np.nan), 2),
                'ALL': round(since_inception, 2)
            }
            
            data.append(fund_data)
            
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
            continue
    
    # Create DataFrame
    df = pd.DataFrame(data)
    return df

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Fetch fund information from Yahoo Finance')
    parser.add_argument('tickers', nargs='+', help='One or more fund tickers')
    parser.add_argument('--output', '-o', help='Output file (CSV format). If not specified, prints to stdout')
    parser.add_argument('--no-header', action='store_true', help='Omit header row in output')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Get fund info
    df = get_fund_info(args.tickers)
    
    # Output results
    if args.output:
        df.to_csv(args.output, index=False, header=not args.no_header)
    else:
        # Column format specifications
        columns = {
            'Ticker':    {'width': 6},
            'Name':      {'width': 25},
            'Category':  {'width': 20},
            'Price':     {'width': 8, 'decimal': 2, 'prefix': '$'},
            '1Y':        {'width': 6, 'suffix': '%'},
            '3Y':        {'width': 6, 'suffix': '%'},
            '5Y':        {'width': 6, 'suffix': '%'},
            '10Y':       {'width': 6, 'suffix': '%'},
            'ALL':       {'width': 6, 'suffix': '%'}
        }
        
        write_table(df, columns=columns)

if __name__ == '__main__':
    main()