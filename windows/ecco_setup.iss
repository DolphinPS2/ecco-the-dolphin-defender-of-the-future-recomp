[Setup]
AppName=Ecco the Dolphin: Defender of the Future
AppVersion=1.0
DefaultDirName={autopf}\Ecco the Dolphin
DefaultGroupName=Ecco the Dolphin
OutputDir=dist
OutputBaseFilename=Setup_Ecco_the_Dolphin
SetupIconFile=engine\ecco.ico
UninstallDisplayIcon={app}\Ecco_the_Dolphin.exe
Compression=lzma2/fast
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "Ecco_the_Dolphin_Windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Ecco the Dolphin"; Filename: "{app}\Ecco_the_Dolphin.exe"
Name: "{autodesktop}\Ecco the Dolphin"; Filename: "{app}\Ecco_the_Dolphin.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Ecco_the_Dolphin.exe"; Description: "{cm:LaunchProgram,Ecco the Dolphin}"; Flags: nowait postinstall skipifsilent
