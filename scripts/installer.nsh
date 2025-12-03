; Custom NSIS installer script for Modelling Mate
; This adds auto-uninstall of previous versions and shows progress

; Auto-uninstall previous version before installing (with progress feedback)
!macro customInit
  ; Check if app is already installed
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{com.imsciences.modellingmate}" "UninstallString"
  ${If} $0 != ""
    ; Previous version found - show message and uninstall
    MessageBox MB_ICONINFORMATION "Updating Modelling Mate...$\r$\n$\r$\nThe installer will now:$\r$\n1. Close any running processes$\r$\n2. Remove the previous version$\r$\n3. Install the new version$\r$\n$\r$\nThis may take 30-60 seconds.$\r$\nPlease wait..." /SD IDOK

    DetailPrint "========================================="
    DetailPrint "UPDATING MODELLING MATE"
    DetailPrint "========================================="
    DetailPrint ""
    DetailPrint "[Step 1/4] Checking for running Modelling Mate processes..."

    ; Try to close gracefully first
    DetailPrint "  • Closing Modelling Mate application..."
    ExecWait 'taskkill /IM "Modelling Mate.exe" /T' $1
    DetailPrint "  • Closing Python backend..."
    ExecWait 'taskkill /IM "modelling-mate-backend.exe" /T' $1
    ExecWait 'taskkill /IM "backend.exe" /T' $1
    ExecWait 'taskkill /IM "python.exe" /T' $1
    DetailPrint "  • Closing Electron processes..."
    ExecWait 'taskkill /IM "electron.exe" /T' $1

    ; Wait a moment for processes to close
    DetailPrint "  • Waiting for processes to terminate..."
    Sleep 3000

    ; Force kill if still running
    DetailPrint "  • Ensuring all processes are closed..."
    ExecWait 'taskkill /F /IM "Modelling Mate.exe"' $1
    ExecWait 'taskkill /F /IM "modelling-mate-backend.exe"' $1
    ExecWait 'taskkill /F /IM "backend.exe"' $1
    ExecWait 'taskkill /F /IM "python.exe"' $1

    ; Wait longer for files to be released
    DetailPrint "  • Waiting for Windows to release file locks..."
    Sleep 3000
    DetailPrint "  ✓ All processes closed successfully"
    DetailPrint ""

    ; Clear application logs before uninstalling
    DetailPrint "[Step 2/4] Clearing application logs..."

    ; Get the user's AppData Local directory where Electron stores userData
    ReadEnvStr $2 LOCALAPPDATA
    ${If} $2 != ""
      Delete "$2\modelling-mate\modelling-mate.log"
      DetailPrint "  • Cleared application logs"
    ${EndIf}
    DetailPrint "  ✓ Logs cleared successfully"
    DetailPrint ""

    ; Run the uninstaller silently
    DetailPrint "[Step 3/4] Uninstalling previous version..."
    DetailPrint "  • Running uninstaller..."
    ExecWait '$0 /S _?=$INSTDIR' $1

    ; Check if uninstall succeeded
    ${If} $1 != 0
      DetailPrint "  ⚠ Warning: Uninstaller returned code $1"
      DetailPrint "  • Attempting manual cleanup..."
    ${Else}
      DetailPrint "  ✓ Uninstaller completed successfully"
    ${EndIf}

    ; Wait for uninstall to complete
    DetailPrint "  • Waiting for cleanup to complete..."
    Sleep 3000

    ; Clean up any remaining files
    DetailPrint "  • Removing old installation files..."
    RMDir /r "$INSTDIR"
    DetailPrint "  • Cleaning temporary files..."
    Delete "$TEMP\modelling-mate-*"
    DetailPrint "  ✓ Cleanup complete"
    DetailPrint ""

    DetailPrint "[Step 4/4] Installing new version..."
    DetailPrint "  • This will take 20-30 seconds..."
    DetailPrint ""
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
