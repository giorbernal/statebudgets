---
name: download-budgets
description: Descarga de la fuente original los presupuestos de un año en particular y lo guarda un path local
license: MIT
compatibility: opencode
---

## What I do

Para un año en concreto "x" debemos crear una carpeta x en la ruta pge/, es decir, quedaría pge/x/, en la que se almacenará la información descargada.

Hay que tener en cuenta los siguientes puntos para realizar esta tarea:

* Si la carpeta x existe ya en la ruta pge/ habrá que borrarla inicialmente con todo su contenido. 
* La descarga de información se realiza de la siguiente ruta: https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/PGE/Paginas/PresupuestosGE.aspx. Aqui se encontran dos opciones principales.
  * La del año en curso
  * Otro enlace, dentro del cual, encontraremos enlaces para cada año de los anteriores. Dentro de cada uno de dichos enlaces encontraremos la información de los años anteriores.
* La información debe consolidarse en la descarga y posterior descompresión de un .zip bajo el enlace "  Versión comprimida (.zip) de los Presupuestos" (No la versión en formato "tomos")
* Si no se encuentra el enlace anterior debe indicarse claramente esta circunstancia.

## When to use me

Usa esto cuando necesites obtener la información fuente de los presupuestos del estado para un determinado año.
