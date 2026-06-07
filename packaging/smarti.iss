#define MyAppName "SmartiAI"
#define MyAppPublisher "SmartiAI"
#define MyAppExeName "SmartiAI.exe"

#ifndef MyAppVersion
#define MyAppVersion "dev"
#endif

#ifndef SourceDir
#define SourceDir "..\dist\SmartiAI"
#endif

#ifndef OutputDir
#define OutputDir "..\release"
#endif

#ifndef IconFile
#define IconFile "..\assets\smarti.ico"
#endif

[Setup]
AppId={{2F7748B6-3D46-4E9C-B187-0F5C2E9F38E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\SmartiAI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=SmartiAI-Agent-for-Windows-{#MyAppVersion}-Setup
SetupIconFile={#IconFile}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
AppMutex=SmartiAI-Agent-for-Windows
CloseApplications=yes
RestartApplications=no
UsePreviousTasks=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: files; Name: "{autoprograms}\SmartiAI Agent for Windows.lnk"
Type: files; Name: "{userdesktop}\SmartiAI Agent for Windows.lnk"; Tasks: desktopicon
Type: files; Name: "{commondesktop}\SmartiAI Agent for Windows.lnk"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\AppUserModelId\SmartiAI"; ValueType: string; ValueName: "DisplayName"; ValueData: "SmartiAI"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\AppUserModelId\SmartiAI"; ValueType: string; ValueName: "IconUri"; ValueData: "{app}\_internal\assets\smarti.ico"; Flags: uninsdeletekey

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM {#MyAppExeName} /T /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
