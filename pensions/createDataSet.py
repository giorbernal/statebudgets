import sys
import numpy as np
import pandas as pd

AGE=sys.argv[1]
AGE_MELT=sys.argv[2]
IMP=sys.argv[3]
IMP_MELT=sys.argv[4]

# Aging file process
print('processing aging file ...')
dfe = pd.read_csv(AGE, sep=';')
dfe.set_index(keys='Rangos de edad', drop=True, inplace=True)
dfe.drop(columns=['Número pensiones.5','Pensión media.5','Importe total nómina.5','Unnamed: 19'], axis=0, inplace=True)
dfe.columns=pd.MultiIndex.from_arrays([['Incapacidad','Incapacidad','Incapacidad','Jubilación','Jubilación','Jubilación','Viudedad','Viudedad','Viudedad','Orfandad','Orfandad','Orfandad','FF','FF','FF'],['N','Media','Total','N','Media','Total','N','Media','Total','N','Media','Total','N','Media','Total']])
dfe.reset_index(inplace=True)
dfef=dfe.iloc[0:19]
dfefm = dfef.melt(id_vars=['Rangos de edad'], value_vars=['Incapacidad','Jubilación','Viudedad','Orfandad','FF'])
dfefm.columns=['Rango de edad','tipo','variable','valor']
dfefmp=pd.pivot_table(data=dfefm, index=['Rango de edad','tipo'], columns=['variable'], values='valor', aggfunc=np.sum)
dfefmp.reset_index(inplace=True)
dfefmp.to_csv(AGE_MELT, sep=';', index=False)
print('aging file processed!')

# Imports file process
print('processing imports file ...')
dft = pd.read_csv(IMP, sep=';')
dft.drop(columns=['Número pensiones.5','Unnamed: 7'], inplace=True, axis=0)
dft.columns=['Tramos','Incapacidad','Jubilación','Viudedad','Orfandad','FF']
dftf=dft.iloc[0:35]
dftfm=pd.melt(dftf, id_vars=['Tramos'], value_vars=['Incapacidad','Jubilación','Viudedad','Orfandad','FF'])
dftfm.columns=['Tramos','tipo','valor']
dftfm.to_csv(IMP_MELT, sep=';', index=False)
print('imports file processed!')
