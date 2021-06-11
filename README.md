![VidCutter](http://vidcutter.ozmartians.com/vidcutter-banner.png)

[![AUR-GIT](https://img.shields.io/aur/version/vidcutter-git.svg)](https://aur.archlinux.org/packages/vidcutter-git)
[![Build Status](https://travis-ci.org/ozmartian/vidcutter-appimage.svg)](https://github.com/ozmartian/vidcutter-appimage/releases/latest) 
[![Build Status](https://travis-ci.org/ozmartian/vidcutter-osx.svg?branch=master)](https://github.com/ozmartian/vidcutter-osx/releases/latest)
[![Build Status](https://ci.appveyor.com/api/projects/status/jgasythb2vqsxy7v?svg=true)](https://ci.appveyor.com/project/ozmartian/vidcutter/build/artifacts)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/425a00c7c6af446ba87c6152567d9f7e)](https://www.codacy.com/app/ozmartian/vidcutter)

[![Screenshot 1](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-01-thumb.png)](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-01.png) 
[![Screenshot 2](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-02-thumb.png)](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-02.png) 
[![Screenshot 3](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-03-thumb.png)](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-03.png) 
[![Screenshot 4](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-04-thumb.png)](https://cdn.rawgit.com/ozmartian/vidcutter/gh-pages/images/vidcutter-04.png)

### flatpak (Linux)

<a href='https://flathub.org/apps/details/com.ozmartians.VidCutter'><img width='240' alt='Install via Flathub' src='https://flathub.org/assets/badges/flathub-badge-en.png'/></a>

or via the terminal:

```
$ flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  (to enable the flathub repo if not already)
  
$ flatpak install flathub com.ozmartians.VidCutter
$ flatpak run com.ozmartians.VidCutter
```

***

### Arch Linux

Users can install directly from Arch's community repo since VidCutter has been added to Arch's official repos. There is also an AUR development version available.
   
    LATEST STABLE RELEASE:

        sudo pacman -S vidcutter

Using an AUR helper like yay (replace yay with any other AUR helper):

    LATEST DEVELOPMENT RELEASE:
    
        yay -S vidcutter-git

### Ubuntu based (e.g. Mint/Debian/KDE Neon)

Users can install the latest release via:

    ppa:ozmartian/apps

The following set of commands will get you up and running:

    sudo add-apt-repository ppa:ozmartian/apps
    sudo apt update
    sudo apt install vidcutter

### openSUSE

https://software.opensuse.org/package/vidcutter

VidCutter is available from openSUSE Leap 15.0 + Tumbleweed official distributions repos. Community built packages for other openSUSE releases/versions can be found @ https://software.opensuse.org/package/vidcutter. 

VidCutter is also available from the popular Packman third-party repository. Instructions to enable it can be found here:

   https://en.opensuse.org/Additional_package_repositories#Packman

***

### Windows installer

[![Latest Releases](http://tvlinker.ozmartians.com/images/button-latest-release.png)](https://github.com/ozmartian/vidcutter/releases/latest)

#### Chocolatey package

VidCutter has finally been approved + published in the [Chocolatey](https://chocolatey.org) public repository (its a package manager like in Linux but
for Windows).

  To install VidCutter, run the following command from the command line or from PowerShell:
  ```
  C:\> choco install vidcutter
  ```
  To upgrade VidCutter, run the following command from the command line or from PowerShell:
  ```
  C:\> choco upgrade vidcutter
  ```

***

## Command-line for debugging (Linux/macOS only)
  ```
  $ vidcutter --help

Usage: vidcutter [options] [video] [project]

VidCutter - the simplest + fastest video cutter & joiner

Options:
  --debug        debug mode; verbose console output & logging. This will
                 basically output what is being logged to file to the console
                 stdout. Mainly useful for debugging problems with your system
                 video and/or audio stack and codec configuration.
  --dev          developer mode; disables the use of compiled resource files so
                 that all app resources & assets are accessed directly from the
                 file system allowing you to see UI changes immediately. this
                 typically relates to changes made to Qt stylesheets (.qss),
                 layout/templates, content includes and images. basically all
                 assets defined in .qrc files throughout the codebase.
  -v, --version  Displays version information.
  -h, --help     Displays this help.

Arguments:
  video          Preload video file
  project        Open VidCutter project file (.vcp)
  ```
