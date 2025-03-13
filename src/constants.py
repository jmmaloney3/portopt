from dataclasses import dataclass

@dataclass(frozen=True)
class Constants:
    # Constants for standard column names
    TICKER_COL = 'Ticker'
    QUANTITY_COL = 'Quantity'
    ACCOUNT_COL = 'Account'
    ACCOUNT_NAME_COL = 'Account Name'
    ACCOUNT_NUMBER_COL = 'Account Number'
    FACTOR_COL = 'Factor'
    FACTOR_NAME_COL = 'Factor Name'
    FACTOR_LEVEL_COL = 'Factor Level'
    FACTOR_WEIGHT_COL = 'Factor Weight'
