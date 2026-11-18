[Setup]
AppId={{8E2C7B41-5D19-4F3A-9C82-1A7E4B6D9F10}
AppName=Ecco the Dolphin: Defender of the Future
AppVersion=1.0
AppPublisher=DolphinPS2 / cherryduck
DefaultDirName={autopf}\Ecco the Dolphin
DefaultGroupName=Ecco the Dolphin
OutputDir=C:\Users\dolph\Downloads
OutputBaseFilename=Ecco_the_Dolphin_Online_Setup
SetupIconFile=C:\Users\dolph\AppData\Local\Temp\ecco_setup_pkg\ecco.ico
UninstallDisplayIcon={app}\ecco.ico
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "pin_taskbar"; Description: "Закрепить ярлык на Панели задач"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "C:\Users\dolph\AppData\Local\Temp\ecco_setup_pkg\ecco.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\dolph\AppData\Local\Temp\ecco_setup_pkg\tools\extract_paradox_mod.py"; DestDir: "{app}\tools"; Flags: ignoreversion

[Icons]
Name: "{group}\Ecco the Dolphin"; Filename: "{app}\Ecco_the_Dolphin.exe"; IconFilename: "{app}\ecco.ico"; AppUserModelID: "DolphinPS2.EccoDefender.Launcher"
Name: "{group}\Удалить Ecco the Dolphin"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Ecco the Dolphin"; Filename: "{app}\Ecco_the_Dolphin.exe"; IconFilename: "{app}\ecco.ico"; AppUserModelID: "DolphinPS2.EccoDefender.Launcher"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\Ecco the Dolphin"; Filename: "{app}\Ecco_the_Dolphin.exe"; IconFilename: "{app}\ecco.ico"; AppUserModelID: "DolphinPS2.EccoDefender.Launcher"; Tasks: pin_taskbar

[Run]
Filename: "{app}\Ecco_the_Dolphin.exe"; Description: "{cm:LaunchProgram,Ecco the Dolphin}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DiscPage: TInputFileWizardPage;
  DownloadPage: TDownloadWizardPage;

procedure InitializeWizard;
begin
  DiscPage := CreateInputFilePage(wpSelectTasks,
    'Выбор образов дисков Dreamcast',
    'Укажите скачанные образы игры для автоматической установки',
    'Обязателен европейский образ (Europe .chd/.cue/.gdi). Дополнительно можно указать русский образ Paradox RUS (.cdi/.chd/.gdi) — установщик скачает движок с GitHub и сам извлечёт перевод и озвучку.');
  DiscPage.Add('Европейский образ диска (Europe, обязательно):', 'Образы Dreamcast (*.chd;*.cue;*.gdi)|*.chd;*.cue;*.gdi|Все файлы (*.*)|*.*', '.chd');
  DiscPage.Add('Русский образ диска (Paradox RUS, по желанию):', 'Образы Dreamcast (*.cdi;*.chd;*.gdi)|*.cdi;*.chd;*.gdi|Все файлы (*.*)|*.*', '.cdi');
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = DiscPage.ID then begin
    if (DiscPage.Values[0] = '') or (not FileExists(DiscPage.Values[0])) then begin
      MsgBox('Пожалуйста, укажите существующий файл европейского образа диска (Europe).', mbError, MB_OK);
      Result := False;
    end;
  end else if CurPageID = wpReady then begin
    DownloadPage.Clear;
    DownloadPage.Add('https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.0-dc-pc-launcher/Ecco_the_Dolphin_Engine_Win64.zip', 'engine.zip', '');
    DownloadPage.Add('https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.0-dc-pc-launcher/chdman_win64.zip', 'tools.zip', '');
    DownloadPage.Show;
    try
      try
        DownloadPage.Download;
        Result := True;
      except
        if DownloadPage.AbortedByUser then
          Log('Aborted by user.')
        else
          SuppressibleMsgBox(AddPeriod(GetExceptionMessage), mbCriticalError, MB_OK, IDOK);
        Result := False;
      end;
    finally
      DownloadPage.Hide;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EuSrc, RuSrc, EuExt, Cmd: String;
  ResCode: Integer;
begin
  if CurStep = ssPostInstall then begin
    
    Cmd := '/c powershell -NoProfile -Command "Expand-Archive -Path ''' + ExpandConstant('{tmp}\engine.zip') + ''' -DestinationPath ''' + ExpandConstant('{app}') + ''' -Force; Expand-Archive -Path ''' + ExpandConstant('{tmp}\tools.zip') + ''' -DestinationPath ''' + ExpandConstant('{app}\tools') + ''' -Force"';
    Exec(ExpandConstant('{cmd}'), Cmd, '', SW_HIDE, ewWaitUntilTerminated, ResCode);
    EuSrc := DiscPage.Values[0];
    EuExt := ExtractFileExt(EuSrc);
    ForceDirectories(ExpandConstant('{app}\disc'));
    CopyFile(EuSrc, ExpandConstant('{app}\disc\ecco_eu') + EuExt, False);
    RuSrc := DiscPage.Values[1];
    if (RuSrc <> '') and FileExists(RuSrc) then begin
      Cmd := '/c set "PATH=' + ExpandConstant('{app}\tools') + ';%PATH%" && set "PYTHONUTF8=1" && py -3 "' + ExpandConstant('{app}\tools\extract_paradox_mod.py') + '" "' + RuSrc + '" "' + ExpandConstant('{app}\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox') + '"';
      Exec(ExpandConstant('{cmd}'), Cmd, '', SW_HIDE, ewWaitUntilTerminated, ResCode);
    end;
  end;
end;