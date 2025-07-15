@echo off
REM Este script ejecuta odontograma.py con los parámetros predefinidos.

set SCRIPT_PATH="odontograma.py"
REM Si el script .bat está en la carpeta Dental, entonces solo "odontograma.py" está bien.
REM Si no, usa la ruta completa: set SCRIPT_PATH="C:\Users\wbenitez\Downloads\Git\Dental\odontograma.py"

REM Define tus parámetros aquí. Es bueno mantener las comillas para claridad, aunque no siempre críticas aquí.
set CREDENCIAL="354495"
set FECHA="14/07/2025"
set EFECTOR_NOMBRE="ODONTOLOGO DE PRUEBA COCH"
set COLEGIO=3
set EFECTOR_COD_FACT=333

REM ----- ¡LA CLAVE ESTÁ EN ESTA LÍNEA! -----
REM Pon comillas alrededor de cada variable %VARIABLE% que pase un string,
REM especialmente si puede contener espacios o si quieres asegurar que se trate como un solo argumento.
python %SCRIPT_PATH% %CREDENCIAL% %FECHA% %EFECTOR_NOMBRE% %COLEGIO% %EFECTOR_COD_FACT%

pause