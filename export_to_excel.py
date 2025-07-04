import pandas as pd
import xlsxwriter
import os
import tempfile

# Function to export trades_df and dashboard to Excel
# dashboard is a Plotly figure

def export_trades_and_dashboard_to_excel(trades_df: pd.DataFrame, dashboard, excel_path: str):
    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        # Write trades_df to the first sheet
        trades_df.to_excel(writer, sheet_name='Trades', index=False)

        # Save the dashboard as a static image temporarily
        tmp_dir = tempfile.gettempdir()
        img_path = os.path.join(tmp_dir, 'dashboard_image.png')
        # Requires kaleido or orca installed for static image export
        dashboard.write_image(img_path)

        # Access the XlsxWriter workbook and worksheet objects
        workbook  = writer.book
        worksheet = workbook.add_worksheet('Dashboard')

        # Insert the image into the worksheet
        worksheet.insert_image('B2', img_path)

        # Save the Excel file
        writer.save()

        # Optionally remove the temporary image file
        if os.path.exists(img_path):
            os.remove(img_path)


if __name__ == '__main__':
    print("This module provides export_trades_and_dashboard_to_excel(trades_df, dashboard, excel_path) function.")
