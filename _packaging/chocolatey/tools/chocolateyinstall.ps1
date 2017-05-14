
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://github.com/ozmartian/vidcutter/releases/download/3.2.0/VidCutter-3.2.0-setup-x86.exe'
$url64      = 'https://github.com/ozmartian/vidcutter/releases/download/3.2.0/VidCutter-3.2.0-setup-x64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  checksum      = '82f49f5770fa37fe2450136256560148c36b6b4d56c6945ba0b709f94a2fcbce'
  checksumType  = 'sha256'
  checksum64    = 'fb6f233bb31da7901ce6a663c9f74d1f5abad509d4616502e4e0b6a34deb0f52'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
