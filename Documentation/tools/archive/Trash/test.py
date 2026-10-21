from ucimlrepo import fetch_ucirepo
hierarchical_sales_data = fetch_ucirepo(id=611)
X = hierarchical_sales_data.data.features