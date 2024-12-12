# Portfolio Optimizer
The **Portfolio Optimizer** helps users generate an optimal investment portfolio
by balancing fund allocations to match desired asset class targets. The tool
takes a CSV file with fund asset class allocations and target asset class
allocations and produces optimal allocation percentages for each fund. The
optimization minimizes the difference between the target asset class allocations
and the final portfolio’s asset class allocations.

## Features

The optimization process includes:
- **Quadratic Objective Function**: Minimizes the sum of squared differences
between the target and portfolio asset class allocations.
- **Mixed-Integer Variables**: Minimizes the number of funds and optionally
enforces a limit on the number of funds.
- **Linear Constraints**: Ensures the overall portfolio allocation sums to 100%,
with no single fund allocated more than 100%.

Other factors, such as fund performance, fees, or detailed composition, are not
included in the optimization process.

## Additional Arguments
The following additional arguments can be provided to tailor the output to meet
your needs:

* **Sparsity Weight** (`-sw`): This regularization parameter encourages a
sparse, compact portfolio by penalizing allocations across numerous funds. It
promotes selecting a smaller, well-curated subset of funds, reducing negligible
or fragmented investments to create a portfolio that is both less complex and
easier to manage.
* **Maximum Funds** (`-mf`): This parameter sets a hard limit on the number of
funds that can be included in the portfolio. Unlike the sparsity weight, which
uses a penalty to encourage fewer allocations, this constraint enforces an
explicit maximum, ensuring that the portfolio does not exceed the specified
number of funds.
* **Fund List** (`-f`): Specifies a subset of funds to be considered for
portfolio construction. This allows the exclusion of certain funds without
modifying the input data file, enabling the portfolio to be tailored to
specific requirements or preferences.

## Installing the Optimizer
First install Python: [Python Downloads](https://www.python.org/downloads/).

Use [pipenv](https://pipenv.pypa.io/en/latest/) to install the required Python
dependencies.
```
pipenv install
```

## Running the Optimizer
Enter a command similar to the following to run the optimizer:
```
python portopt.py ../data/example_fund_matrix.csv -mf 6
```
To get help with additional program options, enter the following command:
```
python portopt.py -h
```

# File Format
The CSV file should have the following format.
## Columns
* Ticker (Required) - contains the ticker for each fund or the word
  "Targets" for the row that contains the target asset class allocation
* Name (Optional) - contains the name of the fund (this column is
  ignored by the optimizer)
* Description (Optional) - contains a description of the fund (this
  column is ignored by the optimizer)
* Asset Class Name (Required) - one column for each asset class

## Rows
* Initial row contains the names of the columns
* Each row with a fund ticker in the first column contains the asset class
  allocations for that fund
* A row with "Targets" in the first column that contains the target asset
  class allocations

The asset class allocations are provided as percentages in decimal format.  For
example, if the asset class allocation is 13.4% then the value in the CSV file
will be 0.134.

The `data/example_fund_matrix.csv` file provides an example of a properly
formatted CSV file.

# Additioal Information
The portfolio optimization problem has the following features:
* quadratic objective function to minimize the sum of the squared difference
between the target asset class allocation and the asset class allocation of
the final portfolio
* mixed-integer variables to minimize the number of funds and optionally limit
the number of funds to a specified maximum
* linear constraints to enforce certain properties such as forcing the overall
asset class allocation to sum to 100% and the allocation to any particular asset
class or fund to be less than 100%

Since the portfolio optimizatin problem requires minimizing a quadratic
objective function and has some variables that are restricted to being integers,
the problem falls into the category of mixed-integer quadratic programming
(MIQP) problems.