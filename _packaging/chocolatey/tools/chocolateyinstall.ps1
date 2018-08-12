
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://github.com/ozmartian/vidcutter/releases/download/6.0.0/VidCutter-6.0.0-setup-win32.exe'
$url64 		  = 'https://github.com/ozmartian/vidcutter/releases/download/6.0.0/VidCutter-6.0.0-setup-win64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  checksum      = '570519291defb459b9d9cdd18d195f6730ffd7e281bb9f5d4d90e3a3e7f426c5'
  checksumType  = 'sha256'
  checksum64    = 'e180a668cd090084d3dba18d64fe12a036e00db58eb9e069cfdfcc13d88d77ce'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
