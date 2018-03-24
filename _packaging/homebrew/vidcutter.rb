cask 'vidcutter' do
  version '5.5.0'
  sha256 '66ec76e878ccf70a7ebadda94f4b599426201cc3b30b52c42d84c4a7142e6f1b'

  # github.com/ozmartian/vidcutter was verified as official when first introduced to the cask
  url 'https://github.com/ozmartian/vidcutter/releases/download/#{version}/VidCutter-#{version}-macOS.dmg'
  appcast 'https://github.com/ozmartian/vidcutter/releases.atom',
          checkpoint: '249e31bf274b71943c530f7d8da4a069c8d82ac56141a583fd48f3d1aa17d092'
  name 'VidCutter'
  homepage 'https://vidcutter.ozmartians.com'

  app 'VidCutter.app'
end
