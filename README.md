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