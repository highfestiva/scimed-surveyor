#!/usr/bin/env python3


from collections import defaultdict
from elasticsearch import Elasticsearch
from iso3166 import countries_by_name
import journal_util
from journal_countrycode import journal2country_code, doi2cc
from locale import atof
from numpy import nan
import pandas as pd
import re


es = Elasticsearch([{'host': 'localhost', 'port': 9200}], http_auth=('elastic', open('.espassword').read().strip()))

df = pd.DataFrame(
    columns=['Country', 'Population (2020)', 'Yearly Change', 'Net Change', 'Density (P/Km²)', 'Land Area (Km²)', 'Migrants (net)', 'Fert. Rate', 'Med. Age', 'Urban Pop %', 'World Share'],
    data=[['China', 1439323776, '0.39 %', 5540090, 153, 9388211, -348399, 1.7, 38, '61 %', '18.47 %'], ['India', 1380004385, '0.99 %', 13586631, 464, 2973190, -532687, 2.2, 28, '35 %', '17.70 %'], ['United States', 331002651, '0.59 %', 1937734, 36, 9147420, 954806, 1.8, 38, '83 %', '4.25 %'], ['Indonesia', 273523615, '1.07 %', 2898047, 151, 1811570, -98955, 2.3, 30, '56 %', '3.51 %'], ['Pakistan', 220892340, '2.00 %', 4327022, 287, 770880, -233379, 3.6, 23, '35 %', '2.83 %'], ['Brazil', 212559417, '0.72 %', 1509890, 25, 8358140, 21200, 1.7, 33, '88 %', '2.73 %'], ['Nigeria', 206139589, '2.58 %', 5175990, 226, 910770, -60000, 5.4, 18, '52 %', '2.64 %'], ['Bangladesh', 164689383, '1.01 %', 1643222, 1265, 130170, -369501, 2.1, 28, '39 %', '2.11 %'], ['Russia', 145934462, '0.04 %', 62206, 9, 16376870, 182456, 1.8, 40, '74 %', '1.87 %'], ['Mexico', 128932753, '1.06 %', 1357224, 66, 1943950, -60000, 2.1, 29, '84 %', '1.65 %'], ['Japan', 126476461, '-0.30 %', -383840, 347, 364555, 71560, 1.4, 48, '92 %', '1.62 %'], ['Ethiopia', 114963588, '2.57 %', 2884858, 115, 1000000, 30000, 4.3, 19, '21 %', '1.47 %'], ['Philippines', 109581078, '1.35 %', 1464463, 368, 298170, -67152, 2.6, 26, '47 %', '1.41 %'], ['Egypt', 102334404, '1.94 %', 1946331, 103, 995450, -38033, 3.3, 25, '43 %', '1.31 %'], ['Vietnam', 97338579, '0.91 %', 876473, 314, 310070, -80000, 2.1, 32, '38 %', '1.25 %'], ['DR Congo', 89561403, '3.19 %', 2770836, 40, 2267050, 23861, 6.0, 17, '46 %', '1.15 %'], ['Turkey', 84339067, '1.09 %', 909452, 110, 769630, 283922, 2.1, 32, '76 %', '1.08 %'], ['Iran', 83992949, '1.30 %', 1079043, 52, 1628550, -55000, 2.2, 32, '76 %', '1.08 %'], ['Germany', 83783942, '0.32 %', 266897, 240, 348560, 543822, 1.6, 46, '76 %', '1.07 %'], ['Thailand', 69799978, '0.25 %', 174396, 137, 510890, 19444, 1.5, 40, '51 %', '0.90 %'], ['United Kingdom', 67886011, '0.53 %', 355839, 281, 241930, 260650, 1.8, 40, '83 %', '0.87 %'], ['France', 65273511, '0.22 %', 143783, 119, 547557, 36527, 1.9, 42, '82 %', '0.84 %'], ['Italy', 60461826, '-0.15 %', -88249, 206, 294140, 148943, 1.3, 47, '69 %', '0.78 %'], ['Tanzania', 59734218, '2.98 %', 1728755, 67, 885800, -40076, 4.9, 18, '37 %', '0.77 %'], ['South Africa', 59308690, '1.28 %', 750420, 49, 1213090, 145405, 2.4, 28, '67 %', '0.76 %'], ['Myanmar', 54409800, '0.67 %', 364380, 83, 653290, -163313, 2.2, 29, '31 %', '0.70 %'], ['Kenya', 53771296, '2.28 %', 1197323, 94, 569140, -10000, 3.5, 20, '28 %', '0.69 %'], ['South Korea', 51269185, '0.09 %', 43877, 527, 97230, 11731, 1.1, 44, '82 %', '0.66 %'], ['Colombia', 50882891, '1.08 %', 543448, 46, 1109500, 204796, 1.8, 31, '80 %', '0.65 %'], ['Spain', 46754778, '0.04 %', 18002, 94, 498800, 40000, 1.3, 45, '80 %', '0.60 %'], ['Uganda', 45741007, '3.32 %', 1471413, 229, 199810, 168694, 5.0, 17, '26 %', '0.59 %'], ['Argentina', 45195774, '0.93 %', 415097, 17, 2736690, 4800, 2.3, 32, '93 %', '0.58 %'], ['Algeria', 43851044, '1.85 %', 797990, 18, 2381740, -10000, 3.1, 29, '73 %', '0.56 %'], ['Sudan', 43849260, '2.42 %', 1036022, 25, 1765048, -50000, 4.4, 20, '35 %', '0.56 %'], ['Ukraine', 43733762, '-0.59 %', -259876, 75, 579320, 10000, 1.4, 41, '69 %', '0.56 %'], ['Iraq', 40222493, '2.32 %', 912710, 93, 434320, 7834, 3.7, 21, '73 %', '0.52 %'], ['Afghanistan', 38928346, '2.33 %', 886592, 60, 652860, -62920, 4.6, 18, '25 %', '0.50 %'], ['Poland', 37846611, '-0.11 %', -41157, 124, 306230, -29395, 1.4, 42, '60 %', '0.49 %'], ['Canada', 37742154, '0.89 %', 331107, 4, 9093510, 242032, 1.5, 41, '81 %', '0.48 %'], ['Morocco', 36910560, '1.20 %', 438791, 83, 446300, -51419, 2.4, 30, '64 %', '0.47 %'], ['Saudi Arabia', 34813871, '1.59 %', 545343, 16, 2149690, 134979, 2.3, 32, '84 %', '0.45 %'], ['Uzbekistan', 33469203, '1.48 %', 487487, 79, 425400, -8863, 2.4, 28, '50 %', '0.43 %'], ['Peru', 32971854, '1.42 %', 461401, 26, 1280000, 99069, 2.3, 31, '79 %', '0.42 %'], ['Angola', 32866272, '3.27 %', 1040977, 26, 1246700, 6413, 5.6, 17, '67 %', '0.42 %'], ['Malaysia', 32365999, '1.30 %', 416222, 99, 328550, 50000, 2.0, 30, '78 %', '0.42 %'], ['Mozambique', 31255435, '2.93 %', 889399, 40, 786380, -5000, 4.9, 18, '38 %', '0.40 %'], ['Ghana', 31072940, '2.15 %', 655084, 137, 227540, -10000, 3.9, 22, '57 %', '0.40 %'], ['Yemen', 29825964, '2.28 %', 664042, 56, 527970, -30000, 3.8, 20, '38 %', '0.38 %'], ['Nepal', 29136808, '1.85 %', 528098, 203, 143350, 41710, 1.9, 25, '21 %', '0.37 %'], ['Venezuela', 28435940, '-0.28 %', -79889, 32, 882050, -653249, 2.3, 30, 'N.A.', '0.36 %'], ['Madagascar', 27691018, '2.68 %', 721711, 48, 581795, -1500, 4.1, 20, '39 %', '0.36 %'], ['Cameroon', 26545863, '2.59 %', 669483, 56, 472710, -4800, 4.6, 19, '56 %', '0.34 %'], ["Côte d'Ivoire", 26378274, '2.57 %', 661730, 83, 318000, -8000, 4.7, 19, '51 %', '0.34 %'], ['North Korea', 25778816, '0.44 %', 112655, 214, 120410, -5403, 1.9, 35, '63 %', '0.33 %'], ['Australia', 25499884, '1.18 %', 296686, 3, 7682300, 158246, 1.8, 38, '86 %', '0.33 %'], ['Niger', 24206644, '3.84 %', 895929, 19, 1266700, 4000, 7.0, 15, '17 %', '0.31 %'], ['Taiwan', 23816775, '0.18 %', 42899, 673, 35410, 30001, 1.2, 42, '79 %', '0.31 %'], ['Sri Lanka', 21413249, '0.42 %', 89516, 341, 62710, -97986, 2.2, 34, '18 %', '0.27 %'], ['Burkina Faso', 20903273, '2.86 %', 581895, 76, 273600, -25000, 5.2, 18, '31 %', '0.27 %'], ['Mali', 20250833, '3.02 %', 592802, 17, 1220190, -40000, 5.9, 16, '44 %', '0.26 %'], ['Romania', 19237691, '-0.66 %', -126866, 84, 230170, -73999, 1.6, 43, '55 %', '0.25 %'], ['Malawi', 19129952, '2.69 %', 501205, 203, 94280, -16053, 4.3, 18, '18 %', '0.25 %'], ['Chile', 19116201, '0.87 %', 164163, 26, 743532, 111708, 1.7, 35, '85 %', '0.25 %'], ['Kazakhstan', 18776707, '1.21 %', 225280, 7, 2699700, -18000, 2.8, 31, '58 %', '0.24 %'], ['Zambia', 18383955, '2.93 %', 522925, 25, 743390, -8000, 4.7, 18, '45 %', '0.24 %'], ['Guatemala', 17915568, '1.90 %', 334096, 167, 107160, -9215, 2.9, 23, '52 %', '0.23 %'], ['Ecuador', 17643054, '1.55 %', 269392, 71, 248360, 36400, 2.4, 28, '63 %', '0.23 %'], ['Syria', 17500658, '2.52 %', 430523, 95, 183630, -427391, 2.8, 26, '60 %', '0.22 %'], ['Netherlands', 17134872, '0.22 %', 37742, 508, 33720, 16000, 1.7, 43, '92 %', '0.22 %'], ['Senegal', 16743927, '2.75 %', 447563, 87, 192530, -20000, 4.7, 19, '49 %', '0.21 %'], ['Cambodia', 16718965, '1.41 %', 232423, 95, 176520, -30000, 2.5, 26, '24 %', '0.21 %'], ['Chad', 16425864, '3.00 %', 478988, 13, 1259200, 2000, 5.8, 17, '23 %', '0.21 %'], ['Somalia', 15893222, '2.92 %', 450317, 25, 627340, -40000, 6.1, 17, '47 %', '0.20 %'], ['Zimbabwe', 14862924, '1.48 %', 217456, 38, 386850, -116858, 3.6, 19, '38 %', '0.19 %'], ['Guinea', 13132795, '2.83 %', 361549, 53, 245720, -4000, 4.7, 18, '39 %', '0.17 %'], ['Rwanda', 12952218, '2.58 %', 325268, 525, 24670, -9000, 4.1, 20, '18 %', '0.17 %'], ['Benin', 12123200, '2.73 %', 322049, 108, 112760, -2000, 4.9, 19, '48 %', '0.16 %'], ['Burundi', 11890784, '3.12 %', 360204, 463, 25680, 2001, 5.5, 17, '14 %', '0.15 %'], ['Tunisia', 11818619, '1.06 %', 123900, 76, 155360, -4000, 2.2, 33, '70 %', '0.15 %'], ['Bolivia', 11673021, '1.39 %', 159921, 11, 1083300, -9504, 2.8, 26, '69 %', '0.15 %'], ['Belgium', 11589623, '0.44 %', 50295, 383, 30280, 48000, 1.7, 42, '98 %', '0.15 %'], ['Haiti', 11402528, '1.24 %', 139451, 414, 27560, -35000, 3.0, 24, '57 %', '0.15 %'], ['Cuba', 11326616, '-0.06 %', -6867, 106, 106440, -14400, 1.6, 42, '78 %', '0.15 %'], ['South Sudan', 11193725, '1.19 %', 131612, 18, 610952, -174200, 4.7, 19, '25 %', '0.14 %'], ['Dominican Republic', 10847910, '1.01 %', 108952, 225, 48320, -30000, 2.4, 28, '85 %', '0.14 %'], ['Czech Republic (Czechia)', 10708981, '0.18 %', 19772, 139, 77240, 22011, 1.6, 43, '74 %', '0.14 %'], ['Greece', 10423054, '-0.48 %', -50401, 81, 128900, -16000, 1.3, 46, '85 %', '0.13 %'], ['Jordan', 10203134, '1.00 %', 101440, 115, 88780, 10220, 2.8, 24, '91 %', '0.13 %'], ['Portugal', 10196709, '-0.29 %', -29478, 111, 91590, -6000, 1.3, 46, '66 %', '0.13 %'], ['Azerbaijan', 10139177, '0.91 %', 91459, 123, 82658, 1200, 2.1, 32, '56 %', '0.13 %'], ['Sweden', 10099265, '0.63 %', 62886, 25, 410340, 40000, 1.9, 41, '88 %', '0.13 %'], ['Honduras', 9904607, '1.63 %', 158490, 89, 111890, -6800, 2.5, 24, '57 %', '0.13 %'], ['United Arab Emirates', 9890402, '1.23 %', 119873, 118, 83600, 40000, 1.4, 33, '86 %', '0.13 %'], ['Hungary', 9660351, '-0.25 %', -24328, 107, 90530, 6000, 1.5, 43, '72 %', '0.12 %'], ['Tajikistan', 9537645, '2.32 %', 216627, 68, 139960, -20000, 3.6, 22, '27 %', '0.12 %'], ['Belarus', 9449323, '-0.03 %', -3088, 47, 202910, 8730, 1.7, 40, '79 %', '0.12 %'], ['Austria', 9006398, '0.57 %', 51296, 109, 82409, 65000, 1.5, 43, '57 %', '0.12 %'], ['Papua New Guinea', 8947024, '1.95 %', 170915, 20, 452860, -800, 3.6, 22, '13 %', '0.11 %'], ['Serbia', 8737371, '-0.40 %', -34864, 100, 87460, 4000, 1.5, 42, '56 %', '0.11 %'], ['Israel', 8655535, '1.60 %', 136158, 400, 21640, 10000, 3.0, 30, '93 %', '0.11 %'], ['Switzerland', 8654622, '0.74 %', 63257, 219, 39516, 52000, 1.5, 43, '74 %', '0.11 %'], ['Togo', 8278724, '2.43 %', 196358, 152, 54390, -2000, 4.4, 19, '43 %', '0.11 %'], ['Sierra Leone', 7976983, '2.10 %', 163768, 111, 72180, -4200, 4.3, 19, '43 %', '0.10 %'], ['Hong Kong', 7496981, '0.82 %', 60827, 7140, 1050, 29308, 1.3, 45, 'N.A.', '0.10 %'], ['Laos', 7275560, '1.48 %', 106105, 32, 230800, -14704, 2.7, 24, '36 %', '0.09 %'], ['Paraguay', 7132538, '1.25 %', 87902, 18, 397300, -16556, 2.4, 26, '62 %', '0.09 %'], ['Bulgaria', 6948445, '-0.74 %', -51674, 64, 108560, -4800, 1.6, 45, '76 %', '0.09 %'], ['Libya', 6871292, '1.38 %', 93840, 4, 1759540, -1999, 2.3, 29, '78 %', '0.09 %'], ['Lebanon', 6825445, '-0.44 %', -30268, 667, 10230, -30012, 2.1, 30, '78 %', '0.09 %'], ['Nicaragua', 6624554, '1.21 %', 79052, 55, 120340, -21272, 2.4, 26, '57 %', '0.08 %'], ['Kyrgyzstan', 6524195, '1.69 %', 108345, 34, 191800, -4000, 3.0, 26, '36 %', '0.08 %'], ['El Salvador', 6486205, '0.51 %', 32652, 313, 20720, -40539, 2.1, 28, '73 %', '0.08 %'], ['Turkmenistan', 6031200, '1.50 %', 89111, 13, 469930, -5000, 2.8, 27, '53 %', '0.08 %'], ['Singapore', 5850342, '0.79 %', 46005, 8358, 700, 27028, 1.2, 42, 'N.A.', '0.08 %'], ['Denmark', 5792202, '0.35 %', 20326, 137, 42430, 15200, 1.8, 42, '88 %', '0.07 %'], ['Finland', 5540720, '0.15 %', 8564, 18, 303890, 14000, 1.5, 43, '86 %', '0.07 %'], ['Congo', 5518087, '2.56 %', 137579, 16, 341500, -4000, 4.5, 19, '70 %', '0.07 %'], ['Slovakia', 5459642, '0.05 %', 2629, 114, 48088, 1485, 1.5, 41, '54 %', '0.07 %'], ['Norway', 5421241, '0.79 %', 42384, 15, 365268, 28000, 1.7, 40, '83 %', '0.07 %'], ['Oman', 5106626, '2.65 %', 131640, 16, 309500, 87400, 2.9, 31, '87 %', '0.07 %'], ['State of Palestine', 5101414, '2.41 %', 119994, 847, 6020, -10563, 3.7, 21, '80 %', '0.07 %'], ['Costa Rica', 5094118, '0.92 %', 46557, 100, 51060, 4200, 1.8, 33, '80 %', '0.07 %'], ['Liberia', 5057681, '2.44 %', 120307, 53, 96320, -5000, 4.4, 19, '53 %', '0.06 %'], ['Ireland', 4937786, '1.13 %', 55291, 72, 68890, 23604, 1.8, 38, '63 %', '0.06 %'], ['Central African Republic', 4829767, '1.78 %', 84582, 8, 622980, -40000, 4.8, 18, '43 %', '0.06 %'], ['New Zealand', 4822233, '0.82 %', 39170, 18, 263310, 14881, 1.9, 38, '87 %', '0.06 %'], ['Mauritania', 4649658, '2.74 %', 123962, 5, 1030700, 5000, 4.6, 20, '57 %', '0.06 %'], ['Panama', 4314767, '1.61 %', 68328, 58, 74340, 11200, 2.5, 30, '68 %', '0.06 %'], ['Kuwait', 4270571, '1.51 %', 63488, 240, 17820, 39520, 2.1, 37, 'N.A.', '0.05 %'], ['Croatia', 4105267, '-0.61 %', -25037, 73, 55960, -8001, 1.4, 44, '58 %', '0.05 %'], ['Moldova', 4033963, '-0.23 %', -9300, 123, 32850, -1387, 1.3, 38, '43 %', '0.05 %'], ['Georgia', 3989167, '-0.19 %', -7598, 57, 69490, -10000, 2.1, 38, '58 %', '0.05 %'], ['Eritrea', 3546421, '1.41 %', 49304, 35, 101000, -39858, 4.1, 19, '63 %', '0.05 %'], ['Uruguay', 3473730, '0.35 %', 11996, 20, 175020, -3000, 2.0, 36, '96 %', '0.04 %'], ['Bosnia and Herzegovina', 3280819, '-0.61 %', -20181, 64, 51000, -21585, 1.3, 43, '52 %', '0.04 %'], ['Mongolia', 3278290, '1.65 %', 53123, 2, 1553560, -852, 2.9, 28, '67 %', '0.04 %'], ['Armenia', 2963243, '0.19 %', 5512, 104, 28470, -4998, 1.8, 35, '63 %', '0.04 %'], ['Jamaica', 2961167, '0.44 %', 12888, 273, 10830, -11332, 2.0, 31, '55 %', '0.04 %'], ['Qatar', 2881053, '1.73 %', 48986, 248, 11610, 40000, 1.9, 32, '96 %', '0.04 %'], ['Albania', 2877797, '-0.11 %', -3120, 105, 27400, -14000, 1.6, 36, '63 %', '0.04 %'], ['Puerto Rico', 2860853, '-2.47 %', -72555, 323, 8870, -97986, 1.2, 44, 'N.A.', '0.04 %'], ['Lithuania', 2722289, '-1.35 %', -37338, 43, 62674, -32780, 1.7, 45, '71 %', '0.03 %'], ['Namibia', 2540905, '1.86 %', 46375, 3, 823290, -4806, 3.4, 22, '55 %', '0.03 %'], ['Gambia', 2416668, '2.94 %', 68962, 239, 10120, -3087, 5.3, 18, '59 %', '0.03 %'], ['Botswana', 2351627, '2.08 %', 47930, 4, 566730, 3000, 2.9, 24, '73 %', '0.03 %'], ['Gabon', 2225734, '2.45 %', 53155, 9, 257670, 3260, 4.0, 23, '87 %', '0.03 %'], ['Lesotho', 2142249, '0.80 %', 16981, 71, 30360, -10047, 3.2, 24, '31 %', '0.03 %'], ['North Macedonia', 2083374, '0.00 %', -85, 83, 25220, -1000, 1.5, 39, '59 %', '0.03 %'], ['Slovenia', 2078938, '0.01 %', 284, 103, 20140, 2000, 1.6, 45, '55 %', '0.03 %'], ['Guinea-Bissau', 1968001, '2.45 %', 47079, 70, 28120, -1399, 4.5, 19, '45 %', '0.03 %'], ['Latvia', 1886198, '-1.08 %', -20545, 30, 62200, -14837, 1.7, 44, '69 %', '0.02 %'], ['Bahrain', 1701575, '3.68 %', 60403, 2239, 760, 47800, 2.0, 32, '89 %', '0.02 %'], ['Equatorial Guinea', 1402985, '3.47 %', 46999, 50, 28050, 16000, 4.6, 22, '73 %', '0.02 %'], ['Trinidad and Tobago', 1399488, '0.32 %', 4515, 273, 5130, -800, 1.7, 36, '52 %', '0.02 %'], ['Estonia', 1326535, '0.07 %', 887, 31, 42390, 3911, 1.6, 42, '68 %', '0.02 %'], ['Timor-Leste', 1318445, '1.96 %', 25326, 89, 14870, -5385, 4.1, 21, '33 %', '0.02 %'], ['Mauritius', 1271768, '0.17 %', 2100, 626, 2030, 0, 1.4, 37, '41 %', '0.02 %'], ['Cyprus', 1207359, '0.73 %', 8784, 131, 9240, 5000, 1.3, 37, '67 %', '0.02 %'], ['Eswatini', 1160164, '1.05 %', 12034, 67, 17200, -8353, 3.0, 21, '30 %', '0.01 %'], ['Djibouti', 988000, '1.48 %', 14440, 43, 23180, 900, 2.8, 27, '79 %', '0.01 %'], ['Fiji', 896445, '0.73 %', 6492, 49, 18270, -6202, 2.8, 28, '59 %', '0.01 %'], ['Réunion', 895312, '0.72 %', 6385, 358, 2500, -1256, 2.3, 36, '100 %', '0.01 %'], ['Comoros', 869601, '2.20 %', 18715, 467, 1861, -2000, 4.2, 20, '29 %', '0.01 %'], ['Guyana', 786552, '0.48 %', 3786, 4, 196850, -6000, 2.5, 27, '27 %', '0.01 %'], ['Bhutan', 771608, '1.12 %', 8516, 20, 38117, 320, 2.0, 28, '46 %', '0.01 %'], ['Solomon Islands', 686884, '2.55 %', 17061, 25, 27990, -1600, 4.4, 20, '23 %', '0.01 %'], ['Macao', 649335, '1.39 %', 8890, 21645, 30, 5000, 1.2, 39, 'N.A.', '0.01 %'], ['Montenegro', 628066, '0.01 %', 79, 47, 13450, -480, 1.8, 39, '68 %', '0.01 %'], ['Luxembourg', 625978, '1.66 %', 10249, 242, 2590, 9741, 1.5, 40, '88 %', '0.01 %'], ['Western Sahara', 597339, '2.55 %', 14876, 2, 266000, 5582, 2.4, 28, '87 %', '0.01 %'], ['Suriname', 586632, '0.90 %', 5260, 4, 156000, -1000, 2.4, 29, '65 %', '0.01 %'], ['Cabo Verde', 555987, '1.10 %', 6052, 138, 4030, -1342, 2.3, 28, '68 %', '0.01 %'], ['Maldives', 540544, '1.81 %', 9591, 1802, 300, 11370, 1.9, 30, '35 %', '0.01 %'], ['Malta', 441543, '0.27 %', 1171, 1380, 320, 900, 1.5, 43, '93 %', '0.01 %'], ['Brunei', 437479, '0.97 %', 4194, 83, 5270, 0, 1.8, 32, '80 %', '0.01 %'], ['Guadeloupe', 400124, '0.02 %', 68, 237, 1690, -1440, 2.2, 44, 'N.A.', '0.01 %'], ['Belize', 397628, '1.86 %', 7275, 17, 22810, 1200, 2.3, 25, '46 %', '0.01 %'], ['Bahamas', 393244, '0.97 %', 3762, 39, 10010, 1000, 1.8, 32, '86 %', '0.01 %'], ['Martinique', 375265, '-0.08 %', -289, 354, 1060, -960, 1.9, 47, '92 %', '0.00 %'], ['Iceland', 341243, '0.65 %', 2212, 3, 100250, 380, 1.8, 37, '94 %', '0.00 %'], ['Vanuatu', 307145, '2.42 %', 7263, 25, 12190, 120, 3.8, 21, '24 %', '0.00 %'], ['French Guiana', 298682, '2.70 %', 7850, 4, 82200, 1200, 3.4, 25, '87 %', '0.00 %'], ['Barbados', 287375, '0.12 %', 350, 668, 430, -79, 1.6, 40, '31 %', '0.00 %'], ['New Caledonia', 285498, '0.97 %', 2748, 16, 18280, 502, 2.0, 34, '72 %', '0.00 %'], ['French Polynesia', 280908, '0.58 %', 1621, 77, 3660, -1000, 2.0, 34, '64 %', '0.00 %'], ['Mayotte', 272815, '2.50 %', 6665, 728, 375, 0, 3.7, 20, '46 %', '0.00 %'], ['Sao Tome & Principe', 219159, '1.91 %', 4103, 228, 960, -1680, 4.4, 19, '74 %', '0.00 %'], ['Samoa', 198414, '0.67 %', 1317, 70, 2830, -2803, 3.9, 22, '18 %', '0.00 %'], ['Saint Lucia', 183627, '0.46 %', 837, 301, 610, 0, 1.4, 34, '19 %', '0.00 %'], ['Channel Islands', 173863, '0.93 %', 1604, 915, 190, 1351, 1.5, 43, '30 %', '0.00 %'], ['Guam', 168775, '0.89 %', 1481, 313, 540, -506, 2.3, 31, '95 %', '0.00 %'], ['Curaçao', 164093, '0.41 %', 669, 370, 444, 515, 1.8, 42, '89 %', '0.00 %'], ['Kiribati', 119449, '1.57 %', 1843, 147, 810, -800, 3.6, 23, '57 %', '0.00 %'], ['Micronesia', 115023, '1.06 %', 1208, 164, 700, -600, 3.1, 24, '21 %', '0.00 %'], ['Grenada', 112523, '0.46 %', 520, 331, 340, -200, 2.1, 32, '35 %', '0.00 %'], ['St. Vincent & Grenadines', 110940, '0.32 %', 351, 284, 390, -200, 1.9, 33, '53 %', '0.00 %'], ['Aruba', 106766, '0.43 %', 452, 593, 180, 201, 1.9, 41, '44 %', '0.00 %'], ['Tonga', 105695, '1.15 %', 1201, 147, 720, -800, 3.6, 22, '24 %', '0.00 %'], ['U.S. Virgin Islands', 104425, '-0.15 %', -153, 298, 350, -451, 2.0, 43, '96 %', '0.00 %'], ['Seychelles', 98347, '0.62 %', 608, 214, 460, -200, 2.5, 34, '56 %', '0.00 %'], ['Antigua and Barbuda', 97929, '0.84 %', 811, 223, 440, 0, 2.0, 34, '26 %', '0.00 %'], ['Isle of Man', 85033, '0.53 %', 449, 149, 570, 'N.A.', 'N.A.', '53 %', '0.00 %'], ['Andorra', 77265, '0.16 %', 123, 164, 470, 'N.A.', 'N.A.', '88 %', '0.00 %'], ['Dominica', 71986, '0.25 %', 178, 96, 750, 'N.A.', 'N.A.', '74 %', '0.00 %'], ['Cayman Islands', 65722, '1.19 %', 774, 274, 240, 'N.A.', 'N.A.', '97 %', '0.00 %'], ['Bermuda', 62278, '-0.36 %', -228, 1246, 50, 'N.A.', 'N.A.', '97 %', '0.00 %'], ['Marshall Islands', 59190, '0.68 %', 399, 329, 180, 'N.A.', 'N.A.', '70 %', '0.00 %'], ['Northern Mariana Islands', 57559, '0.60 %', 343, 125, 460, 'N.A.', 'N.A.', '88 %', '0.00 %'], ['Greenland', 56770, '0.17 %', 98, 0, 410450, 'N.A.', 'N.A.', '87 %', '0.00 %'], ['American Samoa', 55191, '-0.22 %', -121, 276, 200, 'N.A.', 'N.A.', '88 %', '0.00 %'], ['Saint Kitts & Nevis', 53199, '0.71 %', 376, 205, 260, 'N.A.', 'N.A.', '33 %', '0.00 %'], ['Faeroe Islands', 48863, '0.38 %', 185, 35, 1396, 'N.A.', 'N.A.', '43 %', '0.00 %'], ['Sint Maarten', 42876, '1.15 %', 488, 1261, 34, 'N.A.', 'N.A.', '96 %', '0.00 %'], ['Monaco', 39242, '0.71 %', 278, 26337, 1, 'N.A.', 'N.A.', 'N.A.', '0.00 %'], ['Turks and Caicos', 38717, '1.38 %', 526, 41, 950, 'N.A.', 'N.A.', '89 %', '0.00 %'], ['Saint Martin', 38666, '1.75 %', 664, 730, 53, 'N.A.', 'N.A.', '0 %', '0.00 %'], ['Liechtenstein', 38128, '0.29 %', 109, 238, 160, 'N.A.', 'N.A.', '15 %', '0.00 %'], ['San Marino', 33931, '0.21 %', 71, 566, 60, 'N.A.', 'N.A.', '97 %', '0.00 %'], ['Gibraltar', 33691, '-0.03 %', -10, 3369, 10, 'N.A.', 'N.A.', 'N.A.', '0.00 %'], ['British Virgin Islands', 30231, '0.67 %', 201, 202, 150, 'N.A.', 'N.A.', '52 %', '0.00 %'], ['Caribbean Netherlands', 26223, '0.94 %', 244, 80, 328, 'N.A.', 'N.A.', '75 %', '0.00 %'], ['Palau', 18094, '0.48 %', 86, 39, 460, 'N.A.', 'N.A.', 'N.A.', '0.00 %'], ['Cook Islands', 17564, '0.09 %', 16, 73, 240, 'N.A.', 'N.A.', '75 %', '0.00 %'], ['Anguilla', 15003, '0.90 %', 134, 167, 90, 'N.A.', 'N.A.', 'N.A.', '0.00 %'], ['Tuvalu', 11792, '1.25 %', 146, 393, 30, 'N.A.', 'N.A.', '62 %', '0.00 %'], ['Wallis & Futuna', 11239, '-1.69 %', -193, 80, 140, 'N.A.', 'N.A.', '0 %', '0.00 %'], ['Nauru', 10824, '0.63 %', 68, 541, 20, 'N.A.', 'N.A.', 'N.A.', '0.00 %'], ['Saint Barthelemy', 9877, '0.30 %', 30, 470, 21, 'N.A.', 'N.A.', '0 %', '0.00 %'], ['Saint Helena', 6077, '0.30 %', 18, 16, 390, 'N.A.', 'N.A.', '27 %', '0.00 %'], ['Saint Pierre & Miquelon', 5794, '-0.48 %', -28, 25, 230, 'N.A.', 'N.A.', '100 %', '0.00 %'], ['Montserrat', 4992, '0.06 %', 3, 50, 100, 'N.A.', 'N.A.', '10 %', '0.00 %'], ['Falkland Islands', 3480, '3.05 %', 103, 0, 12170, 'N.A.', 'N.A.', '66 %', '0.00 %'], ['Niue', 1626, '0.68 %', 11, 6, 260, 'N.A.', 'N.A.', '46 %', '0.00 %'], ['Tokelau', 1357, '1.27 %', 17, 136, 10, 'N.A.', 'N.A.', '0 %', '0.00 %'], ['Holy See', 801, '0.25 %', 2, 2003, 0, 'N.A.', 'N.A.', 'N.A.', '0.00 %']])

clean_country = re.compile(r'[,\(\)]')
country_cleanup = {
    'united states': 'united states of america',
    'korea south': 'korea, republic of',
    'south korea': 'KOREA, REPUBLIC OF',
    'north korea': "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF",
    'england': 'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND',
    'scotland': 'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND',
    'wales': 'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND',
    'russia federation': 'RUSSIAN FEDERATION',
    'russia': 'RUSSIAN FEDERATION',
    'iran': 'IRAN, ISLAMIC REPUBLIC OF',
    'vietnam': 'VIET NAM',
    'dr congo': 'CONGO, DEMOCRATIC REPUBLIC OF THE',
    'united kingdom': 'UNITED KINGDOM OF GREAT BRITAIN AND NORTHERN IRELAND',
    'tanzania': 'TANZANIA, UNITED REPUBLIC OF',
    'venezuela': 'VENEZUELA, BOLIVARIAN REPUBLIC OF',
    'taiwan': 'TAIWAN, PROVINCE OF CHINA',
    'syria': 'SYRIAN ARAB REPUBLIC',
    'bolivia': 'BOLIVIA, PLURINATIONAL STATE OF',
    'czech republic czechia': 'CZECHIA',
    'laos': "LAO PEOPLE'S DEMOCRATIC REPUBLIC",
    'state of palestine': 'PALESTINE, STATE OF',
    'moldova': 'MOLDOVA, REPUBLIC OF',
    'brunei': 'BRUNEI DARUSSALAM',}


def country2code(country):
    country = clean_country.sub('', country.partition(':')[0].strip(), count=100).lower()
    country = country_cleanup.get(country, country)
    cc = countries_by_name.get(country.upper())
    if cc is None:
        print('country %s not found ~ '%country)
        return None
    return cc.alpha3


def fetch_docs(index, annotations=None):
    kwargs = {}
    if annotations:
        kwargs = {'body': deepcopy(es_query)}
        kwargs['body']['query']['bool']['must'] = [{'match': {'annotations.'+k:vv.strip('#')}} for k,v in annotations.items() for vv in v.split(',')]
        print(kwargs)
    docs = []
    chunk_hits = 10000
    r = es.search(index=index, size=chunk_hits, scroll='2s', **kwargs)
    while len(r['hits']['hits']):
        docs.extend(r['hits']['hits'])
        r = es.scroll(scroll_id = r['_scroll_id'], scroll = '2s')
    docs = [d['_source'] for d in docs]
    docs = [d for d in docs if d['date']] # only keep documents with dates
    return docs


def calc():
    cc2score = defaultdict(int)
    for index in ['pubtator-covid-19', 'pubtator-cardiac-failure', 'pubtator-tech']:
        try:
            docs = fetch_docs(index=index)
            for doc in docs:
                journal,doip = journal_util.extract(doc['journal'])
                cc = journal2country_code.get(journal)
                if not cc:
                    cc = doi2cc.get(doip)
                if cc:
                    cc2score[cc] += 1
        except:
            pass
    return cc2score


df['cc'] = [country2code(c) for c in df['Country']]
cc2score = calc()
for k,v in sorted(cc2score.items(), key=lambda kv:-kv[1]):
    df.loc[df['cc']==k, 'Score'] = v

df['Articles per capita'] = df['Score'] / df['Population (2020)']
df['c'] = [''.join(c for c in w if c.isupper()) if 'United' in w else w for w in df['Country']]
df = df.sort_values('Articles per capita', ascending=False).dropna().reset_index(drop=True)
df = df.iloc[:20, :]
print(df)
import matplotlib.pyplot as plt
plt.title('Medical science articles per capita')
plt.pie(df['Articles per capita'], labels=df['c'], normalize=True)
plt.show()