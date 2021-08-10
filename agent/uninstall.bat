@ECHO OFF
@TITLE Talend Python Log Collector Uninstaller
echo by Matheus Pavanetti - 2021
echo Removing TalendPyLogCollector service...
%~dp0installers\nssm.exe remove TalendPyLogCollector confirm
echo Service has been deleted with success !
echo.
echo Please, close this window !
echo.
pause.
