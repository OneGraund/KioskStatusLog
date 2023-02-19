import gspread
import time
import string
from datetime import datetime


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
        for i in range(0,4):
            try:
                sa = gspread.service_account()
                connection_error = None
            except Exception as e:
                connection_error = str(e)
            if connection_error:
                print(f'[ERROR CONNECTING] Could not establish a connection to a gspread service account...')
                time.sleep(4)
                if i == 3:
                    raise Exception("[LOGGING IMPOSSIBLE] Server could not connect to gspread")
            else:
                break
        self.sh = sa.open(sh_name)
        try:
            self.wks = self.sh.worksheet(wks_name)
            connection_error = None
        except Exception as e:
            connection_error = str(e)
        if connection_error:
            print(f"[WORKSHEET ERROR] Could not open worksheet named {wks_name}. Creating...")
            # Calculating amount of days in this month
            start_date = wks_name.split(' ')[3]
            end_date = wks_name.split(' ')[5]
            count = int(end_date.split('.')[0])
            self.wks = self.sh.add_worksheet(title=wks_name, rows=1441,cols=count+1)
            top_row = ['Time/Date']
            for col in range(count+1):
                top_row.append(f"{col+1}.{wks_name.split(' ')[3].split('.')[1]}."
                               f"{wks_name.split(' ')[3].split('.')[2]}")
            first_col = []
            for i in range(24):
                for u in range(60):
                    if i<10:
                        hour = '0'+str(i)
                    else:
                        hour = i
                    if u<10:
                        min = '0'+str(u)
                    else:
                        min = u
                    first_col.append([f'{hour}:{min}'])
            alphabet = list(string.ascii_uppercase)
            for i in range(26):
                alphabet.append('A' + alphabet[i])
            self.wks.update(f'A1:{alphabet[count + 1]}1', [top_row])
            self.wks.update(f'A2:A{len(first_col)+1}', first_col)
        print(f'[CONNECTION] Successfully connected to {wks_name} at {sh_name}')
        self.buff = self.wks.get(f'A1:C{self.wks.row_count - 1}')

    def get_all_logs_as_dict(self):
        logs = {}
        print(f'[ROW COUNT] Based on len of self.buff there are {len(self.buff)-1} rows')
        if len(self.buff)-1==0:
            logs = {
                'Date': [],
                'Time': [],
                'Status': []
            }
            return logs
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
    to_upd_ids = compare_file_and_sheet(sh, f)
    if to_upd_ids:
        starting_row = to_upd_ids[0]
        ending_row = to_upd_ids[len(to_upd_ids)-1]
        buffer = []
        file_logs = f.get_all_logs_as_dict()
        for row in range(starting_row, ending_row+1):
            tmp = []
            tmp.append(file_logs['Date'][row])
            tmp.append(file_logs['Time'][row])
            tmp.append(file_logs['Status'][row])
            buffer.append(tmp)
        sh.wks.update(f'A{len(sh.buff)+1}:C{len(sh.buff)+len(to_upd_ids)}', buffer)
    else:
        return '[UPDATED] Worksheet is up to date with local file ...'


def compare_file_and_sheet(sh, f):
    """Sheet is missing this rows for 02.18 15:13, 02.18 15:14, 02.18 15:15"""
    sh_d = sh.get_all_logs_as_dict()
    print(f'[SH_D] {sh_d}')
    f_d = f.get_all_logs_as_dict()
    if sh_d['Time'] != []:
        if len(sh_d['Time'])!=len(sh_d['Date']) or len(sh_d['Date'])!=len(sh_d['Status']):
            print('[ERROR] log.py compare_file_and_sheet at line 80. Sheet data corrupted...')
            return None
        if len(f_d['Time'])!=len(f_d['Date']) or len(f_d['Date'])!=len(f_d['Status']):
            print('[ERROR] log.py compare_file_and_sheet at line 80. File data corrupted...')
            return None
    dif = len(f_d['Time'])-len(sh_d['Time'])
    print(f"[LEN F_D] {len(f_d['Time'])} with \n\t[F_D] {f_d}\n[LEN SH_D] {len(sh_d['Time'])} with"
          f"\n\t[SH_D] {sh_d}")
    missing_ids = []
    message = f'[DIFFERENCE SHEET FILE] Spreadsheet is missing {dif} statuses for this date and time:'
    for i in range(dif):
        message += f"\n\t[{f_d['Date'][len(sh_d['Date'])+i]}] [{f_d['Time'][len(sh_d['Time'])+i]}]" \
                   f" {f_d['Status'][len(sh_d['Status'])+i]}"
        missing_ids.append(len(sh_d['Date'])+i)
    print(message)
    return missing_ids

sh = Sheet('KioskStatuses_MH', '[Kiosk 1] From 01.03.2023 to 31.03.2023')
f = File('Kiosk1.txt')