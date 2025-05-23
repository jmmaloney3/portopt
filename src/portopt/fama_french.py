import pandas as pd

def load_ff_3factor_daily(csv_path: str = "../data/fama-french/F-F_Research_Data_Factors_daily.CSV") -> pd.DataFrame:
    """
    Load the Fama-French 3-factor daily data from the specified CSV file.

    The CSV file is assumed to have 4 rows at the beginning that should be skipped.
    The 5th row contains the column headers. If the first column header is not "Date",
    it will be renamed to "Date". The "Date" column contains dates in YYYYMMDD format,
    which are converted to a datetime index.

    **Important:**
    - The factor values are provided as percentages (e.g., 0.25 corresponds
      to 0.25%) and are converted to decimals (i.e., 0.0025) by dividing by 100.
    - Any rows with NaT (Not a Time) values in the index are removed.

    Args:
        csv_path: Path to the F-F_Research_Data_Factors_daily.CSV file.

    Returns:
        DataFrame indexed by Date with all available factor columns converted to decimal values.
        Rows with NaT index values are removed.
    """

    # Read the CSV file while skipping the first 4 rows.
    df = pd.read_csv(csv_path, skiprows=4, header=0)

    # Strip whitespace from column names.
    df.columns = [str(col).strip() for col in df.columns]

    # If the first column is not "Date", rename it to "Date".
    if df.columns[0] != "Date":
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)

    # Convert the "Date" column from YYYYMMDD format to a datetime object and set it as the index.
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d", errors="coerce")
    df.set_index("Date", inplace=True)

    # Remove any rows where the index is NaT
    df = df[df.index.notna()]

    # Convert the factor values from percentages to decimals by dividing by 100.
    for col in df.columns:
        df[col] = df[col] / 100.0

    return df

def asset_class_proxy_returns(factor_data: pd.DataFrame,
                              beta_m: float,
                              beta_s: float,
                              beta_v: float) -> pd.Series:
    """
    Create an equity asset class proxy returns series using Fama-French factors.

    The proxy is computed as a linear combination of the Fama-French factors:

        proxy_returns = beta_m * factor_data['Mkt-RF']
                      + beta_s * factor_data['SMB']
                      + beta_v * factor_data['HML']
                      + factor_data['RF']

    The risk-free rate is added back to the combination.

    Parameters:
        factor_data : pd.DataFrame
            DataFrame containing values for the FF factors. It is expected to have the following columns:
                - 'Mkt-RF' : Market risk premium.
                - 'SMB'    : Size factor.
                - 'HML'    : Value factor.
                - 'RF'     : Risk-free rate.
        beta_m : float
            Coefficient for the Mkt-RF factor.
        beta_s : float
            Coefficient for the SMB factor.
        beta_v : float
            Coefficient for the HML factor.

    Returns:
        pd.Series
            A time series of proxy returns indexed by Date.
    """
    proxy_returns = beta_m * factor_data['Mkt-RF'] + beta_s * factor_data['SMB'] + beta_v * factor_data['HML']
    proxy_returns += factor_data['RF']
    return proxy_returns

def asset_class_proxy_prices(factor_data: pd.DataFrame,
                             beta_m: float,
                             beta_s: float,
                             beta_v: float,
                             initial_price: float = 100.0) -> pd.Series:
    """
    Create an asset class proxy prices time series using Fama-French factors.

    The function computes a proxy returns series based on the linear combination:

        proxy_returns = beta_m * factor_data['Mkt-RF']
                      + beta_s * factor_data['SMB']
                      + beta_v * factor_data['HML']
                      + factor_data['RF']

    Factor values are assumed to be in decimal form (e.g., 0.0025 for 0.25%).
    The simulated price series is then generated by compounding these returns from an
    initial price:

        proxy_prices = initial_price * (1 + proxy_returns).cumprod()

    Parameters:
        factor_data : pd.DataFrame
            DataFrame containing values for the Fama-French factors. Expected columns:
                - 'Mkt-RF'
                - 'SMB'
                - 'HML'
                - 'RF'
        beta_m : float
            Coefficient for the Mkt-RF factor.
        beta_s : float
            Coefficient for the SMB factor.
        beta_v : float
            Coefficient for the HML factor.
        initial_price : float, optional
            The starting price for the simulation (default is 100).

    Returns:
        pd.Series:
            A time series of simulated asset class prices indexed by Date.
    """
    # Compute the proxy returns using the existing function.
    returns_series = asset_class_proxy_returns(factor_data, beta_m, beta_s, beta_v)

    # Calculate the simulated price series by compounding the returns.
    prices = initial_price * (1 + returns_series).cumprod()

    return prices

def multi_asset_class_proxy_returns(factor_data: pd.DataFrame,
                                    coeff_dict: dict) -> pd.DataFrame:
    """
    Compute proxy returns for multiple asset classes using Fama-French factors.

    For each asset class present in coeff_dict, this function computes a time series
    of proxy returns using the linear combination:

        proxy_returns = beta_m * factor_data['Mkt-RF'] 
                      + beta_s * factor_data['SMB']
                      + beta_v * factor_data['HML']
                      + factor_data['RF']

    The factor values are assumed to be in decimal form as loaded by `load_ff_3factor_daily`.

    Parameters:
        factor_data : pd.DataFrame
            DataFrame containing values for the Fama-French factors. It is expected to include:
                - 'Mkt-RF'
                - 'SMB'
                - 'HML'
                - 'RF'
        coeff_dict : dict
            A dictionary mapping asset class names to coefficient dictionaries. Each of these should have:
                - 'beta_m': Coefficient for the Mkt-RF factor.
                - 'beta_s': Coefficient for the SMB factor.
                - 'beta_v': Coefficient for the HML factor.

            Example:
            {
                "Small Cap": {"beta_m": 1.0, "beta_s": 1.2, "beta_v": 0.8},
                "Large Cap": {"beta_m": 1.0, "beta_s": 0.9, "beta_v": 0.5}
            }

    Returns:
        pd.DataFrame:
            A DataFrame with each column representing the proxy returns for an asset class.
            The DataFrame is indexed by Date.
    """
    asset_returns = {}

    # Loop over each asset class and its coefficients.
    for asset_class, params in coeff_dict.items():
        beta_m = params.get("beta_m", 0)
        beta_s = params.get("beta_s", 0)
        beta_v = params.get("beta_v", 0)
        asset_returns[asset_class] = asset_class_proxy_returns(factor_data, beta_m, beta_s, beta_v)

    # Construct the DataFrame using the Date index from factor_data.
    return pd.DataFrame(asset_returns, index=factor_data.index)

def multi_asset_class_proxy_prices(factor_data: pd.DataFrame,
                                   coeff_dict: dict,
                                   initial_price: float = 100.0) -> pd.DataFrame:
    """
    Compute simulated asset class prices for multiple asset classes using Fama-French factors.
    
    For each asset class in coeff_dict, this function first computes a proxy returns series
    using a linear combination:

        proxy_returns = beta_m * factor_data['Mkt-RF']
                      + beta_s * factor_data['SMB']
                      + beta_v * factor_data['HML']
                      + factor_data['RF']

    Factor values are assumed to be in decimal form, as converted by load_ff_3factor_daily.
    The simulated price series is then generated by compounding the returns from an initial price:

        proxy_prices = initial_price * (1 + proxy_returns).cumprod()

    Parameters:
        factor_data : pd.DataFrame
            DataFrame containing values for the Fama-French factors. Expected columns are:
                - 'Mkt-RF'
                - 'SMB'
                - 'HML'
                - 'RF'
        coeff_dict : dict
            A dictionary mapping asset class names to coefficient dictionaries. Each of these should include:
                - 'beta_m': Coefficient for the Mkt-RF factor.
                - 'beta_s': Coefficient for the SMB factor.
                - 'beta_v': Coefficient for the HML factor.

            Example:
            {
                "Small Cap": {"beta_m": 1.0, "beta_s": 1.2, "beta_v": 0.8},
                "Large Cap": {"beta_m": 1.0, "beta_s": 0.9, "beta_v": 0.5}
            }
        initial_price : float, optional
            The starting price for the simulation (default is 100.0).

    Returns:
        pd.DataFrame:
            A DataFrame with each column representing the simulated asset class prices,
            indexed by Date.
    """
    asset_prices = {}

    # Loop over each asset class and compute its simulated price series.
    for asset_class, params in coeff_dict.items():
        beta_m = params.get("beta_m", 0)
        beta_s = params.get("beta_s", 0)
        beta_v = params.get("beta_v", 0)
        asset_prices[asset_class] = asset_class_proxy_prices(factor_data, beta_m, beta_s, beta_v, initial_price)

    # Construct the DataFrame ensuring it is indexed by Date.
    return pd.DataFrame(asset_prices, index=factor_data.index)
