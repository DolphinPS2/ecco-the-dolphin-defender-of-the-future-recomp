[Setup]
AppId={{8E2C7B41-5D19-4F3A-9C82-1A7E4B6D9F10}
AppName=Ecco the Dolphin: Defender of the Future
AppVersion=1.4
AppPublisher=DolphinPS2 / cherryduck
DefaultDirName={autopf}\Ecco the Dolphin
DefaultGroupName=Ecco the Dolphin
OutputDir=C:\Users\dolph\Downloads\Engine
OutputBaseFilename=Ecco_the_Dolphin_Online_Setup_v14
SetupIconFile=C:\Users\dolph\Downloads\Engine\setup_build\ecco.ico
WizardSmallImageFile=C:\Users\dolph\Downloads\Engine\setup_build\wizard_small.bmp
UninstallDisplayIcon={app}\ecco.ico
ExtraDiskSpaceRequired=209715200
DirExistsWarning=auto
WizardSizePercent=115
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UsePreviousPrivileges=no
UsePreviousAppDir=no
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
Source: "C:\Users\dolph\Downloads\Engine\setup_build\ecco.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\dolph\Downloads\Engine\setup_build\sun_fall.mp3"; DestDir: "{tmp}"; Flags: dontcopy
Source: "C:\Users\dolph\Downloads\Engine\setup_build\sonic.bmp"; DestDir: "{tmp}"; Flags: dontcopy
Source: "C:\Users\dolph\Downloads\Engine\setup_build\textecco.bmp"; DestDir: "{tmp}"; Flags: dontcopy

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
  MusicBtn: TNewButton;
  SonicImg, LogoImg: TBitmapImage;
  MusicPlaying, NeedVcRedist, UseLocalEngine: Boolean;
  LocalEnginePath: String;

function mciSendString(lpszCommand: String; lpszReturnString: String; cchReturn: Cardinal; hwndCallback: HWND): Cardinal;
  external 'mciSendStringW@winmm.dll stdcall';

procedure ToggleMusic(Sender: TObject);
begin
  if MusicPlaying then begin
    mciSendString('pause bgm', '', 0, 0);
    MusicPlaying := False;
    MusicBtn.Caption := 'Музыка: ВЫКЛ';
  end else begin
    mciSendString('play bgm repeat', '', 0, 0);
    MusicPlaying := True;
    MusicBtn.Caption := 'Музыка: ВКЛ';
  end;
end;

procedure InitializeWizard;
var
  Mp3Path: String;
begin
  ExtractTemporaryFile('sun_fall.mp3');
  ExtractTemporaryFile('sonic.bmp');
  ExtractTemporaryFile('textecco.bmp');
  Mp3Path := ExpandConstant('{tmp}\sun_fall.mp3');

  mciSendString('open "' + Mp3Path + '" type mpegvideo alias bgm', '', 0, 0);
  mciSendString('play bgm repeat', '', 0, 0);
  MusicPlaying := True;

  MusicBtn := TNewButton.Create(WizardForm);
  MusicBtn.Parent := WizardForm;
  MusicBtn.Left := ScaleX(16);
  MusicBtn.Top := WizardForm.CancelButton.Top;
  MusicBtn.Width := ScaleX(115);
  MusicBtn.Height := WizardForm.CancelButton.Height;
  MusicBtn.Caption := 'Музыка: ВКЛ';
  MusicBtn.OnClick := @ToggleMusic;

  SonicImg := TBitmapImage.Create(WizardForm);
  SonicImg.Parent := WizardForm.SelectDirPage;
  SonicImg.Width := ScaleX(118);
  SonicImg.Height := ScaleY(150);
  SonicImg.Left := (WizardForm.SelectDirPage.Width - SonicImg.Width) div 2;
  SonicImg.Top := WizardForm.SelectDirPage.Height - SonicImg.Height - ScaleY(12);
  SonicImg.Stretch := True;
  SonicImg.ReplaceColor := clWhite;
  SonicImg.ReplaceWithColor := WizardForm.InnerPage.Color;
  SonicImg.Bitmap.LoadFromFile(ExpandConstant('{tmp}\sonic.bmp'));
  SonicImg.SendToBack;
  WizardForm.DiskSpaceLabel.BringToFront;

  LogoImg := TBitmapImage.Create(WizardForm);
  LogoImg.Parent := WizardForm.SelectProgramGroupPage;
  LogoImg.Width := ScaleX(249);
  LogoImg.Height := ScaleY(115);
  LogoImg.Left := (WizardForm.SelectProgramGroupPage.Width - LogoImg.Width) div 2;
  LogoImg.Top := WizardForm.SelectProgramGroupPage.Height - LogoImg.Height - ScaleY(8);
  LogoImg.Stretch := True;
  LogoImg.ReplaceColor := clWhite;
  LogoImg.ReplaceWithColor := WizardForm.InnerPage.Color;
  LogoImg.Bitmap.LoadFromFile(ExpandConstant('{tmp}\textecco.bmp'));
  LogoImg.Visible := False;

  DiscPage := CreateInputFilePage(wpSelectTasks,
    'Выбор образов дисков Dreamcast',
    'Укажите скачанные образы игры для автоматической установки',
    'Обязателен европейский образ (Europe .chd/.cue/.gdi). Дополнительно можно указать русский образ Paradox RUS (.cdi/.chd/.gdi) — установщик сам подключит движок с современным меню и извлечёт перевод с озвучкой.');
  DiscPage.Add('Европейский образ диска (Europe, обязательно):', 'Образы Dreamcast (*.chd;*.cue;*.gdi)|*.chd;*.cue;*.gdi|Все файлы (*.*)|*.*', '.chd');
  DiscPage.Add('Русский образ диска (Paradox RUS, по желанию):', 'Образы Dreamcast (*.cdi;*.chd;*.gdi)|*.cdi;*.chd;*.gdi|Все файлы (*.*)|*.*', '.cdi');
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectDir then begin
    SonicImg.Parent := WizardForm.SelectDirPage;
    SonicImg.Visible := True;
    SonicImg.SendToBack;
    WizardForm.DiskSpaceLabel.BringToFront;
    LogoImg.Visible := False;
  end else if CurPageID = wpSelectProgramGroup then begin
    SonicImg.Parent := WizardForm.SelectProgramGroupPage;
    SonicImg.Visible := True;
    LogoImg.Visible := False;
  end else if CurPageID = wpSelectTasks then begin
    SonicImg.Visible := False;
    LogoImg.Parent := WizardForm.SelectTasksPage;
    LogoImg.Visible := True;
  end else if CurPageID = DiscPage.ID then begin
    SonicImg.Visible := False;
    LogoImg.Parent := DiscPage.Surface;
    LogoImg.Visible := True;
  end else begin
    SonicImg.Visible := False;
    LogoImg.Visible := False;
  end;
end;

procedure DeinitializeSetup;
begin
  mciSendString('close bgm', '', 0, 0);
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
    NeedVcRedist := not FileExists(ExpandConstant('{sys}\vcruntime140_1.dll'));
    LocalEnginePath := AddBackslash(ExtractFilePath(ExpandConstant('{srcexe}'))) + 'Ecco_the_Dolphin_Engine_Win64_v14.zip';
    UseLocalEngine := FileExists(LocalEnginePath);

    if (not UseLocalEngine) or NeedVcRedist then begin
      DownloadPage.Clear;
      if not UseLocalEngine then
        DownloadPage.Add('https://github.com/DolphinPS2/ecco-the-dolphin-defender-of-the-future-recomp/releases/download/v1.4/Ecco_the_Dolphin_Engine_Win64.zip', 'engine.zip', '');
      if NeedVcRedist then
        DownloadPage.Add('https://aka.ms/vs/17/release/vc_redist.x64.exe', 'vc_redist.x64.exe', '');
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
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EuSrc, RuSrc, EuExt, EngineZip, Cmd: String;
  ResCode: Integer;
begin
  if CurStep = ssPostInstall then begin
    if NeedVcRedist and FileExists(ExpandConstant('{tmp}\vc_redist.x64.exe')) then
      Exec(ExpandConstant('{tmp}\vc_redist.x64.exe'), '/install /passive /norestart', '', SW_SHOW, ewWaitUntilTerminated, ResCode);
    if UseLocalEngine then
      EngineZip := LocalEnginePath
    else
      EngineZip := ExpandConstant('{tmp}\engine.zip');
    Cmd := '-xf "' + EngineZip + '" -C "' + ExpandConstant('{app}') + '"';
    Exec('tar.exe', Cmd, '', SW_HIDE, ewWaitUntilTerminated, ResCode);
    EuSrc := DiscPage.Values[0];
    EuExt := ExtractFileExt(EuSrc);
    ForceDirectories(ExpandConstant('{app}\disc'));
    CopyFile(EuSrc, ExpandConstant('{app}\disc\ecco_eu') + EuExt, False);
    RuSrc := DiscPage.Values[1];
    if (RuSrc <> '') and FileExists(RuSrc) then begin
      ForceDirectories(ExpandConstant('{app}\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox'));
      Cmd := '/c set "PATH=' + ExpandConstant('{app}\tools') + ';%PATH%" && "' + ExpandConstant('{app}\tools\extract_paradox_mod.exe') + '" "' + RuSrc + '" "' + ExpandConstant('{app}\profiles\paradox_rus\dreamcomp\ecco\mods\rus_paradox') + '"';
      Exec(ExpandConstant('{cmd}'), Cmd, '', SW_HIDE, ewWaitUntilTerminated, ResCode);
    end;
  end;
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  if CurPageID = wpInstalling then begin
    DeleteFile(ExpandConstant('{autodesktop}\Ecco the Dolphin.lnk'));
    DeleteFile(ExpandConstant('{userappdata}\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\Ecco the Dolphin.lnk'));
    DelTree(ExpandConstant('{group}'), True, True, True);
    DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;
