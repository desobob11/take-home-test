# Order Processing Pipeline Notes

## Assumptions
- Missing "placed_at" dates in ORDERS is not an error, and should not make an order invalid
    - Order ID provides an ordering of records, and "placed_at" is not required for any parts of this exercise
- Rows deemed invalid in Task 1 should be excluded from Tasks 2,3, 4
    - These invalid rows should be exported to a CSV with error messages included for each record
- If an order references a product SKU that does not exist, it is an invalid row and will be excluded as per the above bullet point

## What I Would Do Differently with More Time
1. I would make my validation report give more detailed error messages
    - Explicitly say which field(s) are missing values.
    - Better indicate empty items list vs. NULL SKU/quantities

2. I would handle the ORDERS dataset and nested JSON objects differently I think
    - Forcing the dataset into a flat dataframe worked well for splitting valid and invalid orders
    - It also worked well when producing the reports in Task 3
    - It did NOT work well for producing the desired reports for Task 1 and Task 2

3. Handling missing "placed_at" values in ORDERS
    - Instead of ignoring these, I would find a way to add best-guess values (datetime from record prior or record after)
    - This would help in a situation where "placed_at" is required, such as detailed order breakdowns based on when they were placed.



## One thing I'd Add If This Was a Production System
- I would add a relational database that would house this data
- This would include seeding the CUSTOMERS, PRODUCTS, and ORDERS tables
- Some associative tables would be useful as well
    - A OrderProduct associative table would be useful to deal with 1:many relationship between Orders and Products
    - Fields could be: order_id, product_id, quantity, price
