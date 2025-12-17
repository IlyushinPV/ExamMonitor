; --- НАСТРОЙКИ УСТАНОВЩИКА ---
#define MyAppName "Exam Monitor Agent"
#define MyAppVersion "2.0"
#define MyAppPublisher "School Admin"
#define MyAppExeName "agent.exe"

[Setup]
AppId={{A3590506-692B-4417-8857-79F019F02302}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=ExamMonitor_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Запускать автоматически при входе в Windows"; GroupDescription: "Автозапуск:"; Flags: checkablealone

[Files]
; GitHub Actions создаст agent.exe в папке dist
Source: "dist\agent.exe"; DestDir: "{app}"; Flags: ignoreversion
; Если есть иконка и логотип в репозитории - раскомментируйте:
; Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить программу"; Flags: nowait postinstall skipifsilent
