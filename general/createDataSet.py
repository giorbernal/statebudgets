import sys
import re
import numpy as np
import pandas as pd

SEP=';'
REGEX_HEADER='^(Programas)  *(2011)  *(2012)  *(2013)  *(2014)  *(2015)  *(2016)  *(2017)  *(2018)  *(2018-P)  *(2019-P)$'
REGEX_DATA='^([0-9][0-9][0-9][A-Z] ?:? [a-zA-Zñ -áéíóú]+[a-zA-Z\)\.áéíóú])  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'
REGEX_DATA_INCOMPLETED='^([0-9][0-9][0-9][A-Z] ?:? [a-zA-Zñ -áéíóú]+[a-zA-Z\)\.áéíóú])  ([0-9 \.]*)$'
REGEX_GROUP='^[0-9][0-9] ([A-ZÑ\. -ÁÉÍÓÚ]+[A-Z\.ÁÉÍÓÚ])  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)  *([0-9]+\.?[0-9]*)$'

LEN_DATA_PROGRAM=73
LEN_DATA_SLOT=12

TOTAL_DATA=10

def processDataIncompleted(reg):
	ref = LEN_DATA_PROGRAM-len(reg[1])
	rest='  ' + reg[2][(ref if ref>0 else 0):]
	data=[x for x in rest.strip().split(' ') if x != '']
	if (rest[:LEN_DATA_SLOT].strip() == ''):
		#print('   ','END',reg,data)
		return (SEP + reg[1] + SEP + SEP.join(np.concatenate([np.zeros(TOTAL_DATA-len(data),dtype='int32'),np.array(data)]).tolist()) + SEP + '\n')
	else:
		#print('   ','INIT',reg,data)
		return (SEP + reg[1] + SEP + SEP.join(np.concatenate([np.array(data),np.zeros(TOTAL_DATA-len(data),dtype='int32')]).tolist()) + SEP + '\n')

def main_parse():
	header_found=False

	data_block = []

	with open(sys.argv[2], 'r') as reader:
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
						#processDataIncompleted(x_data)
						data_block.append(processDataIncompleted(x_data))
						#print(processDataIncompleted(x_data))
					else:
						x_group = re.split(REGEX_GROUP, line)
						if (len(x_group) > 1):
							for i in np.arange(len(data_block)):
								print(data_block[i][:-1] + x_group[1])
							data_block = []
			line = reader.readline()

def melt():
	df=pd.read_csv(sys.argv[2],sep=';', decimal=',')
	df.drop(columns=['Unnamed: 0'],axis=1,inplace=True)
	dfm=df.melt(id_vars=['Programas','Grupo'], value_vars=['2011', '2012', '2013', '2014', '2015', '2016', '2017','2018', '2018-P', '2019-P'])
	dfm.columns=['Programas','Grupo','Año','Valor']
	dfm.to_csv(sys.argv[3],sep=';', decimal=',', index=False);

if (len(sys.argv[1:]) < 1):
	print('Error in params!')
	print('Usage: > python createDataSet.py <mode> (mode: 1(main_parse)/2(melt) )')
	exit(-1);

switcher = {
	'1': main_parse,
	'2': melt
}

func = switcher.get(sys.argv[1], lambda: 'Invalid argument')
func()
