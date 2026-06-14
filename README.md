# Order Processing Pipeline — Take-Home Assessment

## Overview

You are building a backend module for a small e-commerce company. You have been given raw data files and must build a pipeline that ingests, cleans, transforms, and processes orders through a fulfilment workflow.

**Purpose**: you are doing this assignment to give us something concrete (actual code) to talk about in a more formal way than the screening interview we have done so far. The goal is not perfection or for you to attempt to solve every edge case, but for you to build a simple solution and then talk me through the way you solved the problems -- in code.

**Time guidance:** Don't spend more than two to three hours on this. I don't want to steal your valuable time! If your solution is more than 500 lines with spaces and comments, it's probably too big and we won't have time to discuss it all. You can fit the entire thing into one file with a few classes and functions - or use several files. It's up to you.

**Language:** Python, C#, or Node.js/JavaScript/TypeScript — pick one.

**Dependencies:** use whatever libraries feel natural.

**No UI required:** console output or written files is fine.

a partial output of the program might look like this:
```
=== Task 1 — Validation Report ===

  [ORD-002] items list is empty
  [ORD-003] placed_at is null


=== Task 2 — Detailed Orders ===

  ORD-001  customer=Alice Brown (premium)
    A1  Widget Alpha               qty=2  @ $9.99  = $19.98
    B3  Widget Beta                qty=1  @ $14.99  = $14.99
    subtotal=$34.97  discount=$3.50  total=$31.47

  ORD-004  customer=Carol White (standard)
    A1  Widget Alpha               qty=1  @ $9.99  = $9.99
    subtotal=$9.99  discount=$0.00  total=$9.99

  ORD-006  customer=Bill Murray (premium)
    C4  UNKNOWN (C4)               qty=10  @ $0.00  = $0.00
    subtotal=$0.00  discount=$0.00  total=$0.00
```


**You can use AI if you like**: you will still have to explain to me how everything works in detail, and if the code contains redundant or confusing AI 'slop' that likely won't help. 



---

## Data Files

All input files are in the `data/` directory.

| File | Description |
|---|---|
| `orders.json` | Raw incoming orders — may contain quality issues |
| `products.csv` | Product catalogue with pricing and stock levels |
| `customers.json` | Customer records with account tier |

---

## Tasks

### Task 1 — Ingest & Validate

Load all three data sources and produce a **validation report** listing every data quality issue found, with a clear reason for each. Decide what to do with invalid records and document your decision.

### Task 2 — Merge & Enrich

For each valid order, merge the data so that each order line item includes the product name, unit price, and customer tier. Calculate an order total. Apply a **10% discount** to orders from `premium` customers.

### Task 3 — Filter & Summarise

From the enriched orders, produce:

- A list of orders that **cannot be fully fulfilled** because at least one item exceeds available stock
- A **per-customer summary** showing total spend and number of orders
- The **top-selling SKU** by total quantity ordered (across valid orders only)

### Task 4 — State Machine Workflow

Implement a simple order state machine with these transitions:

```
new → validated → processing → shipped → delivered
          ↓              ↓
       rejected       cancelled
```

Rules:
- `new → validated`: order passes Task 1 checks
- `validated → processing`: all items are in stock
- `validated → rejected`: one or more items are out of stock
- `processing → shipped`: call a stub function `ship_order(order_id)` that randomly succeeds or raises an exception ~20% of the time
- `processing → cancelled`: if `ship_order` raises, after **3 retry attempts**
- `shipped → delivered`: call a stub function `confirm_delivery(order_id)` — always succeeds

Run all valid orders through the full state machine and produce a final status report.

### Task 5 — Reflection (no coding)

Include a short `NOTES.md` (bullet points are fine) covering:

- Any assumptions you made and why
- What you'd do differently with more time
- One thing you'd add if this were a real production system

---

## Submission

Fork this repo and send me a link to it, **or** zip your solution and email it back. Include any instructions (the more explicit the better) needed to run your code. 




