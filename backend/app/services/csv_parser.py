import pandas as pd
from datetime import datetime

def parse_portfolio_csv(file):
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return None, [f"Pandas error: {str(e)}"]
    required_cols = ['Symbol', 'Quantity', 'Average Buy Price (INR)']
    errors = []
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    if errors:
        return None, errors

    validated_indices = []
    row_errors = []
    for idx, row in df.iterrows():
        symbol = row.get('Symbol', '').strip()
        try:
            quantity = int(row.get('Quantity', 0))
            price = float(row.get('Average Buy Price (INR)', 0))
            purchase_date = str(row.get('Purchase Date (YYYY-MM-DD)', '')).strip()
        except Exception as e:
            row_errors.append(f"Row {idx+2}: Conversion error: {str(e)}")
            continue

        if (not symbol or quantity <= 0 or price <= 0 or
            (purchase_date and not valid_date(purchase_date))):
            row_errors.append(f"Row {idx+2}: Invalid data: {row.to_dict()}")
            continue
        validated_indices.append(idx)
    return df.loc[validated_indices].reset_index(drop=True), row_errors

def valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except:
        return False
