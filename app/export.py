import datetime
from string import ascii_uppercase

import xlsxwriter

alphabet = list(ascii_uppercase) + [letter1+letter2 for letter1 in ascii_uppercase for letter2 in ascii_uppercase]


def create_xls(booking_data):
    workbook = xlsxwriter.Workbook("/tmp/workbook.xlsx")
    worksheet = workbook.add_worksheet()
    worksheet.set_column("A:A", 15)

    # Format
    format_date = workbook.add_format({"num_format": "d mmm yyyy", "bold": True})
    bold = workbook.add_format({"bold": True})

    row = 0

    # First, assign a column to each user
    all_users = {}
    i = 1
    for date in sorted(booking_data.keys()):
        for user in booking_data[date]:
            if user not in all_users:
                all_users[user] = i
                i += 1

    # Letter of last column
    col_name_end = alphabet[i - 1]

    # Adjust column sizes
    worksheet.set_column(f"B:{col_name_end}", 10)

    # Create heading
    for user in all_users:
        col_name = alphabet[all_users[user]]
        worksheet.write(row, all_users[user], user, bold)
    worksheet.write(row, all_users[user] + 1, "Total", bold)

    # Next, parse lines and write in worksheet
    date_values = {}
    for date in sorted(booking_data.keys()):
        row += 1
        date_values[row] = len(booking_data[date])
        date_num = datetime.datetime.strptime(date, "%Y-%m-%d")
        worksheet.write(row, 0, date_num, format_date)
        for user in booking_data[date]:
            worksheet.write(row, all_users[user], 1)

    # Add total formulas
    # First add per-user formula
    row += 1
    worksheet.write(row, 0, "Total")
    for user, value_ in all_users.items():
        col_name = alphabet[all_users[user]]
        value = len([day for day in booking_data if user in booking_data[day]])
        worksheet.write_formula(
            row, value_, f"=SUM({col_name}2:{col_name}{row})", value=value
        )

    # Next per day
    for row in range(2, row + 1):
        worksheet.write_formula(
            row - 1, i, f"=SUM(B{row}:{col_name_end}{row})", value=date_values[row - 1]
        )

    workbook.close()
