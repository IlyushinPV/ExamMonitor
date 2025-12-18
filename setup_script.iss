; --- НАСТРОЙКИ УСТАНОВЩИКА ---
#define MyAppName "Exam Monitor Agent"
#define MyAppVersion "2.0"
#define MyAppPublisher "School Admin"
#define MyAppExeName "ExamMonAgent.exe"

[Setup]
; Уникальный ID приложения. Если уже ставили старую версию — удалите её сначала.
AppId={{A3590506-692B-4417-8857-79F019F02302}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Установка в Program Files (x86)
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
; ВАЖНО: GitHub Actions собирает exe в папку dist.
Source: "dist\ExamMonAgent.exe"; DestDir: "{app}"; Flags: ignoreversion

; Если вы хотите, чтобы файлы иконок лежали рядом с программой (опционально, т.к. мы их вшили внутрь):
; Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Source: "logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
; КЛЮЧЕВОЙ МОМЕНТ: Добавляем флаг --silent для скрытого автозапуска
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"" --silent"; Flags: uninsdeletevalue; Tasks: startup

[Run]
; При завершении установки запускаем программу (БЕЗ флага silent, чтобы админ мог настроить)
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить программу и настроить"; Flags: nowait postinstall skipifsilent
