# State Budgets

This is an analysis project for the state budgets of Spain.

## Requirements
Python is needed (version 3.6 preferred) and next libraries must be installed in the environment:
- numpy
- pandas

## Analysis
We have developed different analysis:

### General Budgets
The info has been extracted from [here](https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/DocumentacionEstadisticas/Estadisticas/Paginas/Estadisticas.aspx) in .pdf format. Then we have transformed the file to .csv format by using [this](https://convertio.co/es/pdf-csv/) on line tool.

Executing [createDataSet.sh](general/createDataSet.sh) file, the data will be adapted to the *_melt.csv contained in the general/dataset folder.

With this dataset we have developed a Tableau visualization. The result can be observed [here](https://public.tableau.com/profile/gior6119#!/vizhome/Presupuestos_16029571731530/Historia1).

### Pensions

In this case we have developed an analysis over the *contributive* pensions. The information has been extracted from [here](https://w6.seg-social.es/ProsaInternetAnonimo/OnlineAccess?ARQ.SPM.ACTION=LOGIN&ARQ.SPM.APPTYPE=SERVICE&ARQ.IDAPP=ESTA0001) in form of two .csv files: *edad.csv* and *tramos.csv*. The headers of both of them has been adapted (by hand) in *edad2.csv* and *tramos2.csv* respectively.

Executing [createDataSet.sh](pensions/createDataSet.sh) we could get the .csv files to analysis: edad_melt.csv and tramos_melt.csv.

With this dataset we have developed a Tableau visualization. The result can be observed [here](https://public.tableau.com/profile/gior6119#!/vizhome/Pensiones_16026224709640/Edad-Tipo-Total-Media).

### Autonomic Budgets
Not implemented yet.

