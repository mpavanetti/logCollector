@ECHO OFF
@TITLE Talend Python Log Collector Uninstaller
echo by Matheus Pavanetti - 2021
echo Stoping TalendPyLogCollector windows service...
%~dp0installers\nssm.exe stop TalendPyLogCollector
echo.
echo Removing TalendPyLogCollector service...
%~dp0installers\nssm.exe remove TalendPyLogCollector confirm
echo Service has been deleted with success !
echo.
echo Deleting TalendEnv python virtual environment...
rmdir /s /q C:\Python\Environments\TalendEnv\
echo.
echo Please, close this window !
echo.
pause.
