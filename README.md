# Portfolio Optimizer
The portfolio optimizer takes a CSV file with the following information:
* Asset class allocations for each fund
* Target asset class allocations

It produces allocation percentages for each fund that minimizes the difference
between the target asset class allocations and the asset class allocations for
the portfolio.

Additional arguments can be provided to influence the fund allocation produced:
* Sparsity weight - weight used to penalize portfolios with a larger number
  of funds, this can help prevent very small allocations to funds
* Max funds - the maximum number of fund to include in the final portfolio
* Fund list - specify a subset of funds that should be considered for
  inclusion in the final portfolio

Only asset class allocation is considered when generating an optimal portfolio.
Other criteria such as fund performance, detailed fund composition or fees are 
not considered.

## Running the Optimizer
Enter a command similar to the following to run the optimizer:
```
python portopt.py my-fund-matrix.csv --mf 6
```
To get help with additional program options, enter the following command:
```
python portopt.py -h
```

# File Format
The CSV file should have the following format.
## Columns
* Ticker (Required) - column that contains the ticker for each fund or the word
  "Targets" for the row that contains the target asset class allocation
* Name (Optional) - column that contains the name of the fund (this column is
  ignored by the optimizer)
* Description (Optional) - column that contains a description of the fund (this
  column is ignored by the optimizer)
* <Asset Class> - one column for each asset class

## Rows
* Initial row contains the names of the columns
* Each row with a fund ticker in the first column contains the asset class
  allocations for that fund
* A row with "Targets" in the first column that contains the target asset
  class allocations

The asset class allocations are provide as percentages in decimal format.  For
example, if the asset class allocation is 13.4% then the cvalue in the CSV file
will be 0.134.

# Additioan Information
The portfolio optimization problem has the following features:
* quadratic objective function to minimize the sum of the squared difference
between the target asset class allocation and the actual asset class allocation
* mixed-integer variables to minimize the number of funds and optionally limit
the number of funds to a specified maximum
* linear constraints to enforce certain properties such as forcing the overall
asset class allocation to sum to 100% and the allocation to any particular asset
class or fund to be less than 100%

Since the portfolio optimizatin problem requires minimizing a quadratic
objective function and has some variables that are restricted to being integers,
the problem falls into the category of mixed-integer quadratic programming
(MIQP) problems.