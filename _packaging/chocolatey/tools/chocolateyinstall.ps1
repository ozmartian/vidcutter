
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url 		= 'https://github.com/ozmartian/vidcutter/releases/download/5.0.0/VidCutter-5.0.0-setup-win32.exe'
$url64 		= 'https://github.com/ozmartian/vidcutter/releases/download/5.0.0/VidCutter-5.0.0-setup-win64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  checksum      = 'd74f7cde2a92e78aa1d075a2a67d800289e51c75ccef50926ecdd6591cc72bc2'
  checksumType  = 'sha256'
  checksum64    = '261ac04b6f5fb6ebaf70a4b8a1ba4cb6e031111228cd79fa9cd4d4cd5885d278'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
