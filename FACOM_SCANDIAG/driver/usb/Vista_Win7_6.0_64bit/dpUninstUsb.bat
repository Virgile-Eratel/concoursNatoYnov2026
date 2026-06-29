@echo off
echo WAIT . . .
DPInst.exe /U FTDIBUS.INF
DPInst.exe /U FTDIPORT.INF
DPInst.exe /U CYUSB.INF
@echo on