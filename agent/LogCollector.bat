@ECHO OFF
@TITLE Talend Log Collector

@ECHO Welcome to Python Talend Log Collector
@ECHO Version 0.1.0 - Matheus Pavanetti (matheuspavanetti@gmail.com)

:MAIN
echo Checking if exists TalendEnv Python Virtual Environment...

IF EXIST "C:\Python\Environments\TalendEnv\Scripts\activate.bat" ( GOTO RUN ) ELSE ( GOTO INSTALL ) 

:RUN
echo TalendEnv found, activating environment...
CALL C:\Python\Environments\TalendEnv\Scripts\activate.bat
GOTO AGENT

:INSTALL
echo TalendEnv was not found, attempting to run install_agent.bat
CALL %~dp0install_agent.bat
GOTO MAIN

:AGENT
echo Starting Talend Log Collector python script...
py %~dp0\scripts\ETL_TalendReLogs.py
