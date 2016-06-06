ver | find /i "6.3." > NUL
if %errorlevel% equ 0 (goto win8)

ver | find /i "6.2." > NUL
if %errorlevel% equ 0 (goto win8)

ver | find /i "6.1." > NUL  
if %errorlevel% equ 0 (goto win7)  
  
ver | find /i "5.1."  > NUL  
if %errorlevel% equ 0 (goto winXP)

:winXP
netsh firewall add allowedprogram mode=ENABLE profile=ALL name=fbt program=%1
netsh firewall add allowedprogram mode=ENABLE profile=ALL name=stun program=%3
goto end 

:win8
:win7
netsh advfirewall firewall add rule action=allow profile=any protocol=any enable=yes direction=in name=fbt_in program=%1
netsh advfirewall firewall add rule action=allow profile=any protocol=any enable=yes direction=out name=fbt_out program=%1
netsh advfirewall firewall add rule action=allow profile=any protocol=any enable=yes direction=in name=stun_in program=%2
netsh advfirewall firewall add rule action=allow profile=any protocol=any enable=yes direction=out name=stun_out program=%2
:end