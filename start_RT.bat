cls
@ECHO OFF
ECHO. ***********************************
ECHO. ** Starting Jupyter Lab **
ECHO. *******************************

call C:\Users\n10400265\AppData\Local\Continuum\miniconda3\Scripts\activate.bat C:\Users\n10400265\AppData\Local\Continuum\miniconda3
cd C:\Users\n10400265\nf\nf-rtime
call conda activate rt
call jupyter lab

EXIT