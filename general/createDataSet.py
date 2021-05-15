import re
import numpy as np
import pandas as pd
import argparse

# Key columns
PROGRAM='Programa'
GROUP='Grupo'
TYPE='Tipo'
YEAR='Año'
VALUE='Valor'
INC='Incremento'

# Constants
INC_SUFFIX = 'inc'
INCOME = 'ingreso'
OUTCOME = 'gasto'

# Parsing paramenters (Constants for the moment)
YEARS = ['2012', '2013', '2014', '2015', '2016', '2017','2018', '2018-P', '2019-P', '2021']

# Income parse params
REGEX_INCOME_HEADER = '^(Capítulos)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)  *(2021)$'
REGEX_INCOME_DATA_GROUP = '^([A-Z][a-zA-Zñ -áéíóú]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'
NO_FINANCIAL_OPERATIONS = 'OPERACIONES NO FINANCIERAS'
FINANCIAL_OPERATIONS = 'OPERACIONES FINANCIERAS'
END_MARK = 'TOTAL CAPÍTULOS 1 a 8'

# Outcome parser params
REGEX_OUTCOME_HEADER = '^(Programas)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)  *(2021)$'
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

def __melt__(df, years, value_field):
	dfm=df.melt(id_vars=[PROGRAM,GROUP,TYPE], value_vars=years)
	dfm.columns=[PROGRAM,GROUP,TYPE,YEAR,value_field]
	return dfm

def mainParse(fileIn, fileOut):
	# Process income
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
					if (x_data[1] == NO_FINANCIAL_OPERATIONS):
						group = x_data[1]
					elif (x_data[1] == END_MARK):
						group = FINANCIAL_OPERATIONS
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

	income = pd.DataFrame(data, columns=([PROGRAM] + YEARS + [GROUP]))
	for y in YEARS:
		income[y] = income[y].apply(lambda x: pd.to_numeric(x.replace('.','')))

	# Process Outcome
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

	outcome = pd.DataFrame(data, columns=([PROGRAM] + YEARS + [GROUP]))
	for y in YEARS:
		outcome[y] = outcome[y].apply(lambda x: pd.to_numeric(x.replace('.','')))

	# merging income and outcome in the same dataset
	income[TYPE] = INCOME
	outcome[TYPE] = OUTCOME
	budget = pd.concat([income, outcome])

	# Calculating percentage increments
	for i in np.arange(len(YEARS)-1):
		budget['_'.join([YEARS[i+1],INC_SUFFIX])] = budget[[YEARS[i],YEARS[i+1]]].apply(__increment__, axis=1)

	# Melting
	budget_abs = budget[[PROGRAM,GROUP,TYPE] + YEARS]
	budget_rel = budget[[PROGRAM,GROUP,TYPE] + ['_'.join([x,INC_SUFFIX]) for x in YEARS[1:]]]
	budget_rel.columns = [PROGRAM,GROUP,TYPE] + YEARS[1:]

	budget_abs_melt = __melt__(budget_abs, YEARS, VALUE)
	budget_rel_melt = __melt__(budget_rel, YEARS[1:], INC)
	budget_melt = budget_abs_melt.merge(budget_rel_melt, how='outer', on=[PROGRAM,GROUP,TYPE,YEAR])

	budget_melt.to_csv(fileOut, sep=';', decimal=',', index=False)

if (__name__ == "__main__"):
	parser = argparse.ArgumentParser(description="Creating dataset for state budget analysis")
	parser.add_argument("--fileIn", required=False, help="Input files (If more than one, use comma separated)")
	parser.add_argument("--fileOut", required=False, help="Output file")

	args = parser.parse_args()
	mainParse(args.fileIn, args.fileOut)
