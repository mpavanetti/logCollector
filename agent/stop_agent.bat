@ECHO OFF
@TITLE Talend Python Log Collector Service Stop
echo by Matheus Pavanetti - 2021
echo Stopping TalendPyLogCollector service...
%~dp0installers\nssm.exe stop TalendPyLogCollector
echo Service has been stopped with success !
echo.
echo Please, close this window !
echo.
pause.
