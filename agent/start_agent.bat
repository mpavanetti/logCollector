@ECHO OFF
@TITLE Talend Python Log Collector Service Start
echo by Matheus Pavanetti - 2021
echo Starting TalendPyLogCollector service...
%~dp0installers\nssm.exe start TalendPyLogCollector
echo Service has been started with success !
echo.
echo Please, close this window !
echo.
pause.
