; Custom NSIS installer script for Modelling Mate
; This adds auto-uninstall of previous versions and Python dependency installation

; Auto-uninstall previous version before installing
!macro customInit
  ; Check if app is already installed
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{com.imsciences.modellingmate}" "UninstallString"
  ${If} $0 != ""
    ; Previous version found - show message and uninstall
    MessageBox MB_OKCANCEL|MB_ICONINFORMATION \
      "Modelling Mate is already installed. The previous version will be uninstalled automatically before installing the new version.$\r$\n$\r$\nClick OK to continue or Cancel to abort." \
      IDOK uninst
      Abort

    uninst:
      ; Close the app if it's running
      DetailPrint "Checking for running Modelling Mate processes..."

      ; Try to close gracefully first
      ExecWait 'taskkill /IM "Modelling Mate.exe" /T' $1
      ExecWait 'taskkill /IM "modelling-mate-backend.exe" /T' $1
      ExecWait 'taskkill /IM "electron.exe" /T' $1

      ; Wait a moment for processes to close
      Sleep 2000

      ; Force kill if still running
      ExecWait 'taskkill /F /IM "Modelling Mate.exe"' $1
      ExecWait 'taskkill /F /IM "modelling-mate-backend.exe"' $1

      ; Wait for files to be released
      Sleep 1000

      ; Run the uninstaller
      DetailPrint "Uninstalling previous version..."
      ExecWait '$0 /S _?=$INSTDIR' $1

      ; Wait for uninstall to complete
      Sleep 2000

      ; Clean up any remaining files
      RMDir /r "$INSTDIR"

      DetailPrint "Previous version uninstalled successfully"
  ${EndIf}
!macroend

; Custom finish page - removed Python dependency checkbox since we have bundled backend
!macro customFinishPage
  ; Launch application option
  !define MUI_FINISHPAGE_RUN "$INSTDIR\Modelling Mate.exe"
  !define MUI_FINISHPAGE_RUN_TEXT "Launch Modelling Mate"
!macroend

; Custom finish page text
!macro customFinishPageText
  ; Additional information on the finish page
  !define MUI_FINISHPAGE_TITLE "Modelling Mate Installation Complete"
  !define MUI_FINISHPAGE_TEXT "Modelling Mate has been installed successfully with a bundled Python backend.$\r$\n$\r$\nNo additional Python installation is required - all analytics features are ready to use!$\r$\n$\r$\nClick Finish to close this wizard."
!macroend
