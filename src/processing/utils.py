import csv
import io

def csv_to_markdown(csv_string: str) -> str:
    f = io.StringIO(csv_string)
    reader = csv.reader(f)
    rows = list(reader)
    
    if not rows:
        return ''
    
    # Calculate max width for each column
    num_cols = len(rows[0])
    col_widths = [0] * num_cols
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Helper to format a row
    def format_row(row):
        return '| ' + ' | '.join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + ' |'

    # Build Markdown lines
    md_lines = []
    md_lines.append(format_row(rows[0]))  # Header
    md_lines.append('| ' + ' | '.join('-' * col_widths[i] for i in range(num_cols)) + ' |')  # Divider
    for row in rows[1:]:
        md_lines.append(format_row(row))  # Data rows

    return '\n'.join(md_lines)
