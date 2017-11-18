
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

  checksum      = 'f572b65c7c03dc439b71cbfa0e3eb5cbbc3c8a945987694980b963dbb50be39e'
  checksumType  = 'sha256'
  checksum64    = 'e8a000161ff205351510097f19003004f2b4410e4c91799cd1911aab8b5853dc'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
