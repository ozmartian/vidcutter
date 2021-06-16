
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
# $url        = 'https://github.com/ozmartian/vidcutter/releases/download/6.0.0/VidCutter-6.0.5.1-setup-win32.exe'
$url64 		  = 'https://ci.appveyor.com/api/buildjobs/6e92yh0mu6yii87v/artifacts/VidCutter-6.0.5.1-setup-win64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  # url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  # checksum      = '570519291defb459b9d9cdd18d195f6730ffd7e281bb9f5d4d90e3a3e7f426c5'
  # checksumType  = 'sha256'
  checksum64    = '5b2ecefaacef42da106187bf09714cc700301810fccfe27f6950f288e9891f40'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
