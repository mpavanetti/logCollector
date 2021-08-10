@ECHO OFF
@TITLE Talend Python Log Collector Installer
echo Installer by Matheus Pavanetti - 2021
echo Starting Python Talend Logs collector Agent installation...
echo at %date%

:MAIN

IF EXIST "C:\Python\Environments\TalendEnv\Scripts\activate.bat" ( GOTO RUN ) ELSE ( GOTO INSTALL ) 

:RUN
  echo Talend Environment Found !
  echo Installing Windows Service...
  %~dp0installers\nssm.exe install TalendPyLogCollector %~dp0\LogCollector.bat [SERVICE_AUTO_START: Automatic]
  echo Starting Windows Service...
  %~dp0installers\nssm.exe start TalendPyLogCollector
  echo.
  echo Installation Finished Please, Close this windows !
  pause
  
GOTO :EOF

:INSTALL
  echo Talend python Environment was not found
  echo checking if python is installed...

  reg query "hkcu\software\Python"

  if ERRORLEVEL 1 GOTO NOPYTHON
  echo Python was found
  echo installping pip3 virtualenv...
  pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org virtualenv
  echo creating virtual env directory...
  mkdir "C:\Python\Environments\"
  echo finding virtual env directory...
  cd "C:\Python\Environments\"
  echo creating TalendEnv...
  py -m venv TalendEnv
  echo Activating TalendEnv...
  CALL C:\Python\Environments\TalendEnv\Scripts\activate.bat
  echo Installing python elasticsearch...
  pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org elasticsearch
  echo Installing python pandas...
  pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pandas
  echo deactivating TalendEnv...
  GOTO :MAIN

  :NOPYTHON
   %~dp0installers\python-3.9.6.exe
   GOTO :MAIN

GOTO :EOF

  


