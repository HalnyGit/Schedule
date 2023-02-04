# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 11:25:59 2019

@author: Halny
"""

import pandas as pd
import datetime
import os
import itertools

#reading holidays from csv files and making dictionary of holidays{ccy:[dates]}
holiday_paths = [os.path.join('..\\holidays', file) for file in os.listdir('..\\holidays') if file.endswith('.csv')]

hol_df = pd.DataFrame()
for i in range(len(holiday_paths)):
    data = pd.read_csv(holiday_paths[i])
    ccy = list(data.columns)[0]
    try:
        data[ccy] = pd.to_datetime(data[ccy], format='%Y-%m-%d')
    except:
        data[ccy] = pd.to_datetime(data[ccy], format='%d-%m-%Y')
    hol_df=pd.concat([hol_df, data], axis=1)

holidays = hol_df.to_dict('list')
ccy_pairs = [ccy_pair for ccy_pair in itertools.combinations(holidays.keys(), 2)]
for ccy_pair in ccy_pairs:
    holidays[ccy_pair]=sorted(list(set(holidays[ccy_pair[0]]+holidays[ccy_pair[1]])))
    rev_ccy_pair = (ccy_pair[1], ccy_pair[0])
    holidays[rev_ccy_pair] = holidays[ccy_pair]

    

###overwrite holidays dict for testing only
#holidays={'pln':[datetime.date(2020, 2, 3),
#            datetime.date(2021, 3, 1),
#            datetime.date(2020, 2, 28) ]}
###
    
#non working days dictionary {ccy:[1-Mon, ..., 7-Sun]}
non_working_days={'pln':[6, 7], 
                  'eur':[6, 7], 
                  'usd':[6, 7]
                  }

#number of working days from today to the start and the end for particular currency
dse={'pln':{'on':(0, 1),
         'tn':(1, 1),
         'sn':(2, 1),
         'w':(2,),
         'm':(2,),
         'q':(2,),
         'y':(2,)},
      'eur':{'on':(0, 1),
         'tn':(1, 1),
         'sn':(2, 1),
         'w':(2,),
         'm':(2,),
         'q':(2,),
         'y':(2,)}
}

###some dates for testing purpose only
# d = datetime.date(2020, 1, 31)
# h1 = datetime.date(2020, 2, 3)
# h2 = datetime.date(2021, 3, 1)
# h3 = datetime.date(2020, 11, 28)
###


# helper function for checking and getting end of month dates
def get_eom(init_date):
    '''
    init_date: date
    return: date, last day of month of init_date
    '''
    temp_date = init_date.replace(day=28) + datetime.timedelta(days=4)
    return temp_date - datetime.timedelta(days=temp_date.day)
    
#test
#get_eom(h3)
    
def get_weom(init_date, nwd_key=None, hol_key=None):
    '''
    init_date: date
    return: date, last working day of month of init_date
    '''
    eom_date = get_eom(init_date)
    weom = move_date_by_days(eom_date + datetime.timedelta(days=1), roll=-1, nwd_key=nwd_key, hol_key=hol_key)
    return weom

#test
#get_weom(datetime.date(2020, 2, 28), 'pln', 'pln')

def is_eom(init_date):
    '''
    init_date: date
    return: boolean, True if init_date is the last day of month
    '''
    return init_date == get_eom(init_date)

#test
#is_eom(h3)

def is_weom(init_date, nwd_key=None, hol_key=None):
    '''
    init_date: date
    return: boolean, True if init_date is last working day of month
    '''
    return init_date == get_weom(init_date, nwd_key=nwd_key, hol_key=hol_key)

#test
#is_weom(datetime.date(2020, 2, 29), nwd_key='pln')

# functions for rolling dates by day and month according to conventions
def move_date_by_days(init_date, roll=1, nwd_key=None, hol_key=None):
    '''
    moves date by n-number of days forward or backward,
    if nwd_key and hol_key are provided, final date is moved to working day
    init_date: date, initial caluclation date
    roll: integer, number of days to move forward (+) or backward (-)
    nwd_key: string that stands for currency iso code, it is a key in non_working_days dictionary
    hol_key: string or tuple of pair of strings that stand for currency iso code, it is a key in holidays dictonary
    return: date
    '''

    moved_date=init_date
    moved_date = moved_date + datetime.timedelta(days=roll)
    if roll>=0:
        while (days_between(init_date, moved_date, nwd_key=nwd_key, hol_key=hol_key) < roll):
            moved_date = moved_date + datetime.timedelta(days=1)
    if roll<0:
        while (days_between(moved_date, init_date, nwd_key, hol_key) < abs(roll)):
            moved_date = moved_date + datetime.timedelta(days=-1)
    return moved_date

#test        
#move_date_by_days(d, 1, 'pln', 'pln')
#move_date_by_days(datetime.date(2020, 1, 6), -1, 'pln', 'pln')   

def mdbm_calendar(init_date, roll=1):
    '''
    moves date by n-number of months forward or backward
    init_date: date, initial caluclation date
    roll: integer, number of months the init_date will be rolled forward (+) or backward(-)
    return: date
    '''
    n_month = (init_date.month + roll) % 12
    if n_month==0: n_month=12
    n_year = (init_date.month + roll)    
    
    if roll >= 0:
        n_year = 0 if n_year == 12 else ((init_date.month + (roll-1)) // 12)    
    else:
        n_year = -1 if n_year == 0 else ((init_date.month + (roll-1)) // 12) 
    
    try:
        moved_date=datetime.date(init_date.year + n_year, n_month, init_date.day)
    except:
        moved_date=mdbm_preceding(init_date + datetime.timedelta(days=-1), roll=roll)
    
    return moved_date

#test
#mdbm_calendar(datetime.date(2019, 3, 31), -1)

def mdbm_following(init_date, roll=1, nwd_key=None, hol_key=None):
    '''
    moves date by n-number of months forward or backward, if moved date is weekend or holiday
    it is moved to next working day
    init_date: date
    roll: integer, number of months the init_date will be rolled forward (+) or backward(-)
    nwd_key: string that stands for currency iso code, it is a key in non_working_days dictionary
    hol_key: string that stands for currency iso code, it is a key in holidays dictonary
    the function does not comply end-end rule: 31/01 + 1 month => 01/03 as there is no 31/02
    return: date
    '''
    n_month = (init_date.month + roll) % 12
    if n_month==0: n_month=12
    n_year = (init_date.month + roll)    
    if roll >= 0:
        n_year = 0 if n_year == 12 else ((init_date.month + (roll-1)) // 12)    
    else:
        n_year = -1 if n_year == 0 else ((init_date.month + (roll-1)) // 12) 
    
    try:
        moved_date=datetime.date(init_date.year + n_year, n_month, init_date.day)
    except:
        moved_date=mdbm_following(init_date + datetime.timedelta(days=1), roll)
    moved_date=move_date_by_days(moved_date + datetime.timedelta(days=-1), roll=1, nwd_key=nwd_key, hol_key=hol_key) 
    return moved_date

#test   
#mdbm_following(datetime.date(2020, 3, 31), -1, 'pln', 'pln')


def mdbm_preceding(init_date, roll=1, nwd_key=None, hol_key=None):
    '''
    moves date by n-number of months forward or backward, if moved date is weekend or holiday
    it is moved to preceding working day
    init_date: date
    roll: integer, number of months the init_date will be rolled forward (+) or backward(-)
    nwd_key: string that stands for currency iso code, it is a key in non_working_days dictionary
    hol_key: string that stands for currency iso code, it is a key in holidays dictonary
    the function does not comply end-end rule: 29/02 + 1 month => 29/03, not 31/03
    return: date
    '''
    n_month = (init_date.month + roll) % 12
    if n_month==0: n_month=12
    n_year = (init_date.month + roll)    
    if roll >= 0:
        n_year = 0 if n_year == 12 else ((init_date.month + (roll-1)) // 12)    
    else:
        n_year = -1 if n_year == 0 else ((init_date.month + (roll-1)) // 12)   
    try:
        moved_date=datetime.date(init_date.year + n_year, n_month, init_date.day)
    except:
        moved_date=mdbm_preceding(init_date + datetime.timedelta(days=-1), roll)
    moved_date=move_date_by_days(moved_date + datetime.timedelta(days=1), roll=-1, nwd_key=nwd_key, hol_key=hol_key) 
    return moved_date

#test
#mdbm_preceding(datetime.date(2020, 2, 29), -1, 'pln', 'pln')

def mdbm_eom(init_date, roll=1):
    '''
    moves date by n-number of months forward or backward to the end of the new month irrespectively of working days 
    init_date: date
    roll: integer, number of months the init_date will be rolled forward (+) or backward(-)
    the function complies end-end rule: 29/02 + 1 month => 31/03
    return: date
    '''
    moved_date = mdbm_preceding(init_date, roll)
    return get_eom(moved_date)

#test
#mdbm_end_end(h3, 12)
    
def mdbm_eom_following(init_date, roll=1, nwd_key=None, hol_key=None):    
    '''
    moves date by n-number of months forward or backward to the end of the new month taking into account working days
    init_date: date
    roll: integer, number of months the init_date will be rolled forward (+) or backward(-)
    the function complies end-end rule: 29/02 + 1 month => 31/03
    return: date
    '''
    moved_date = mdbm_eom(init_date, roll)
    return move_date_by_days(moved_date, 0, nwd_key, hol_key)

#test
#mdbm_eom_following(datetime.date(2019, 12, 6), 1, 'usd', 'usd')
#mdbm_eom_following(datetime.date(2020, 1, 31), 1, 'pln', 'pln')
#mdbm_eom_following(datetime.date(2020, 2, 29), 1, 'pln', 'pln')  
   
def mdbm_modified_following(init_date, roll=1, nwd_key=None, hol_key=None):
    '''
    moves date by n-number of months forward or backward, if moved date is weekend or holiday
    it is moved according to modified following convention
    init_date: date
    roll: integer, number of months the init_date will be rolled forward (+) or backward(-)
    nwd_key: string that stands for currency iso code, it is a key in non_working_days dictionary
    hol_key: string that stands for currency iso code, it is a key in holidays dictonary
    the function complies end-end rule: 29/02 + 1 month => 31/03
    '''
    nwd = non_working_days.get(nwd_key, [])
    hol = holidays.get(hol_key,[])
    
    if is_weom(init_date):
        moved_date = mdbm_preceding(init_date, roll, nwd_key, hol_key)
        return get_weom(moved_date, nwd_key, hol_key)
    
    n_month = (init_date.month + roll) % 12
    if n_month == 0: n_month = 12
    n_year = (init_date.month + roll)
    if roll >= 0:
        n_year = 0 if n_year == 12 else ((init_date.month + (roll-1)) // 12)    
    else:
        n_year = -1 if n_year == 0 else ((init_date.month + (roll-1)) // 12) 
    try:
        moved_date = datetime.date(init_date.year + n_year, n_month, init_date.day)
    except:
        moved_date = get_eom(datetime.date(init_date.year + n_year, n_month, 28))
    while ((moved_date.isoweekday() in nwd) or (moved_date in hol)): 
        moved_date = moved_date + datetime.timedelta(days=1)
    if moved_date.month != n_month:
        moved_date=move_date_by_days(moved_date, -1, nwd_key, hol_key)
    return moved_date

#test
#mdbm_modified_following(datetime.date(2019, 12, 6), 1, 'usd', 'usd')
#print(mdbm_modified_following(datetime.date(2020, 1, 31), 1, 'pln', 'pln'))
#print(mdbm_modified_following(datetime.date(2020, 2, 29), 1, 'pln', 'pln'))
#print(mdbm_modified_following(datetime.date(2012, 11, 29), 3, 'pln', 'pln'))  

#day count conventions    

def days_between(d1, d2, hol_key=None, nwd_key=None):
    '''
    d1: date
    d2: date
    return: integer, number of days between dates d1 and d2
            if hol_key and nwd_key provided then it returns number of working days between two dates
    '''
    assert d1<=d2, 'd1 must be less or equal d2'
    if hol_key==None and nwd_key==None:
        return (d2 - d1) / datetime.timedelta(days=1)
    else:
        nwd = non_working_days.get(nwd_key, [])
        hol = holidays.get(hol_key,[])
        n = int(days_between(d1, d2))
        k=0
        for i in range(n+1):
            check_date = d1 + datetime.timedelta(days=i)
            if check_date in hol or check_date.isoweekday() in nwd:
                k += 1
        return n-k
    

def is_leap(d):
    '''
    date
    return: True if year of the date 'd' is leap, False otherwise
    '''
    try:
        datetime.date(d.year, 2, 29)
    except:
        return False
    return True

def dcf_act365(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in ACT365 convention
    '''
    return days_between(d1, d2)/365.0

def dcf_actact(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in ACT/ACT ISDA convention
    '''
    base1=366.0 if is_leap(d1) else 365.0
    base2=366.0 if is_leap(d2) else 365.0
    eoy = datetime.date(d1.year, 12, 31)
    return (((days_between(d1, eoy) + 1) / base1) + ((days_between(eoy, d2) - 1) / base2))

def dcf_act360(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in ACT360 convention
    '''
    return days_between(d1, d2)/360.0

def dcf_30360(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in 30/360 convention
    '''
    day1 = d1.day
    day2 = d2.day
    month1 = d1.month
    month2 = d2.month
    year1 = d1.year
    year2 = d2.year
    return (360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1))/360.0

def dcf_30u360(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in 30/360 Bond Basis convention
    '''
    day1 = d1.day
    day2 = d2.day
    month1 = d1.month
    month2 = d2.month
    year1 = d1.year
    year2 = d2.year
    if (day2==31 and (day1==30 or day1==31)): day2=30
    if day1==31: day1=30
    return (360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1))/360.0

def dcf_30e360(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in 30/360 Eurobond Basis convention
            also known as Special German or 30/360 ICMA
    '''
    day1 = d1.day
    day2 = d2.day
    month1 = d1.month
    month2 = d2.month
    year1 = d1.year
    year2 = d2.year
    if day1==31: day1=30
    if day2==31: day2=30
    return (360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1))/360.0    

def dcf_30e360_isda(d1, d2):
    '''
    d1: date, d2: date
    return: day count fraction in 30E/360 ISDA convention
    '''
    day1 = d1.day
    day2 = d2.day
    month1 = d1.month
    month2 = d2.month
    year1 = d1.year
    year2 = d2.year    
    if is_eom(d1): day1=30
    if is_eom(d2): day2=30
    return (360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1))/360.0
   

def calc_period(calc_date, ccy, nwd_key=None, hol_key=None, period=''):
    '''calc_date: date, calculation date
       ccy: string, (eg. pln, usd)
       period: string, (possible entries: on, tn, sn, *w, *m, *q, *y, *x*
               where * is integer eg 3w, 2m, 3q, 5y, 1x4)
       hol: list of dates that represent holidays 
       returns: tuple of dates that represent start date and end date
               for given period and currency
    '''
    assert isinstance(calc_date, datetime.date), 'calc_date must be a date'
    period = period.lower()
    if (period=='on' or period=='tn' or period=='sn'):
        start_date=move_date_by_days(calc_date, dse[ccy][period][0], nwd_key, hol_key)
        end_date=move_date_by_days(start_date, dse[ccy][period][1], nwd_key, hol_key)
    if 'x' in period:
        n = int(period.split('x')[0])
        m = int(period.split('x')[1])
        spot_date = move_date_by_days(calc_date, dse[ccy]['sn'][0], nwd_key, hol_key)
        start_date=mdbm_modified_following(spot_date, n, nwd_key, hol_key)
        end_date=mdbm_modified_following(spot_date, m, nwd_key, hol_key)
    if any(elem in {'w', 'm', 'q', 'y'} for elem in period):
        duration=int(period[:-1])
        interval=period[len(period)-1:]
        if interval=='w':
            start_date=move_date_by_days(calc_date, dse[ccy][interval][0], nwd_key, hol_key)
            end_date=move_date_by_days(start_date, 7*duration, nwd_key, hol_key)
        if interval=='m':
            start_date=move_date_by_days(calc_date, dse[ccy][interval][0], nwd_key, hol_key)
            end_date=mdbm_modified_following(start_date, duration, nwd_key, hol_key)
        if interval=='q':
            start_date=move_date_by_days(calc_date, dse[ccy][interval][0], nwd_key, hol_key)
            end_date=mdbm_modified_following(start_date, 3*duration, nwd_key, hol_key)
        if interval=='y':
            start_date=move_date_by_days(calc_date, dse[ccy][interval][0], nwd_key, hol_key)
            end_date=mdbm_modified_following(start_date, 12*duration, nwd_key, hol_key)
    return(start_date, end_date)


class Schedule(object):
    CONVENTIONS = {'calendar', 'following', 'preceding', 'eom', 'eom_following', 
                       'modified_following'}
    def __init__(self, start=None, end=None, ccy=None, roll=None, convention='calendar', stub=None, 
                 pay_shift=None, dcf='act365'):
        '''
        start: date
        end: date
        ccy: string, iso currency code (eg 'usd', 'eur')
        roll: integer, number of months the interest periods will roll (3 - every 3 months, 6  -every 6 months)
        convention: string, one of the values from CONVENTIONS set
        stub: date
        pay_shift: tuple (integer, string), integer specifies number of days the payment date needs to be shifted +/- from start or end date
                          string: 'start_date' or 'end_date' represents the date from which payment date shall be deduced
                          if pay_shift=None then payment date equals end date
        dcf: string, day count factor
        self.dates_table: is DataFrame that consist of interest periods meaning, start dates, end dates, fixing dates and payment dates                
        '''
        self.start = start
        self.end = end
        self.ccy = ccy
        self.roll = roll
        self.stub = stub
        self.pay_shift = pay_shift
        self.convention = convention.lower()
        self.dcf = dcf.lower()
        if self.convention not in self.CONVENTIONS:
            raise ValueError ('\"{0}\" is not valid convention, available conventions are: {1}'.format(self.convention, self.CONVENTIONS))
    
        i = 1
        dates = [self.start]
        if self.stub != None:
            dates.append(self.stub)
            roll_date = self.stub
        else:
            roll_date = self.start
        while dates[-1] < self.end:
            if self.convention == 'calendar':
                next_date = mdbm_calendar(roll_date, self.roll * i)
            if self.convention == 'following':
                next_date = mdbm_following(roll_date, self.roll * i, self.ccy, self.ccy)
            if self.convention == 'preceding':
                next_date = mdbm_preceding(roll_date, self.roll * i, self.ccy, self.ccy)
            if self.convention == 'eom':
                next_date = mdbm_eom(roll_date, self.roll * i)
            if self.convention == 'eom_following':
                next_date = mdbm_eom_following(roll_date, self.roll * i, self.ccy, self.ccy)
            if self.convention == 'modified_following':
                next_date = mdbm_modified_following(roll_date, self.roll * i, self.ccy, self.ccy)
            if next_date < self.end:
                dates.append(next_date)
            else:
                dates.append(self.end)        
            i += 1
        
        self.dates = dates
        self.start_dates = self.dates[:-1]
        self.end_dates = self.dates[1:]
        days_to_spot = dse[self.ccy]['sn'][0]
        #self.fixing_dates = [move_date_by_days(d, -days_to_spot, self.ccy, self.ccy ) for d in self.start_dates]
        temp_data = {'start_date':self.start_dates,
                     'end_date':self.end_dates}
        self.dates_table = pd.DataFrame(temp_data)
        self.dates_table['fixing_date'] = self.dates_table['start_date'].apply(lambda x: move_date_by_days(x, -days_to_spot, self.ccy, self.ccy))
    
        if self.pay_shift == None:
            self.dates_table['payment_date'] = self.dates_table['end_date']
        else:
            self.dates_table['payment_date'] = self.dates_table[self.pay_shift[0]].apply(lambda x: move_date_by_days(x, self.pay_shift[1], self.ccy, self.ccy))

                
        if self.dcf == 'act365':
            self.dates_table['dcf'] = dcf_act365(self.dates_table['start_date'], self.dates_table['end_date'])
        elif self.dcf == 'actact':
            self.dates_table['dcf'] = self.dates_table.apply(lambda x: dcf_actact(x['start_date'],  x['end_date']), axis=1)
        elif self.dcf == 'act360':
            self.dates_table['dcf'] = self.dates_table.apply(lambda x: dcf_act360(x['start_date'],  x['end_date']), axis=1)
        elif self.dcf == '30360':
            self.dates_table['dcf'] = self.dates_table.apply(lambda x: dcf_30360(x['start_date'],  x['end_date']), axis=1)        
        elif self.dcf == '30u360':
            self.dates_table['dcf'] = self.dates_table.apply(lambda x: dcf_30u360(x['start_date'],  x['end_date']), axis=1) 
        elif self.dcf == '30e360':
            self.dates_table['dcf'] = self.dates_table.apply(lambda x: dcf_30u360(x['start_date'],  x['end_date']), axis=1)
        elif self.dcf == '30e360_isda':
            self.dates_table['dcf'] = self.dates_table.apply(lambda x: dcf_30e360_isda(x['start_date'],  x['end_date']), axis=1)

    def get_dates(self):
        return self.dates
    
    def get_start_dates(self):
        return self.start_dates
    
    def get_end_dates(self):
        return self.end_dates
    
    def get_dates_table(self):
        return self.dates_table
    
    
# # example
start_date = datetime.date(2022, 10, 12)
end_date = datetime.date(2022, 10, 19)

# s=Schedule(start_date, end_date, "pln", 6)
# print s.get_dates()
# print s.get_start_dates()
# print s.get_end_dates()
# print s.get_dates_table()
 
        
days = pd.date_range(start_date, end_date).to_list()

# for i in range(5):
#       print(type(days[i]))          

# s1=days[0]
# s2=days[365]

# s=Schedule(s1, s2, "pln", 3)
# print(s.get_dates())
# print(s.get_start_dates())
# print(s.get_end_dates())
# print(s.get_dates_table())


# not connected to the rest of this script
# just an exampple of using getattr
class Switcher(object):
    def indirect(self,i):
        method_name='number_'+str(i)
        method=getattr(self,method_name,lambda:'Invalid')
        return method()
    def number_0(self):
        return 'zero'
    def number_1(self):
        return 'one'
    def number_2(self):
        return 'two'

#test
#s=Switcher()
#s.indirect(2)


