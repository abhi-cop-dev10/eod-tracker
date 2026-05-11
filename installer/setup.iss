; EOD Tracker — Inno Setup Installer Script
; CodeClouds Internal Tool | Developed by Abhinay Kumar

#define AppName        "EOD Tracker"
#define AppVersion     "1.1.0"
#define AppPublisher   "CodeClouds"
#define AppURL         "https://codeclouds.co"
#define AppExeName     "EODTracker.exe"
#define AppDescription "CodeClouds Internal Tool — Daily EOD Task Tracker"
#define AppDeveloper   "Abhinay Kumar"
#define AppCopyright   "2025-2026 CodeClouds"
#define AppDataDir     "{userappdata}\CodeClouds\EODTracker"

[Setup]
AppId={{F3A7C9B2-1D4E-4A8F-B5C6-2E9D0F3A1B7C}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
AppCopyright={#AppCopyright}
DefaultDirName={autopf}\CodeClouds\EODTracker
DefaultGroupName=CodeClouds\EOD Tracker
DisableProgramGroupPage=no
OutputDir=..\dist\installer
OutputBaseFilename=EODTracker_Setup_v{#AppVersion}
SetupIconFile=..\assets\tray_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
DisableWelcomePage=no
DisableDirPage=no
DisableReadyPage=no
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion} — {#AppPublisher}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppDescription}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}.0
VersionInfoCopyright={#AppCopyright}
VersionInfoTextVersion={#AppVersion}
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
CloseApplicationsFilter=EODTracker.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "Create a &desktop shortcut";                    GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut";               GroupDescription: "Additional shortcuts:"; Flags: unchecked; OnlyBelowVersion: 6.2
Name: "startup";         Description: "Start EOD Tracker &automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\EODTracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*";            DestDir: "{app}\assets";    Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\templates\*";         DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\EOD Tracker";             Filename: "{app}\{#AppExeName}"; Comment: "{#AppDescription}"
Name: "{group}\Uninstall EOD Tracker";   Filename: "{uninstallexe}"
Name: "{autodesktop}\EOD Tracker";       Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; Comment: "{#AppDescription}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\EOD Tracker"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "EODTracker"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch EOD Tracker now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM EODTracker.exe"; Flags: runhidden; RunOnceId: "KillApp"

[Messages]
WelcomeLabel1=Welcome to EOD Tracker {#AppVersion} Setup
WelcomeLabel2=This will install [name/ver] on your computer.%n%nEOD Tracker is a CodeClouds internal tool for tracking daily tasks and exporting a filled Excel EOD report at end of day.%n%nDeveloped by {#AppDeveloper} — CodeClouds Dev Team.%n%nWhat's new in v1.1.0:%n  - Client Bookmarks module (links, files, PDFs, folders per client)%n  - Smart Copy — paste files directly anywhere%n  - Floating button gap fix and white background%n  - All modules disabled by default%n%nClick Next to continue.
FinishedHeadingLabel=EOD Tracker {#AppVersion} is ready!
FinishedLabel=EOD Tracker has been installed on your computer.%n%nThe app runs silently in your system tray. Look for the icon in your taskbar notification area, and click the floating side button on the right edge of your screen to open the task panel.%n%nDeveloped by {#AppDeveloper} — CodeClouds Dev Team.%nVersion {#AppVersion} | {#AppCopyright}

[Code]

// ── Uninstall: ask whether to delete user data ──────────────────────────────

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir  : String;
  NL       : String;
  MsgResult: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    NL      := Chr(13) + Chr(10);
    DataDir := ExpandConstant('{userappdata}\CodeClouds\EODTracker');

    if DirExists(DataDir) then
    begin
      MsgResult := MsgBox(
        'Do you want to permanently delete all EOD Tracker data?' + NL +
        NL +
        'This includes:' + NL +
        '  - All tasks and EOD history' + NL +
        '  - Client bookmarks and saved items' + NL +
        '  - Settings and preferences' + NL +
        '  - Exported Excel reports stored in app data' + NL +
        NL +
        'Location: ' + DataDir + NL +
        NL +
        'Click YES to delete everything (cannot be undone).' + NL +
        'Click NO to keep your data on this computer.',
        mbConfirmation,
        MB_YESNO or MB_DEFBUTTON2
      );

      if MsgResult = IDYES then
      begin
        if not DelTree(DataDir, True, True, True) then
          MsgBox(
            'Some files in ' + DataDir + ' could not be deleted.' + NL +
            'You may remove them manually.',
            mbInformation, MB_OK
          );
      end;
    end;
  end;
end;

// ── Install: remove old autostart reg key if task not selected ───────────────

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    if not WizardIsTaskSelected('startup') then
      RegDeleteValue(
        HKCU,
        'Software\Microsoft\Windows\CurrentVersion\Run',
        'EODTracker'
      );
  end;
end;
