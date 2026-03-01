---
name: build-budgets-csv
description: Genera, para un año concreto, el .csv donde se definene el gasto de los presupuestos generales de ese año
license: MIT
compatibility: opencode
---

## What I do

Para un año en concreto "x" entrar en la ruta pge/x/, una vez allí realizar los siguientes pasos.

* Creamos un fichero "spending.csv" (lo borramos si ya existe).
* Buscaremos en PGE-ROM.htm el enlace a la "Serie roja", despues "Gastos. Presupuesto por programas y memoria de objetivos". Allí encontraremos un listado de secciones.
* Entraremos en cada una de las secciones y buscaremos "Presupuesto por programas" -> "Resumen económico por programas del presupuesto de gastos", trantando de buscar el .html que define este punto.
  * De cada fichero que allí encontremos (En esta ruta puedes ver un ejemplo: /pge/2024/PGE-ROM/doc/HTM/N_23P_E_R_31_107_1_1_3_1.HTM), queremos volcar en spending.csv tantas filas como filas aparezcan con un valor en la columna "Clasif. por programas", en cada fila solo incluiremos los dos primeros campos y el último, aquí tenemos un ejemplo de cómo quedarían las filas en este fichero:
  ```
  211B;Pensiones de Clases Pasivas;20.369.000,89
  211C;Otras pensiones y prestaciones de Clases Pasivas;49.447,74
  212B;Pensiones de guerra;81.093,93
  000X;Transferencias y libramientos internos,249,75
  ```
  * En los códigos 000x, el segundo campo del csv, tiene que llevar adicionalmente el nombre de la sección entre paréntesis. Aqui vemos como quedaría en el ejemplo:
  ```
  000X;Transferencias y libramientos internos (Sección: 07 CLASES PASIVAS);249,75
  ```
  * Finalmente, añadiremos en cada registro una última columna cuyo valor extraeremos de la siguiente manera:
    * Toma el primer campo del registro y quédate con los dos primeros caracteres
    * Busca en "políticas_gastos.txt" un registro que empiece por estos caracteres y añadelo como valor de la ultima columna
    * En el caso del código 00 no se encuentra correspondencia con líneas de "políticas_gastos.txt", pero pondremos el que mas ocurra en el resto de los registros.
  * En el ejemplo quedaría asi:
  ```
  211B;Pensiones de Clases Pasivas;20.369.000,89;21. PENSIONES
  211C;Otras pensiones y prestaciones de Clases Pasivas;49.447,74;21. PENSIONES
  212B;Pensiones de guerra;81.093,93;21. PENSIONES
  000X;Transferencias y libramientos internos (Sección: 07 CLASES PASIVAS);249,75;21. PENSIONES
  ```


## When to use me

Usa esto cuando necesites obtener en formato .csv los gastos de los presupuestos generales