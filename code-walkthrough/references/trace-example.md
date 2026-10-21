# Example: step into an import and return to its caller

This is an illustrative two-file program. In a real walkthrough, extract exact excerpts from the captured source and link their actual paths and lines. The labels below demonstrate reading order; they are not a required page template.

`app.py`:

```python
from totals import subtotal

def main():
    prices = [10, 20]
    amount = subtotal(prices)
    print(f"Total: {amount}")

if __name__ == "__main__":
    main()
```

`totals.py`:

```python
def subtotal(prices):
    total = 0
    for price in prices:
        if price < 0:
            raise ValueError("negative price")
        total += price
    return total
```

Running `python app.py` prints a total. We will follow the illustrative input `[10, 20]` from the entry guard through the imported calculation and back to the print.

**Enter the program — `app.py:8–9`**

```python
if __name__ == "__main__":
    main()
```

Python first imports `subtotal` and defines `main`; defining either function does not execute its body. When this file runs as a script, `__name__` is `"__main__"`, so the guard calls `main()`. Importing `app` would skip that call.

**Enter `main` — `app.py:3–5`; stack: `entry guard → main`**

```python
def main():
    prices = [10, 20]
    amount = subtotal(prices)
```

`prices` holds the two integer prices. The right-hand side `subtotal(prices)` must finish before Python assigns `amount`. This imported function owns the calculation and validation, so step into `totals.py`. Leave `main` suspended at line 5, awaiting the result; line 6 has not run yet.

**Enter `subtotal` — `totals.py:1–6`; stack: `entry guard → main → subtotal`**

```python
def subtotal(prices):
    total = 0
    for price in prices:
        if price < 0:
            raise ValueError("negative price")
        total += price
```

The parameter refers to the same `[10, 20]` list. Start with `total = 0`. On the first iteration `price = 10`, the negative check is false, and `total += price` changes the total to `10`. The second iteration uses `price = 20` and changes the total to `30`; the iterator is now exhausted.

The alternate branch is meaningful: a negative element raises before adding that element. For `[10, -2]`, the first iteration reaches `total = 10`, then the second raises. There is no handler in either function, so the exception unwinds through `main` and the print is never reached. This is an illustrative branch trace, not an executed test.

**Return from `subtotal` — `totals.py:7`**

```python
    return total
```

For `[10, 20]`, the return value is `30`. Pop `subtotal` off the stack and return to the pending assignment in `main`, not to a separate module overview.

**Resume `main` — `app.py:5–6`; stack: `entry guard → main`**

```python
    amount = subtotal(prices)
    print(f"Total: {amount}")
```

The call on line 5 has completed, so `amount` becomes `30`. Line 6 formats and prints `Total: 30`. `print` is routine here; its internal implementation adds nothing to this calculation. `main` then returns `None` implicitly, control returns to the entry guard, and the script finishes.

This trace covered both function bodies, the guard, and the negative-value branch. The imports were explained at their role in setup and at the actual call; there was no separate alphabetical tour of the files.
