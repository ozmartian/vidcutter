
$ErrorActionPreference = 'Stop';

$packageName= 'vidcutter'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://github.com/ozmartian/vidcutter/releases/download/3.5.0/VidCutter-3.5.0-setup-win32.exe'
$url64      = 'https://github.com/ozmartian/vidcutter/releases/download/3.5.0/VidCutter-3.5.0-setup-win64.exe'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url           = $url
  url64bit      = $url64

  softwareName  = 'VidCutter'

  checksum      = 'c080b31dd06952a55104cfdaf39ec314844c6529b068d0d4fadee37d5b953818'
  checksumType  = 'sha256'
  checksum64    = '74c96e6fb10a42af9e1264db6d3d5a630b30ef2652ede37eabef81d6bd249ef5'
  checksumType64= 'sha256'

  silentArgs    = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
