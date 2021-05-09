import sys
import re
import numpy as np
import pandas as pd
import argparse
from collections import defaultdict

years = defaultdict()
years['2020'] = (
	['2011', '2012', '2013', '2014', '2015', '2016', '2017','2018', '2018-P', '2019-P'],
	'^(Programas)  *(2011)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)$',
	'^(Capítulos)  *(2011)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)$',
)
years['2021'] = (
	['2012', '2013', '2014', '2015', '2016', '2017','2018', '2018-P', '2019-P', '2021'],
	'^(Programas)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)  *(2021)$',
	'^(Capítulos)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)  *(2021)$',
)

REGEX_INCOME_DATA_GROUP='^([A-Z][a-zA-Zñ -áéíóú]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'

REGEX_OUTCOME_DATA= '^([0-9][0-9][0-9][A-Z] ?:? [a-zA-Zñ -áéíóú]+[a-zA-Z\)\.áéíóú])  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'
REGEX_OUTCOME_DATA_INCOMPLETED= '^([0-9][0-9][0-9][A-Z] ?:? [a-zA-Zñ -áéíóú]+[a-zA-Z\)\.áéíóú])  ([0-9 \.]*)$'
REGEX_OUTCOME_GROUP= '^[0-9][0-9] ([A-ZÑ\. -ÁÉÍÓÚ]+[A-Z\.ÁÉÍÓÚ])  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'

LEN_OUTCOME_DATA_PROGRAM=73
LEN_OUTCOME_DATA_SLOT=12

TOTAL_OUTCOME_DATA=10

def __processDataIncompleted__(reg):
	ref = LEN_OUTCOME_DATA_PROGRAM - len(reg[1])
	rest='  ' + reg[2][(ref if ref>0 else 0):]
	data=[x for x in rest.strip().split(' ') if x != '']
	if (rest[:LEN_OUTCOME_DATA_SLOT].strip() == ''):
		return np.concatenate([[reg[1]], np.zeros(TOTAL_OUTCOME_DATA - len(data), dtype='int32'), np.array(data)]).tolist()
	else:
		return np.concatenate([[reg[1]], np.array(data), np.zeros(TOTAL_OUTCOME_DATA - len(data), dtype='int32')]).tolist()

def __increment__(x):
	xnp = x.to_numpy()
	last = xnp[1:]
	init = xnp[:-1] + 0.001
	result = [100 if x > 100 else np.round(x) for x in ((last-init)/init*100).tolist()]
	return result[0]


def mainParse(fileIn, year):
	# Process income
	REGEX_INCOME_HEADER=years[year][2]
	header_found=False
	data = []
	data_block = []
	exit = False
	with open(fileIn, 'r') as reader:
		line=reader.readline()
		while (line != '') & ~exit:  # The EOF char is an empty string
			if (header_found == False):
				x_head = re.split(REGEX_INCOME_HEADER, line)
				if (len(x_head) > 1):
					header_found=True
			else:
				x_data = [x.strip() for x in re.split(REGEX_INCOME_DATA_GROUP, line)]
				if (len(x_data) > 1):
					if (x_data[1] == 'OPERACIONES NO FINANCIERAS'):
						group = x_data[1]
					elif (x_data[1] == 'TOTAL CAPÍTULOS 1 a 8'):
						group = 'OPERACIONES FINANCIERAS'
						exit = True
					else:
						group = ''

					if (group != ''):
						for i in np.arange(len(data_block)):
							reg = data_block[i].copy()
							reg.append(group)
							data.append(reg)
						data_block = []
					else:
						data_block.append(x_data[1:-1])

			line = reader.readline()

	income = pd.DataFrame(data, columns=['Programas','2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021','Grupo'])
	income[['2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021']] = income[['2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021']].apply(pd.to_numeric)

	# Process Outcome
	REGEX_OUTCOME_HEADER = years[year][1]
	header_found=False
	data = []
	data_block = []
	with open(fileIn, 'r') as reader:
		line=reader.readline()
		while line != '':  # The EOF char is an empty string
			if (header_found == False):
				x_head = re.split(REGEX_OUTCOME_HEADER, line)
				if (len(x_head) > 1):
					header_found=True
			else:
				x_data = re.split(REGEX_OUTCOME_DATA, line)
				if (len(x_data) > 1):
					data_block.append(x_data[1:-1])
				else:
					x_data = re.split(REGEX_OUTCOME_DATA_INCOMPLETED, line)
					if (len(x_data) > 1):
						data_block.append(__processDataIncompleted__(x_data))
					else:
						x_group = re.split(REGEX_OUTCOME_GROUP, line)
						if (len(x_group) > 1):
							for i in np.arange(len(data_block)):
								reg = data_block[i].copy()
								reg.append(x_group[1])
								data.append(reg)
							data_block = []
			line = reader.readline()

	outcome = pd.DataFrame(data, columns=['Programas','2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021','Grupo'])
	outcome[['2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021']] = outcome[['2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021']].apply(pd.to_numeric)

	# merging income and outcome in the same dataset
	income['Tipo'] = 'ingreso'
	outcome['Tipo'] = 'gasto'
	budget = pd.concat([income, outcome])
	budget.info()

	# Calculating percentage increments
	budget['2013_inc'] = budget[['2012','2013']].apply(__increment__, axis=1)
	budget['2014_inc'] = budget[['2013','2014']].apply(__increment__, axis=1)
	budget['2015_inc'] = budget[['2014','2015']].apply(__increment__, axis=1)
	budget['2016_inc'] = budget[['2015','2016']].apply(__increment__, axis=1)
	budget['2017_inc'] = budget[['2016','2017']].apply(__increment__, axis=1)
	budget['2018_inc'] = budget[['2017','2018']].apply(__increment__, axis=1)
	budget['2018-P_inc'] = budget[['2018','2018-P']].apply(__increment__, axis=1)
	budget['2019-P_inc'] = budget[['2018-P','2019-P']].apply(__increment__, axis=1)
	budget['2021_inc'] = budget[['2019-P','2021']].apply(__increment__, axis=1)

	# Melting
	budget_abs = budget[['Programas','Grupo','Tipo','2012','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021']]
	budget_rel = budget[['Programas','Grupo','Tipo','2013_inc','2014_inc','2015_inc','2016_inc','2017_inc','2018_inc','2018-P_inc','2019-P_inc','2021_inc']]
	budget_rel.columns = ['Programas','Grupo','Tipo','2013','2014','2015','2016','2017','2018','2018-P','2019-P','2021']
	budget.info()
	# TODO

def melt(fileIn, fileOut, year):
	df=pd.read_csv(fileIn,sep=';', decimal=',')
	df.drop(columns=['Unnamed: 0'],axis=1,inplace=True)
	dfm=df.melt(id_vars=['Programas','Grupo'], value_vars=years[year][0])
	dfm.columns=['Programas','Grupo','Año','Valor']
	dfm.to_csv(fileOut,sep=';', decimal=',', index=False);

if (__name__ == "__main__"):
	parser = argparse.ArgumentParser(description="Creating dataset for state budget analysis")
	parser.add_argument("--fileIn", required=False, help="Input files (If more than one, use comma separated)")
	parser.add_argument("--fileOut", required=False, help="Output file")
	parser.add_argument("--year", required=False, help="year of budget")

	args = parser.parse_args()
	mainParse(args.fileIn, args.year)
