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
  "%~dp0installers\nssm.exe" install TalendPyLogCollector "%~dp0LogCollector.bat"
  "%~dp0installers\nssm.exe" set TalendPyLogCollector Start SERVICE_AUTO_START
  echo Starting Windows Service...
  "%~dp0installers\nssm.exe" start TalendPyLogCollector
  echo.
  echo Installation Finished Please, Close this windows !
  pause
  
GOTO :EOF

:INSTALL
  echo Talend python Environment was not found
  echo checking if python is installed...

  REM The py launcher is what creates the environment, whether Python is installed per user or for all users
  py --version

  if ERRORLEVEL 1 GOTO NOPYTHON
  echo Python was found
  echo creating virtual env directory...
  mkdir "C:\Python\Environments\"
  echo finding virtual env directory...
  REM /d: the agent may sit on another drive than C:
  cd /d "C:\Python\Environments\"
  echo creating TalendEnv...
  py -m venv TalendEnv
  echo Activating TalendEnv...
  CALL C:\Python\Environments\TalendEnv\Scripts\activate.bat
  REM pip verifies PyPI's certificates. Behind a TLS-inspecting proxy, point it at that proxy's CA:
  REM   pip config set global.cert C:\path\to\proxy-ca.pem
  echo Installing python elasticsearch...
  REM The 7.x client, as the agent and the Kibana objects are written for Elasticsearch 7
  pip3 install "elasticsearch<8"
  echo Installing python pandas...
  pip3 install pandas pytz
  echo deactivating TalendEnv...
  GOTO :MAIN

  :NOPYTHON
   %~dp0installers\python-3.9.6.exe
   GOTO :MAIN

GOTO :EOF

  


