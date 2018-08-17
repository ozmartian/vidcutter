cask 'vidcutter' do
  version '6.0.0'
  sha256 '33943d56de307b026554824bc9b06779428bd75e5197779897ee2b4952313961'

  # github.com/ozmartian/vidcutter was verified as official when first introduced to the cask
  url 'https://github.com/ozmartian/vidcutter/releases/download/#{version}/VidCutter-#{version}-macOS.dmg'
  appcast 'https://github.com/ozmartian/vidcutter/releases.atom',
          checkpoint: '249e31bf274b71943c530f7d8da4a069c8d82ac56141a583fd48f3d1aa17d092'
  name 'VidCutter'
  homepage 'https://vidcutter.ozmartians.com'

  app 'VidCutter.app'
end
