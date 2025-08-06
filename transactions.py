import importlib.util

# Try to import private transactions if available
spec = importlib.util.find_spec('transactions_private')
if spec is not None:
    transactions_private = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transactions_private)
    transactions = transactions_private.transactions
else:
    # Demo transactions for public/demo use only
    transactions = [
        ('2024-01-01', 'DEMO_STOCK', 10, 100.0, 'USD'),
        ('2024-02-01', 'DEMO_STOCK', 5, 110.0, 'USD'),
        ('2024-03-01', 'DEMO_COIN', 0.1, 500.0, 'NOK'),
    ]
