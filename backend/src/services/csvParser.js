const { parse } = require('csv-parse/sync');

/**
 * Parses a portfolio CSV buffer.
 * Mirrors parse_portfolio_csv() in csv_parser.py.
 *
 * Expected columns:
 *   Symbol | Quantity | Average Buy Price (INR) | Purchase Date (YYYY-MM-DD) [optional]
 *
 * Returns:
 *   { rows: Array<Object> | null, errors: string[] }
 */
function parsePortfolioCsv(buffer) {
  let records;
  try {
    records = parse(buffer, {
      columns:          true,    // first row = headers
      skip_empty_lines: true,
      trim:             true,
    });
  } catch (err) {
    return { rows: null, errors: [`CSV parse error: ${err.message}`] };
  }

  const REQUIRED = ['Symbol', 'Quantity', 'Average Buy Price (INR)'];
  const errors   = [];

  const headers = records.length > 0 ? Object.keys(records[0]) : [];
  for (const col of REQUIRED) {
    if (!headers.includes(col)) errors.push(`Missing required column: ${col}`);
  }
  if (errors.length) return { rows: null, errors };

  const rows = [];
  records.forEach((record, idx) => {
    const rowNum = idx + 2;           // row 1 = header
    const symbol = (record['Symbol'] || '').trim().toUpperCase();

    let quantity, averageBuyPrice, purchaseDate;
    try {
      quantity       = parseInt(record['Quantity'], 10);
      averageBuyPrice = parseFloat(record['Average Buy Price (INR)']);
      purchaseDate   = (record['Purchase Date (YYYY-MM-DD)'] || '').trim() || null;
    } catch (e) {
      errors.push(`Row ${rowNum}: Conversion error: ${e.message}`);
      return;
    }

    if (!symbol || isNaN(quantity) || quantity <= 0 ||
        isNaN(averageBuyPrice) || averageBuyPrice <= 0) {
      errors.push(`Row ${rowNum}: Invalid data: ${JSON.stringify(record)}`);
      return;
    }

    if (purchaseDate && !isValidDate(purchaseDate)) {
      errors.push(`Row ${rowNum}: Invalid date format (expected YYYY-MM-DD): ${purchaseDate}`);
      return;
    }

    rows.push({ symbol, quantity, averageBuyPrice, purchaseDate });
  });

  return { rows, errors };
}

function isValidDate(str) {
  return /^\d{4}-\d{2}-\d{2}$/.test(str) && !isNaN(Date.parse(str));
}

module.exports = { parsePortfolioCsv };