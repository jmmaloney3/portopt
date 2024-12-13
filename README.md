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
1. Install Python: [Python Downloads](https://www.python.org/downloads/).
2. Clone or download this repository.
3. Navigate to the project directory in your terminal.
4. Use [pipenv](https://pipenv.pypa.io/en/latest/) to install dependencies:
   ```bash
   pipenv install
   ```

## Running the Optimizer
Enter a command similar to the following to run the optimizer:
```bash
python portopt.py ../data/example_fund_matrix.csv -mf 6
```
This example command uses the `-mf` option to limit the number of funds included
in the final portfolio.  To get help with additional program options, enter the following command:
```bash
python portopt.py -h
```

# File Format
The CSV file should have the following format.
## Columns
* **Ticker** (Required): Fund ticker or “Targets” for target allocations.
* **Name** (Optional): Fund name (ignored by the optimizer)
* **Description** (Optional): Fund description(this ignored by the optimizer)
* **Asset Class Name** (Required): One column per asset class

## Rows
* The first row contains column headers.
* Each subsequent row provides fund allocations, where percentages are represented as decimals (e.g., 13.4% → 0.134).

## CSV Examples
The following is an example of a properly formatted CSV file:

```csv
Ticker,Name,Description,Equities,Bonds,Cash
FundA,Fund A Name,Large-Cap Fund,0.7,0.2,0.1
FundB,Fund B Name,Government Bonds,0.1,0.9,0.0
Targets,,,,0.6,0.3,0.1
```

A more extensive example is provided by the
[example_fund_matrix.csv](https://github.com/jmmaloney3/portopt/blob/main/data/example_fund_matrix.csv)
file.

# Additional Information
The portfolio optimization problem has the following features:
* **Quadratic Objective Function**: Minimizes the sum of squared differences between portfolio and target allocations.
* **Mixed-Integer Variables**: Reduces the number of funds used and enforces maximum fund limits.
* **Linear Constraints**: Ensures total allocation sums to 100% and the
individual fund allocations are between 0% and 100%.

This is a Mixed-Integer Quadratic Programming (MIQP) problem and [SCIP](https://scipopt.org) is used to solve the problem.