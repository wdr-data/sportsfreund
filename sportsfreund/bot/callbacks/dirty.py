# this dirty file is designed to impress the crowed on friday in the cantene
import logging

#import necessary modules
from ..fb import (send_buttons, button_postback, send_text, send_attachment_by_id,
                  guess_attachment_type)

logger = logging.getLogger(__name__)


# data of first and only competition
result =[{'country': 'deutschland',
  'first_name': 'Viktoria',
  'first_run': '55.90',
  'last_name': 'Rebensburg',
  'position': '1',
  'second_run': '59.30',
  'time_difference': '1:55.20'},
 {'country': 'frankreich',
  'first_name': 'Tessa',
  'first_run': '56.21',
  'last_name': 'Worley',
  'position': '2',
  'second_run': '59.13',
  'time_difference': '+ 0.14'},
 {'country': 'italien',
  'first_name': 'Manuela',
  'first_run': '55.57',
  'last_name': 'Mölgg',
  'position': '3',
  'second_run': '1:00.16',
  'time_difference': '+ 0.53'},
 {'country': 'oesterreich',
  'first_name': 'Stephanie',
  'first_run': '56.51',
  'last_name': 'Brunner',
  'position': '4',
  'second_run': '59.40',
  'time_difference': '+ 0.71'},
 {'country': 'usa',
  'first_name': 'Mikaela',
  'first_run': '55.69',
  'last_name': 'Shiffrin',
  'position': '5',
  'second_run': '1:00.25',
  'time_difference': '+ 0.74'},
 {'country': 'schweiz',
  'first_name': 'Wendy',
  'first_run': '57.06',
  'last_name': 'Holdener',
  'position': '6',
  'second_run': '59.25',
  'time_difference': '+ 1.11'},
 {'country': 'norwegen',
  'first_name': 'Ragnhild',
  'first_run': '56.61',
  'last_name': 'Mowinckel',
  'position': '7',
  'second_run': '1:00.04',
  'time_difference': '+ 1.45'},
 {'country': 'norwegen',
  'first_name': 'Kristin',
  'first_run': '56.42',
  'last_name': 'Lysdahl',
  'position': '8',
  'second_run': '1:00.26',
  'time_difference': '+ 1.48'},
 {'country': 'schweden',
  'first_name': 'Sara',
  'first_run': '55.92',
  'last_name': 'Hector',
  'position': '9',
  'second_run': '1:00.83',
  'time_difference': '+ 1.55'},
 {'country': 'slowenien',
  'first_name': 'Tina',
  'first_run': '57.05',
  'last_name': 'Robnik',
  'position': '9',
  'second_run': '59.70',
  'time_difference': '+ 1.55'},
 {'country': 'oesterreich',
  'first_name': 'Ricarda',
  'first_run': '57.18',
  'last_name': 'Haaser',
  'position': '11',
  'second_run': '59.64',
  'time_difference': '+ 1.62'},
 {'country': 'oesterreich',
  'first_name': 'Bernadette',
  'first_run': '57.87',
  'last_name': 'Schild',
  'position': '12',
  'second_run': '59.03',
  'time_difference': '+ 1.70'},
 {'country': 'oesterreich',
  'first_name': 'Elisabeth',
  'first_run': '57.16',
  'last_name': 'Kappaurer',
  'position': '13',
  'second_run': '59.84',
  'time_difference': '+ 1.80'},
 {'country': 'italien',
  'first_name': 'Irene',
  'first_run': '57.33',
  'last_name': 'Curtoni',
  'position': '14',
  'second_run': '59.73',
  'time_difference': '+ 1.86'},
 {'country': 'frankreich',
  'first_name': 'Estelle',
  'first_run': '57.65',
  'last_name': 'Alphand',
  'position': '14',
  'second_run': '59.41',
  'time_difference': '+ 1.86'},
 {'country': 'slowakei',
  'first_name': 'Petra',
  'first_run': '57.23',
  'last_name': 'Vlhová',
  'position': '16',
  'second_run': '59.97',
  'time_difference': '+ 2.00'},
 {'country': 'frankreich',
  'first_name': 'Taina',
  'first_run': '57.65',
  'last_name': 'Barioz',
  'position': '17',
  'second_run': '59.80',
  'time_difference': '+ 2.25'},
 {'country': 'oesterreich',
  'first_name': 'Katharina',
  'first_run': '57.40',
  'last_name': 'Truppe',
  'position': '18',
  'second_run': '1:00.09',
  'time_difference': '+ 2.29'},
 {'country': 'italien',
  'first_name': 'Laura',
  'first_run': '58.15',
  'last_name': 'Pirovano',
  'position': '19',
  'second_run': '59.41',
  'time_difference': '+ 2.36'},
 {'country': 'oesterreich',
  'first_name': 'Carmen',
  'first_run': '57.74',
  'last_name': 'Thalmann',
  'position': '20',
  'second_run': '1:00.05',
  'time_difference': '+ 2.59'},
 {'country': 'schweden',
  'first_name': 'Frida',
  'first_run': '57.15',
  'last_name': 'Hansdotter',
  'position': '21',
  'second_run': '1:00.79',
  'time_difference': '+ 2.74'},
 {'country': 'norwegen',
  'first_name': 'Nina',
  'first_run': '57.32',
  'last_name': 'Haver-Löseth',
  'position': '22',
  'second_run': '1:00.65',
  'time_difference': '+ 2.77'},
 {'country': 'norwegen',
  'first_name': 'Kristine',
  'first_run': '57.65',
  'last_name': 'Gjelsten',
  'position': '23',
  'second_run': '1:00.41',
  'time_difference': '+ 2.86'},
 {'country': 'kanada',
  'first_name': 'Marie-Michele',
  'first_run': '57.18',
  'last_name': 'Gagnon',
  'position': '24',
  'second_run': '1:00.89',
  'time_difference': '+ 2.87'},
 {'country': 'japan',
  'first_name': 'Asa',
  'first_run': '58.16',
  'last_name': 'Ando',
  'position': '25',
  'second_run': '1:00.30',
  'time_difference': '+ 3.26'},
 {'country': 'deutschland',
  'first_name': 'Maren',
  'first_run': '57.81',
  'last_name': 'Wiesler',
  'position': '26',
  'second_run': '1:01.08',
  'time_difference': '+ 3.69'},
 {'country': 'italien',
  'first_name': 'Elena',
  'first_run': '58.31',
  'last_name': 'Curtoni',
  'position': '27',
  'second_run': '1:00.62',
  'time_difference': '+ 3.73'},
 {'country': 'slowenien',
  'first_name': 'Meta',
  'first_run': '58.02',
  'last_name': 'Hrovat',
  'position': '28',
  'second_run': '1:03.78',
  'time_difference': '+ 6.60'},
 {'country': 'liechtenstein',
  'first_name': 'Tina',
  'first_run': '56.12',
  'last_name': 'Weirather',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'schweiz',
  'first_name': 'Melanie',
  'first_run': '56.37',
  'last_name': 'Meillard',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'norwegen',
  'first_name': 'Mina',
  'first_run': '58.44',
  'last_name': 'Fürst',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'japan',
  'first_name': 'Emi',
  'first_run': '58.51',
  'last_name': 'Hasegawa',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweiz',
  'first_name': 'Jasmina',
  'first_run': '58.68',
  'last_name': 'Suter',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'usa',
  'first_name': 'Lindsey',
  'first_run': '58.88',
  'last_name': 'Vonn',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweiz',
  'first_name': 'Aline',
  'first_run': '58.93',
  'last_name': 'Danioth',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweiz',
  'first_name': 'Rahel',
  'first_run': '59.02',
  'last_name': 'Kopp',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'deutschland',
  'first_name': 'Jessica',
  'first_run': '59.12',
  'last_name': 'Hilzinger',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'polen',
  'first_name': 'Maryna',
  'first_run': '59.12',
  'last_name': 'Gasienica',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'serbien',
  'first_name': 'Nevena',
  'first_run': '59.13',
  'last_name': 'Ignjatovic',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweiz',
  'first_name': 'Elena',
  'first_run': '59.25',
  'last_name': 'Stoffel',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'frankreich',
  'first_name': 'Marie',
  'first_run': '59.32',
  'last_name': 'Massios',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'usa',
  'first_name': 'Megan',
  'first_run': '59.33',
  'last_name': 'McJames',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweden',
  'first_name': 'Magdalena',
  'first_run': '59.39',
  'last_name': 'Fjällström',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'deutschland',
  'first_name': 'Patrizia',
  'first_run': '59.53',
  'last_name': 'Dorsch',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'niederlande',
  'first_name': 'Adriana',
  'first_run': '59.62',
  'last_name': 'Jelinkova',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'italien',
  'first_name': 'Jole',
  'first_run': '59.62',
  'last_name': 'Galli',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'usa',
  'first_name': 'Foreste',
  'first_run': '59.70',
  'last_name': 'Peterson',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweden',
  'first_name': 'Ylva',
  'first_run': '59.79',
  'last_name': 'Staalnacke',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'slowenien',
  'first_name': 'Desiree',
  'first_run': '59.81',
  'last_name': 'Ajlec',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'schweden',
  'first_name': 'Emelie',
  'first_run': '1:00.12',
  'last_name': 'Wikström',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'japan',
  'first_name': 'Haruna',
  'first_run': '1:00.23',
  'last_name': 'Ishikawa',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'italien',
  'first_name': 'Luisa',
  'first_run': '1:00.58',
  'last_name': 'Matilde',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'tschechien',
  'first_name': 'Ester',
  'first_run': '1:00.85',
  'last_name': 'Ledecka',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'ukraine',
  'first_name': 'Olga',
  'first_run': '1:03.15',
  'last_name': 'Knysch',
  'position': '',
  'second_run': '',
  'time_difference': 'nicht qualifiziert'},
 {'country': 'italien',
  'first_name': 'Marta',
  'first_run': '',
  'last_name': 'Bassino',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'schweiz',
  'first_name': 'Lara',
  'first_run': '',
  'last_name': 'Gut',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'italien',
  'first_name': 'Sofia',
  'first_run': '',
  'last_name': 'Goggia',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'slowenien',
  'first_name': 'Ana',
  'first_run': '',
  'last_name': 'Drev',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'kanada',
  'first_name': 'Valerie',
  'first_run': '',
  'last_name': 'Grenier',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'grossbritannien',
  'first_name': 'Alexandra',
  'first_run': '',
  'last_name': 'Tilley',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'kanada',
  'first_name': 'Mikaela',
  'first_run': '',
  'last_name': 'Tommy',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'oesterreich',
  'first_name': 'Katharina',
  'first_run': '',
  'last_name': 'Liensberger',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'slowenien',
  'first_name': 'Ana',
  'first_run': '',
  'last_name': 'Bucik',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'kroatien',
  'first_name': 'Leona',
  'first_run': '',
  'last_name': 'Popovic',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'oesterreich',
  'first_name': 'Nadine',
  'first_run': '',
  'last_name': 'Fest',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'oesterreich',
  'first_name': 'Chiara',
  'first_run': '',
  'last_name': 'Mair',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'},
 {'country': 'weissrussland',
  'first_name': 'Maria',
  'first_run': '',
  'last_name': 'Schkanowa',
  'position': '',
  'second_run': '',
  'time_difference': 'ausgeschieden'}]


# data worldcup
wc_standing =[{'country': 'deutschland',
  'first_name': 'Viktoria',
  'last_name': 'Rebensburg',
  'points': 100,
  'position': 1},
 {'country': 'frankreich',
  'first_name': 'Tessa',
  'last_name': 'Worley',
  'points': 80,
  'position': 2},
 {'country': 'italien',
  'first_name': 'Manuela',
  'last_name': 'Mölgg',
  'points': 60,
  'position': 3},
 {'country': 'oesterreich',
  'first_name': 'Stephanie',
  'last_name': 'Brunner',
  'points': 50,
  'position': 4},
 {'country': 'usa',
  'first_name': 'Mikaela',
  'last_name': 'Shiffrin',
  'points': 45,
  'position': 5},
 {'country': 'schweiz',
  'first_name': 'Wendy',
  'last_name': 'Holdener',
  'points': 40,
  'position': 6},
 {'country': 'norwegen',
  'first_name': 'Ragnhild',
  'last_name': 'Mowinckel',
  'points': 36,
  'position': 7},
 {'country': 'norwegen',
  'first_name': 'Kristin',
  'last_name': 'Lysdahl',
  'points': 32,
  'position': 8},
 {'country': 'schweden',
  'first_name': 'Sara',
  'last_name': 'Hector',
  'points': 29,
  'position': 9},
 {'country': 'slowenien',
  'first_name': 'Tina',
  'last_name': 'Robnik',
  'points': 29,
  'position': 9},
 {'country': 'oesterreich',
  'first_name': 'Ricarda',
  'last_name': 'Haaser',
  'points': 24,
  'position': 11},
 {'country': 'oesterreich',
  'first_name': 'Bernadette',
  'last_name': 'Schild',
  'points': 22,
  'position': 12},
 {'country': 'oesterreich',
  'first_name': 'Elisabeth',
  'last_name': 'Kappaurer',
  'points': 20,
  'position': 13},
 {'country': 'italien',
  'first_name': 'Irene',
  'last_name': 'Curtoni',
  'points': 18,
  'position': 14},
 {'country': 'schweden',
  'first_name': 'Estelle',
  'last_name': 'Alphand',
  'points': 18,
  'position': 14},
 {'country': 'slowakei',
  'first_name': 'Petra',
  'last_name': 'Vlhová',
  'points': 15,
  'position': 16},
 {'country': 'frankreich',
  'first_name': 'Taina',
  'last_name': 'Barioz',
  'points': 14,
  'position': 17},
 {'country': 'oesterreich',
  'first_name': 'Katharina',
  'last_name': 'Truppe',
  'points': 13,
  'position': 18},
 {'country': 'italien',
  'first_name': 'Laura',
  'last_name': 'Pirovano',
  'points': 12,
  'position': 19},
 {'country': 'oesterreich',
  'first_name': 'Carmen',
  'last_name': 'Thalmann',
  'points': 11,
  'position': 20},
 {'country': 'schweden',
  'first_name': 'Frida',
  'last_name': 'Hansdotter',
  'points': 10,
  'position': 21},
 {'country': 'norwegen',
  'first_name': 'Nina',
  'last_name': 'Haver-Löseth',
  'points': 9,
  'position': 22},
 {'country': 'norwegen',
  'first_name': 'Kristine',
  'last_name': 'Gjelsten',
  'points': 8,
  'position': 23},
 {'country': 'kanada',
  'first_name': 'Marie-Michele',
  'last_name': 'Gagnon',
  'points': 7,
  'position': 24},
 {'country': 'japan',
  'first_name': 'Asa',
  'last_name': 'Ando',
  'points': 6,
  'position': 25},
 {'country': 'deutschland',
  'first_name': 'Maren',
  'last_name': 'Wiesler',
  'points': 5,
  'position': 26},
 {'country': 'italien',
  'first_name': 'Elena',
  'last_name': 'Curtoni',
  'points': 4,
  'position': 27},
 {'country': 'slowenien',
  'first_name': 'Meta',
  'last_name': 'Hrovat',
  'points': 3,
  'position': 28}]


# next events
event_list = [
{'date' : '29.10.', 'city': 'Sölden', 'country' : 'AUT', 'discipline': {'Abfahrt': False, 'Slalom': False, 'Riesenslalom': True, 'Super-G': False}},
{'date' : '12.11.', 'city': 'Levi', 'country' : 'FIN',  'discipline': {'Abfahrt': False, 'Slalom': True, 'Riesenslalom': False, 'Super-G': False}},
{'date' : '25.-26.11.','city': 'Lake Louise', 'country' : 'CAN',  'discipline': {'Abfahrt': True, 'Slalom': False, 'Riesenslalom': False, 'Super-G': True}},
{'date' : '1.-3.12.','city': 'Beaver Creek', 'country' : 'USA',  'discipline': {'Abfahrt': True, 'Slalom': False, 'Riesenslalom': True, 'Super-G': True}},
{'date' : '9.-10.12.','city': "Val d'Isere", 'country' : 'FRA',  'discipline': {'Abfahrt': False, 'Slalom': True, 'Riesenslalom': True, 'Super-G': False}},
{'date' : '15.-16.12.','city': 'Gröden', 'country': 'ITA',  'discipline': {'Abfahrt': True, 'Slalom': False, 'Riesenslalom': False, 'Super-G': True}}
]

# athletes
athletes_list = [{'first_name': 'Felix',
                        'last_name': 'Neureuther',
                        'uuid': 'Felix.Neureuther',
                        'birthday':  '26.03.1984',
                        'birthplace': 'München/Pasing',
                        'city': 'Garmisch-Partenkirchen',
                        'country': 'germany',
                        'hight': '1,84',
                        'weight': None,
                        'victories': ['1. Platz Weltcup Yukawa Naeba, Slalom','3. Platz Weltmeisterschaft St. Moritz Slalom'],
                        'fun_fact1': '1998 Schulweltmeister',
                        'fun_fact2': None,
                        'picture': None,
                        'sport': 'Ski Alpin',
                        'disciplines':['Slalom','Riesenslalom']},
                        {'first_name': 'Viktoria',
                        'last_name': 'Rebensburg',
                        'uuid': 'Viktoria.Rebensburg',
                         'country' : 'germany',
                        'birthday':  '4. Oktober 1989',
                        'birthplace': None,
                        'city': 'Tegernsee',
                        'hight': '1,70',
                        'weight':'67kg',
                        'victories': ['Olympiasiegerin Riesenslalom 2010','Vizeweltmeisterin Riesenslalom 2015'],
                        'fun_fact1': '1998 Schulweltmeister',
                        'fun_fact2': None,
                        'picture': 'here',
                        'sport': 'Ski Alpin',
                        'disciplines': ['Riesenslalom', 'Abfahrt', 'Super G']},
                        {'first_name': 'Lindsay',
                        'last_name': 'Vonn',
                        'uuid': 'Lindsay.Vonn',
                        'birthday':  '18. Oktober 1984',
                        'birthplace': 'Saint Paul/Minnesota',
                         'country': 'usa',
                        'city': 'Tegernsee',
                         'hight': '1,78',
                        'weight': '73',
                         'relationsship_status': ' Thomas Vonn (verh. 2007–2013)',
                        'victories': ['Olympiasiegerin Abfahrt 2010','Bronze in Vancover 2010'],
                        'fun_fact1': 'Buch geschrieben Namens Strong Is the New Beautiful',
                        'fun_fact2': None,
                        'picture': None,
                        'sport': 'Ski Alpin',
                        'disciplines': ['Riesenslalom', 'Abfahrt', 'Super G', 'Kombination']},
                        {'first_name': 'Viktoria',
                        'last_name': 'Rebensburg',
                        'uuid': 'Viktoria.Rebensburg',
                         'country' : 'germany',
                        'birthday':  '4. Oktober 1989',
                        'birthplace': None,
                        'city': 'Tegernsee',
                        'hight': '1,70',
                        'weight':'67kg',
                        'victories': ['Olympiasiegerin Riesenslalom 2010','Vizeweltmeisterin Riesenslalom 2015'],
                        'fun_fact1': '1998 Schulweltmeister',
                        'fun_fact2': None,
                        'picture': 'here',
                        'sport': 'Ski Alpin',
                        'disciplines': ['Riesenslalom', 'Abfahrt', 'Super G']},
                         ]

by_uuid = dict()
for athlete in athletes_list:
    by_uuid[athlete['uuid']] = athlete

def results_ski_alpin_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    city = parameters.get('city')
    discipline = parameters.get('discipline')
    sport = parameters.get('sport')



    send_text(sender_id,
              'Hier stehen die ersten drei')



def athlete_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    first_name = parameters.get('first_name')
    last_name = parameters.get('last_name')

    if not first_name and not last_name:
        send_text(sender_id,
                  'Komisch, ich habe keinen Namen erhalten')
    elif not first_name and last_name:
        send_text(sender_id,
                  'Hier infos zu ' + last_name)
    elif first_name and not last_name:
        send_text(sender_id,
                  'Hier infos zu ' + first_name + 'Ich brauche noch deinen Nachnamen')
    elif first_name and last_name:
        athlete(event, {'athlete': {'first_name': first_name, 'last_name': last_name}})

def athlete(event,payload,**kwargs):
    sender_id = event['sender']['id']
    first_name = payload['athlete']['first_name']
    last_name = payload['athlete']['last_name']

    logger.info('Anfrage nach Infos zu ' + first_name + ' ' + last_name)

    athlete_info = by_uuid['.'.join([first_name, last_name])]
    if athlete_info:
        reply = '{first_name} {last_name}\n' \
            'Geboren am {birthday} in {birthplace}.\n' \
            'Disziplinen: {disciplines} \nErfolge: {victories}\nTritt 2018 in Pyeongchang an für {country}'.format(
                first_name=athlete_info['first_name'],
                last_name=athlete_info['last_name'],
                birthday=athlete_info['birthday'],
                birthplace=athlete_info['birthplace'],
                disciplines=', '.join(athlete_info['disciplines']),
                victories=', '.join(athlete_info['victories']),
                country=athlete_info['country'],
            )

    else:
        reply = 'Zu diesem Athleten habe ich leider noch keine Informationen.'

    if athlete_info['uuid'] == 'Felix.Neureuther':
        buttons = [
            button_postback('Fun Facts',
                            {'fun_fact': athlete_info['uuid']}),
        ]
        send_buttons(sender_id, reply, buttons)
    else:
        send_text(sender_id, reply)

def fun_fact(event, payload, **kwargs):
    athlete_id = payload['fun_fact']
    athlete = by_uuid[athlete_id]
    send_text(sender_id,
              'Hier kommen zukünftig witzige Infos über ' + athlete['first_name'] + ' ' + athlete['last_name'])

def next_event_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    city = parameters.get('city')
    discipline = parameters.get('discipline')
    sport = parameters.get('sport')

    if not discipline and not sport and not city:
        send_text(sender_id,
                  'Ich schaue gerne in meinem Kalender nach. Welche Sportart interessiert dich?')
    elif not discipline and not sport and city:
        send_text(sender_id,
                  'Nächstes event in ' + city + 'ist folgendes:')
    elif not discipline and sport:
        if sport != 'Ski Alpin':
            send_text(sender_id,
                      'Sorry, aber ich habe noch kein Infos zum ' + sport +'. Bisher kenne ich nur ein wenig im Ski Alpin aus.')
        send_text(sender_id,
                  'Nächste event in der Diszipline '+discipline + 'findet am ... in city statt')
    elif discipline:
        next_event(event, {'search_parameters': {'city': city, 'discipline': discipline, 'sport': sport}})

def next_event(event, payload, **kwargs):
    sender_id = event['sender']['id']
    discipline = payload['search_parameters']['discipline']

    logger.info('Anfrage nach Infos zu ' + discipline)

    # by_discipline = dict()
    #
    # for event in event_list:
    #     for kind in event['discipline']:
    #         if discipline == True:
    #             logger.info('Infos ' + kind)
    #             by_discipline[discipline] = event
    #
    # event_info = by_discipline[discipline]

    send_text(sender_id,
              'Hier bekommst du demnächst Infos zum ' + discipline)

def world_cup_standing_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    sport = parameters.get('sport')
    discipline = parameters.get('discipline')



    send_text(sender_id,
              'info zum Worldcup stand')
