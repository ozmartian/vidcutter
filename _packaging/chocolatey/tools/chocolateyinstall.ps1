
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://github.com/ozmartian/vidcutter/releases/download/5.5.0/VidCutter-5.5.0-setup-win32.exe'
$url64 		= 'https://github.com/ozmartian/vidcutter/releases/download/5.5.0/VidCutter-5.5.0-setup-win64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  checksum      = '1d6669e57a8c7969abd677ce832ae93271459fb098f3c76d7076124788ed3d6f'
  checksumType  = 'sha256'
  checksum64    = '1a70253ee9deb9c3cd37086328026ac8179e8479c120b5d3de82adc888266677'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
