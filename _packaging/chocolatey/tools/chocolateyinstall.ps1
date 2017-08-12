
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://github.com/ozmartian/vidcutter/releases/download/4.0.0/VidCutter-4.0.0-setup-win32.exe'
$url64      = 'https://github.com/ozmartian/vidcutter/releases/download/4.0.0/VidCutter-4.0.0-setup-win64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  checksum      = 'e63209e2b72bc933399708634fa9109e08bc5099a3c1ef84d573cc4a9ab87e0a'
  checksumType  = 'sha256'
  checksum64    = '846e158c22807389e09f29c7ee48a8db4f341ad5f95fc9d904a096f4ee8b56bc'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
