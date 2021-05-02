import sys
import re
import numpy as np
import pandas as pd
import argparse
from collections import defaultdict

years = defaultdict()
years['2020'] = (
	['2011', '2012', '2013', '2014', '2015', '2016', '2017','2018', '2018-P', '2019-P'],
	'^(Programas)  *(2011)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)$'
)
years['2021'] = (
	['2012', '2013', '2014', '2015', '2016', '2017','2018', '2018-P', '2019-P', '2021'],
	'^(Programas)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)  *(2021)$'
)

SEP=';'
REGEX_DATA='^([0-9][0-9][0-9][A-Z] ?:? [a-zA-Zñ -áéíóú]+[a-zA-Z\)\.áéíóú])  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'
REGEX_DATA_INCOMPLETED='^([0-9][0-9][0-9][A-Z] ?:? [a-zA-Zñ -áéíóú]+[a-zA-Z\)\.áéíóú])  ([0-9 \.]*)$'
REGEX_GROUP='^[0-9][0-9] ([A-ZÑ\. -ÁÉÍÓÚ]+[A-Z\.ÁÉÍÓÚ])  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'

LEN_DATA_PROGRAM=73
LEN_DATA_SLOT=12

TOTAL_DATA=10

def __processDataIncompleted__(reg):
	ref = LEN_DATA_PROGRAM-len(reg[1])
	rest='  ' + reg[2][(ref if ref>0 else 0):]
	data=[x for x in rest.strip().split(' ') if x != '']
	if (rest[:LEN_DATA_SLOT].strip() == ''):
		#print('   ','END',reg,data)
		return (SEP + reg[1] + SEP + SEP.join(np.concatenate([np.zeros(TOTAL_DATA-len(data),dtype='int32'),np.array(data)]).tolist()) + SEP + '\n')
	else:
		#print('   ','INIT',reg,data)
		return (SEP + reg[1] + SEP + SEP.join(np.concatenate([np.array(data),np.zeros(TOTAL_DATA-len(data),dtype='int32')]).tolist()) + SEP + '\n')

def mainParse(fileIn, year):
	REGEX_HEADER = years[year][1]

	header_found=False

	data_block = []

	with open(fileIn, 'r') as reader:
		line=reader.readline()
		while line != '':  # The EOF char is an empty string
			if (header_found == False):
				x_head = re.split(REGEX_HEADER, line)
				if (len(x_head) > 1):
					print(SEP.join(x_head)[:-1] + 'Grupo')
					header_found=True
			else:
				x_data = re.split(REGEX_DATA, line)
				if (len(x_data) > 1):
					data_block.append(SEP.join(x_data))
					#print(SEP.join(x_data))
				else:
					x_data = re.split(REGEX_DATA_INCOMPLETED, line)
					if (len(x_data) > 1):
						#__processDataIncompleted__(x_data)
						data_block.append(__processDataIncompleted__(x_data))
						#print(__processDataIncompleted__(x_data))
					else:
						x_group = re.split(REGEX_GROUP, line)
						if (len(x_group) > 1):
							for i in np.arange(len(data_block)):
								print(data_block[i][:-1] + x_group[1])
							data_block = []
			line = reader.readline()

def melt(fileIn, fileOut, year):
	df=pd.read_csv(fileIn,sep=';', decimal=',')
	df.drop(columns=['Unnamed: 0'],axis=1,inplace=True)
	dfm=df.melt(id_vars=['Programas','Grupo'], value_vars=years[year][0])
	dfm.columns=['Programas','Grupo','Año','Valor']
	dfm.to_csv(fileOut,sep=';', decimal=',', index=False);

def concatBudgets(fileIns, fileOut):
	file_in_list = fileIns.split(',')
	dfs = [pd.read_csv(x, sep=';', decimal=',') for x in file_in_list]
	dfc = pd.concat(dfs).drop_duplicates().reset_index(drop=True)
	dfc.to_csv(fileOut,sep=';', decimal=',', index=False);

if (__name__ == "__main__"):
	parser = argparse.ArgumentParser(description="Creating dataset for state budget analysis")
	parser.add_argument("--command", required=True, help="PARSE | MELT | CONCAT")
	parser.add_argument("--fileIn", required=False, help="Input files (If more than one, use comma separated)")
	parser.add_argument("--fileOut", required=False, help="Output file")
	parser.add_argument("--year", required=False, help="year of budget")

	args = parser.parse_args()
	if (args.command == 'PARSE'):
		mainParse(args.fileIn, args.year)
	elif (args.command == 'MELT'):
		melt(args.fileIn, args.fileOut, args.year)
	elif (args.command == 'CONCAT'):
		concatBudgets(args.fileIn, args.fileOut)
	else:
		print('Invalid command')
