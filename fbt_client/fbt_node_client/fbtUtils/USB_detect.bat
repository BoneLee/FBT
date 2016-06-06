@echo off
for %%d in (D: E: F: G: H: I: etc...) do (
   if exist %%d\nul (
      echo USB at drive %%d connected
   )
)