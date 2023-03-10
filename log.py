import gspread
import time
import string
import collections
from datetime import datetime


class File:
    def __init__(self, fname, location='.'):
        self.location = location
        self.fname = fname
        with open(f'{self.location}\{self.fname}', mode='r') as f:
            self.buff = f.read().split('\n')

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

    def get_last_day(self):
        return int((self.buff[len(self.buff)-1]).split('.')[0])


class Sheet:
    alphabet = list(string.ascii_uppercase)
    for i in range(26):
        alphabet.append('A' + alphabet[i])
    def __init__(self, sh_name, wks_name):
        self.wks_name = wks_name
        for i in range(0, 4):
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
            self.wks = self.sh.add_worksheet(title=wks_name, rows=1441, cols=count)
            top_row = ['Time/Date']
            for col in range(count):
                top_row.append(f"{col + 1}.{wks_name.split(' ')[3].split('.')[1]}."
                               f"{wks_name.split(' ')[3].split('.')[2]}")
            first_col = []
            for i in range(24):
                for u in range(60):
                    if i < 10:
                        hour = '0' + str(i)
                    else:
                        hour = i
                    if u < 10:
                        min = '0' + str(u)
                    else:
                        min = u
                    first_col.append([f'{hour}:{min}'])
            self.wks.update(f'A1:{Sheet.alphabet[count + 1]}1', [top_row])
            self.wks.update(f'A2:A{len(first_col) + 1}', first_col)
        print(f"[CONNECTION] Successfully connected to '{wks_name} at {sh_name}'")
        self.buff = self.wks.get(f"A1:{Sheet.alphabet[int(wks_name.split(' ')[5].split('.')[0])]}"
                                 f"{self.wks.row_count}")

    def get_all_logs_as_dict(self):
        # See until which point of time does the last day have logs in them
        logs = {
            'Date': [],
            'Time': [],
            'Status': []
        }
        for u in range(len(self.buff[1])-1):
            for i in range(1440):
                try:
                    logs['Status'].append(self.buff[i + 1][u + 1])
                    logs['Date'].append(f"{u+1}.{self.wks_name.split('.')[1]}."
                                        f"{self.wks_name.split(' ')[3].split('.')[2]}")
                    logs['Time'].append(self.buff[i+1][0])
                    missing_data_error = None
                except Exception as e:
                    missing_data_error = str(e)
                if missing_data_error:
                    return logs
        return logs

    def update_sheet_buff(self):
        self.buff.append(self.wks.get(f'A{len(self.buff)}:C{(self.wks.row_count - 1)}'))

    def get_last_log_time(self):
        pass

    def update_sheet_from_file(self, f):
        missing_ids = compare_file_and_sheet(self, f)
        missing_buff = {'Date': [], 'Time': [], 'Status': [], 'date_int': []}
        for id in missing_ids:
            missing_buff['Date'].append(f.buff[id].split(' ')[0])
            missing_buff['Time'].append(f.buff[id].split(' ')[1])
            missing_buff['Status'].append(f.buff[id].split(' ')[2])
        for date in missing_buff['Date']: missing_buff['date_int'].append(int(date.split('.')[0]))
        if missing_ids:
            print("[TABLE] Updating google worksheet table...")
            limits = {
                'starting_date': f.buff[missing_ids[0]].split(' ')[0],
                'starting_time': f.buff[missing_ids[0]].split(' ')[1],
                'ending_date': f.buff[missing_ids[len(missing_ids)-1]].split(' ')[0],
                'ending_time': f.buff[missing_ids[len(missing_ids)-1]].split(' ')[1]
            }
            limits['st_d_int'] = int(limits['starting_date'].split('.')[0])
            limits['st_t_int'] = int(limits['starting_time'].split(':')[0])*60 + int(limits['starting_time'].split(':')[1])
            limits['en_d_int'] = int(limits['ending_date'].split('.')[0])
            limits['en_t_int'] = int(limits['ending_time'].split(':')[0])*60 + int(limits['ending_time'].split(':')[1])
            dif = limits['en_d_int'] - limits['st_d_int'] + 1
            print(f"[LIMITS] Here are limits of the incoming update:\n\t"
                  f"[STARTING_DATE] {limits['starting_date']}\n\t"
                  f"[STARTING_TIME] {limits['starting_time']}\n\t"
                  f"[ENDING_DATE] {limits['ending_date']}\n\t"
                  f"[ENDING_TIME] {limits['ending_time']}\n\t"
                  f"---------------------\n\t|-To update {dif} days-|\n\t"
                  "---------------------")
            # Creating array for every separete day and sending it to update.
            all_dump=[]
            for id in missing_ids:
                splited = f.buff[id].split(' ')
                all_dump.append([
                    int(splited[1].split(':')[0])*60 + int(splited[1].split(':')[1])+2,     # row
                    int(splited[0].split('.')[0])+1,        # col
                    splited[2]]         # value
                )

        else:
            print("[TABLE] Google worksheet is up to date. No need to update anything")



def compare_file_and_sheet(sh, f):
    """Sheet is missing this rows for 02.18 15:13, 02.18 15:14, 02.18 15:15"""
    sh_d = sh.get_all_logs_as_dict()
    f_d = f.get_all_logs_as_dict()
    if sh_d['Time'] != []:
        if len(sh_d['Time']) != len(sh_d['Date']) or len(sh_d['Date']) != len(sh_d['Status']):
            print('[ERROR] log.py compare_file_and_sheet at line 80. Sheet data corrupted...')
            return None
        if len(f_d['Time']) != len(f_d['Date']) or len(f_d['Date']) != len(f_d['Status']):
            print('[ERROR] log.py compare_file_and_sheet at line 80. File data corrupted...')
            return None
    dif = len(f_d['Time']) - len(sh_d['Time'])
    missing_ids = []
    message = f'[DIFFERENCE SHEET FILE] Spreadsheet is missing {dif} statuses for this date and time:'
    for i in range(dif):
        message += f"\n\t[ID: {i}] [{f_d['Date'][len(sh_d['Date']) + i]}] [{f_d['Time'][len(sh_d['Time']) + i]}]" \
                   f" {f_d['Status'][len(sh_d['Status']) + i]}"
        missing_ids.append(len(sh_d['Date']) + i)
    print(message)
    return missing_ids


sh = Sheet('KioskStatuses_MH', '[Kiosk 1] From 01.03.2023 to 31.03.2023')
f = File('Kiosk1.txt')
print(sh.update_sheet_from_file(f))
