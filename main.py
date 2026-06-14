# =============================================================================
# File: OrderProcessingPipeline.py
#
# Author: Desmond OBrien
# =============================================================================


import pandas as pd
import random

CUSTOMER_FILENAME = "customers.json"
ORDERS_FILENAME = "orders.json"
PRODUCTS_FILENAME = "products.csv"

# Products and Customers datasets will be global variables for this exercise
PRODUCTS = None
CUSTOMERS = None

'''============= Task 1 - Ingest and Validate ============='''

def rename_dataset(df_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Prefix all column names in a DataFrame with a dataset identifier.
    This ensures no name column name collisions when joining datasets

    Parameters
    ----------
    df_name : str
        The prefix you would like to use (table name is best)
    df: pd.DataFrame
        The dataset itself

    Returns
    -------
    The same dataset with the columns renamed

    Examples
    --------
    ORDERS.id = orders_id
    CUSTOMERS.id = customers_id
    """

    old_cols = df.columns
    new_cols = [f"{df_name}_{col}" for col in df.columns] # column names with prefixes attached
    rename_dict = dict(zip(old_cols, new_cols))
    return df.rename(columns=rename_dict)


def load_dataset(filename: str, col_to_norm: str | None) -> pd.DataFrame | None:
    """
    Load dataset flat file into a Pandas dataframe. Works with CSV and JSON files.
    If a JSON file contains a nested field, the cross product of that field is computed
    against the records of the table to create rows for each element, as well as columns
    for each item in the element. New column names are normalized

    Parameters
    ----------
    df_name : str
        Name of file to read from
    cols_to_norm: list[str] | None
        List of fields that need to be normalized (ORDERS.items, for example). None if CSV

    Returns
    -------
    A spreadsheet representation of the dataset as a DataFrame
    """

    if ".json" in filename:
        df = pd.read_json(filename)

        if col_to_norm is None:
            return df
        
        df_exploded = df.explode(col_to_norm)  # cross product, create new table rows for nested elements. Elements are in one column
        df_normed = pd.json_normalize(df_exploded[col_to_norm]).set_index(df_exploded.index) # Creates unique columns for each element key
        df = df_exploded.drop(columns=col_to_norm).join(df_normed).drop_duplicates()
        return df
    
    elif ".csv" in filename:
        return pd.read_csv(filename)


def validate_orders(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates the ORDERS dataset. Invalid orders are separated from valid orders
    and moved to a separate dataset

    Parameters
    ----------
    orders: pd.DataFrame
        A dataframe of the raw ORDERS dataset

    Returns
    -------
    A tuple containing two dataframes: The first has valid rows, the second has invalid rows.
    Invalid rows are given error messages as well.
    
    Examples
    --------
    ORDERS.id = orders_id
    CUSTOMERS.id = customers_id
    """

    # columns that NEED non-NULL values
    required_columns = ["orders_id", "orders_customer_id", "orders_sku", "orders_qty"]  # columns that NEED non-NULL values

    missing_data_mask = orders[required_columns].isna().any(axis=1) # filter to get NAN values

    # Some SKUs are referring to product SKUs that do not exist - we need to filter these out as well
    invalid_sku_mask = ~orders["orders_sku"].isin(PRODUCTS["products_sku"])

    valid_mask = ~missing_data_mask & ~invalid_sku_mask # filter to get our valid rows
    
    # get rows with NAN values, add error message to each row
    missing_data = orders[missing_data_mask].copy()
    missing_data["error_msg"] = missing_data.apply(lambda row: f"ERROR [{row['orders_id']}]: is missing a value for one of the following field: {required_columns}", axis=1)

    # get rows that refer to non-existant SKUs - add error message
    invalid_sku_data = orders[invalid_sku_mask].copy()
    invalid_sku_data["error_msg"] = invalid_sku_data.apply(lambda row: f"ERROR [{row['orders_id']}]: SKU #[{row['orders_sku']}] refers to a product that does not exist, or there are no items in the order (nan)", axis=1)

    # Concatenate these two datasets on top of each other (UNION ALL) - these are invaliud records
    invalid_data = pd.concat([invalid_sku_data, missing_data], axis=0).sort_values(by="orders_id", ascending=True)
    valid_data = orders[valid_mask].copy()

    for msg in invalid_data["error_msg"]:
        print(msg)

    # return valid orders away from invalid orders
    return (valid_data, invalid_data)

'''============= End of Task 1 ============='''



'''============= Task 2 - Merge & Enrich ============='''

def enrich_valid_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich our dataset that only contains valid orders

    Parameters
    ----------
    orders : pd.DataFrame
        Our valid orders

    Returns
    -------
    The enriched dataset
    """
    global CUSTOMERS
    global PRODUCTS

    enriched = orders.copy()

    # join CUSTOMERS and PRODUCTS datasets onto ORDERS
    enriched = pd.merge(enriched, CUSTOMERS, left_on="orders_customer_id", right_on="customers_id", how="inner")
    enriched = pd.merge(enriched, PRODUCTS, left_on="orders_sku", right_on="products_sku", how="inner")
    
    # lookup table from Order ID -> customer name and tier
    order_to_cust_name = enriched[["orders_id", "customers_name", "customers_tier"]].drop_duplicates()
 
    # calculate the subtotal for each SKU/qty pair. 
    enriched["subtotal"] = enriched.apply(lambda row: row["products_price"] * row["orders_qty"], axis=1)

    # Discount is subtotal * 0.1
    enriched["discount"] = enriched.apply(lambda row: row["subtotal"] * 0.1 if row["customers_tier"] == "premium" else 0, axis=1)

    # Discounts and ssubtotals aggregated to print out to terminal
    discounts = enriched.groupby("orders_id")["discount"].sum().reset_index()
    subtotals = enriched.groupby("orders_id")["subtotal"].sum().reset_index()

    # print out details for each order
    for order_id in enriched["orders_id"].drop_duplicates():
        
        # get details for each order
        customer_name: str = order_to_cust_name.query("orders_id == @order_id")["customers_name"].iloc[0]   # singletones, so .ilocp[0] is the single field value
        customers_tier: str = order_to_cust_name.query("orders_id == @order_id")["customers_tier"].iloc[0]
        discount: float = discounts.query("orders_id == @order_id")["discount"].iloc[0]
        subtotal: float = subtotals.query("orders_id == @order_id")["subtotal"].iloc[0]

        # print formatted etails for each order
        print(f"[{order_id}]    customer={customer_name} ({customers_tier})")

        # print indiviudal line items for each SKU/qty pair in an order
        enriched[enriched["orders_id"] == order_id].apply(lambda row: print(f"   {row['orders_sku']}     {row['customers_name']}     qty={row['orders_qty']}        @ {row['products_price']:.2f}  =  {(row['orders_qty'] * row['products_price']):.2f}"), axis=1)
       
        print(f"    subtotal={subtotal:.2f}     discount={discount:.2f}     total={(subtotal - discount):.2f}\n")

    return enriched
       
''' ============= End of Task 2 ============='''





''' ============= Task 3 - Filter & Summarise ============='''

def unfillable_orders(enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Returns subset of orders that have qty > available stock
    Parameters
    ----------
    enriched: pd.DataFrame
        Enriched dataset

    Returns
    -------
    Unfillable orders
    """

    unfillable = enriched.query("orders_qty > products_stock")
    return unfillable.copy()
    

def per_customer_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Returns aggregated customer summary
    ----------
    enriched: pd.DataFrame
        Enriched dataset

    Returns
    -------
    Tabular summary
    """

    # SELECT customer_name, SUM(subtotal), COUNT() GROUP BY customer_name
    return enriched.groupby("customers_name").agg(
        subtotal=("subtotal", "sum"),
        order_count=("subtotal", "count")
    ).reset_index()



def top_selling_sku(enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Returns SKUs in order of sales
    ----------
    enriched: pd.DataFrame
        Enriched dataset

    Returns
    -------
    Tabular summary
    """

    # SELECT order_sku, SUM(orders_qty) GROUP BY order_sku ORDER BY SUM(orders_qty) DESC
    return enriched.groupby("orders_sku").agg(
        sku_count=("orders_qty", "sum")
    ).reset_index().sort_values("sku_count", ascending=False)


''' ============= End of Task 3 ============='''



''' ============= Task 4 - State Machine Workflow ============='''

# Stub exception
class ShippingException(Exception):
    pass

# Stub exception
class DeliveryException(Exception):
    pass

# Stub defined in outline
def ship_order(order_id: str) -> None:
    rand = random.random()
    if rand <= 0.2:
        raise ShippingException()

# Stub defined in outline
def confirm_delivery(order_id: str) -> None:
    if True is False:
        raise DeliveryException()

def state_machine(enriched: pd.DataFrame) -> pd.DataFrame:
    """
    State machine to simulate order processing
    ----------
    enriched: pd.DataFrame
        Enriched dataset

    Returns
    -------
    Table that shows ORDER id along with status
    """

    SHIP_ATTEMPT_LIM = 3
    order_ids = enriched["orders_id"].drop_duplicates().to_list() # going to iterate over each ID one by one

    # template for output table (order id, status)
    status_df = pd.DataFrame([order_ids, ["new" for i in order_ids]]).transpose()
    status_df.columns = ["orders_id", "status"]
    

    for order in order_ids:
        # only validated records made it into "enriched" dataset
        status_df.loc[status_df["orders_id"] == order, "status"] = "validated"

        # rejected / processing
        order_slice = enriched.query("orders_id == @order") # portion of enriched corresponding to order_id
        out_of_stocks = order_slice.query("orders_qty > products_stock") # out of stock records
        if not out_of_stocks.empty:
            status_df.loc[status_df["orders_id"] == order, "status"] = "rejected"
            continue    # end-state
        else:
            status_df.loc[status_df["orders_id"] == order, "status"] = "processing"

        # Shipped / cancelled
        ship_attempt = 0
        while ship_attempt < SHIP_ATTEMPT_LIM:
            try:
                ship_order(order)
                status_df.loc[status_df["orders_id"] == order, "status"] = "shipped"
                break
            except ShippingException:
                ship_attempt += 1
                if ship_attempt == SHIP_ATTEMPT_LIM:
                    status_df.loc[status_df["orders_id"] == order, "status"] = "cancelled"

        if ship_attempt == SHIP_ATTEMPT_LIM:
            continue # end-state
        
        # Delivered
        try:
            confirm_delivery(order)
            status_df.loc[status_df["orders_id"] == order, "status"] = "delivered"
        except DeliveryException:
            print("How'd we get here?")

    return status_df

''' ============= End of Task 4 ============='''




def main():
    global PRODUCTS
    global CUSTOMERS

    # Read datasets into memoery
    CUSTOMERS = load_dataset(CUSTOMER_FILENAME, None)
    orders = load_dataset(ORDERS_FILENAME, "items")
    PRODUCTS = load_dataset(PRODUCTS_FILENAME, None)

    # rename columns
    CUSTOMERS = rename_dataset("customers",  CUSTOMERS)
    orders = rename_dataset("orders",  orders)
    PRODUCTS = rename_dataset("products",  PRODUCTS)

    # validate and split dataset
    print("============= Task 1 - Validation Report =============\n")
    valid, invalid = validate_orders(orders)
    print("\n")

    # Enrich and print details
    print("============= Task 2 - Detailed Orders =============\n")
    enriched = enrich_valid_orders(valid)
    print("\n")

    print("============= Unfillable Records =============\n")
    unfillable = unfillable_orders(enriched)
    print(unfillable)
    print("\n")

    print("============= Per Customer Summary =============\n")
    per_cust = per_customer_summary(enriched)
    print(per_cust)
    print("\n")

    print("============= Top Selling SKU =============\n")
    top_sellers = top_selling_sku(enriched)
    top_seller = top_sellers.iloc[0]["orders_sku"]
    print(top_seller)
    print("\n")

    print("============= Shipping Status for Valid Orders =============\n")
    status_df = state_machine(enriched)
    print(status_df)
    print("\n")

    print("============= Invalid Rows - Exported to CSV =============\n")
    print(invalid)
    print("\n")
    invalid.to_csv("invalid_orders.csv")

if __name__ == "__main__":
    main()