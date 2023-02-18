import gspread
import time


class File:
    def __init__(self, fname, location='.'):
        self.location = location
        self.fname = fname
        self.buff = None

    def get_all_logs_as_dict(self):
        with open(f'{self.location}\{self.fname}', mode='r') as f:
            content = f.read()
        d = {
            'Date': [],
            'Time': [],
            'Status': []
        }
        rows = content.split('\n')
        # ['18.02.2023 14:42 CustomerReady', '18.02.2023 14:43 WhiteScreen']
        rows_and_columns = []
        for i in range(len(rows)):
            tmp = rows[i].split(' ')
            # ['18.02.2023', '14:42', 'CustomerReady']
            rows_and_columns.append(tmp)
        # rows_and_columns
        # [['18.02.2023', '14:42', 'CustomerReady'], ['12.42', '12:12', '...']]
        for row in rows_and_columns:
            d['Date'].append(row[0])
            d['Time'].append(row[1])
            d['Status'].append(row[2])
        return d

    def write_status_for(self, d, t, s=None):
        with open(f'{self.location}\{self.fname}', mode='a') as f:
            f.write(f'{d} {t} {s}')
        print(f'[FILE UPDATE] [NEW ROW ADDED]\n\t[DETAILS] {d} {t} {s}')


    def pull_logs_from_to(self, fr, to):
        pass


class Sheet:
    def __init__(self, sh_name, wks_name):
        sa = gspread.service_account()
        self.sh = sa.open(sh_name)
        self.wks = self.sh.worksheet(wks_name)
        print(f'[CONNECTION] Successfully connected to {wks_name} at {sh_name}')
        self.buff = self.wks.get(f'A1:C{self.wks.row_count - 1}')

    def get_all_logs_as_dict(self):
        logs = {}
        buff = self.buff
        header = []
        for elem in buff[0]:
            header.append(elem)
        for col in range(len(header)):
            for row in range(self.wks.row_count-1):
                if row == 0:
                    logs[header[col]] = [buff[row + 1][col]]
                else:
                    try:
                        logs[header[col]].append(buff[row + 1][col])
                    except:
                        pass
        return logs

    def update_sheet_buff(self):
        self.buff.append(self.wks.get(f'A{len(self.buff)}:C{(self.wks.row_count - 1)}'))

    def get_last_log_time(self):
        pass


def update_sheet_from_file(sh, f):
    to_upd = compare_file_and_sheet(sh, f)
    for i in range(3):



def compare_file_and_sheet(sh, f):
    """Sheet is missing this rows for 02.18 15:13, 02.18 15:14, 02.18 15:15"""
    sh_d = sh.get_all_logs_as_dict()
    f_d = f.get_all_logs_as_dict()
    if len(sh_d['Time'])!=len(sh_d['Date']) or len(sh_d['Date'])!=len(sh_d['Status']):
        print('[ERROR] log.py compare_file_and_sheet at line 80. Sheet data corrupted...')
        return None
    if len(f_d['Time'])!=len(f_d['Date']) or len(f_d['Date'])!=len(f_d['Status']):
        print('[ERROR] log.py compare_file_and_sheet at line 80. File data corrupted...')
        return None
    dif = len(f_d['Time'])-len(sh_d['Time'])
    missing_ids = []
    message = '[DIFFERENCE SHEET FILE] Spreadsheet is missing statuses for this date and time:'
    for i in range(dif):
        message += f"\n\t[{f_d['Date'][len(sh_d['Date'])+i]}] [{f_d['Time'][len(sh_d['Time'])+i]}]" \
                   f" {f_d['Status'][len(sh_d['Status'])+i]}"
        missing_ids.append(len(sh_d['Date'])+i)
    print(message)
    return missing_ids

print(compare_file_and_sheet(Sheet('KioskStatuses_MH', 'Kiosk 1'), File('Kiosk1.txt')))
