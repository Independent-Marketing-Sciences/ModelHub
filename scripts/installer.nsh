; Custom NSIS installer script for Modelling Mate
; This adds a checkbox to install Python dependencies after installation

!macro customFinishPage
  ; Add checkbox for Python dependency installation
  !define MUI_FINISHPAGE_SHOWREADME
  !define MUI_FINISHPAGE_SHOWREADME_TEXT "Install Python Dependencies (Required for Analytics)"
  !define MUI_FINISHPAGE_SHOWREADME_FUNCTION InstallPythonDependencies
!macroend

; Function to run the Python dependency installer
Function InstallPythonDependencies
  ; Execute the Install-Dependencies.bat script
  ExecShell "open" "$INSTDIR\resources\app.asar.unpacked\scripts\Install-Dependencies.bat"
FunctionEnd

; Custom finish page text
!macro customFinishPageText
  ; Additional information on the finish page
  !define MUI_FINISHPAGE_TITLE "Modelling Mate Installation Complete"
  !define MUI_FINISHPAGE_TEXT "Please install Python dependencies to enable all features.$\r$\n$\r$\nYou can also run the dependency installer later from:$\r$\n$INSTDIR\resources\app.asar.unpacked\scripts\Install-Dependencies.bat"
!macroend
