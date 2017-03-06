![Build Status](https://travis-ci.org/ozmartian/vidcutter.svg?branch=master)

# VidCutter

<img src="https://raw.githubusercontent.com/ozmartian/vidcutter/master/data/icons/vidcutter.png" width="120" height="120" />

### Windows + macOS Users

Native installers for Windows and macOS are available on the releases page with every new version, or just click the button below. 

<p style="text-align:center;"><a href="https://github.com/ozmartian/vidcutter/releases/latest"><img alt="Latest Release" src="http://tvlinker.ozmartians.com/images/button-latest-release.png" style="max-width:100%;"></a></p>

***

### Linux Users

####Arch Linux

Users can install directly from AUR, package is available in both stable and git-latest versions:

    AUR: vidcutter, vidcutter-git

####Ubuntu/Mint/Debian and all other Ubuntu derivatives 

Users can install the latest release via:

    ppa:ozmartian/apps

If you are new to PPAs then just issue the following commands in a terminal:

    sudo add-apt-repository ppa:ozmartian/apps
    sudo apt-get update
    sudo apt-get install vidcutter

####Fedora

Users can install via the RPM available on the releases page or via my custom copr repository:

    suspiria/VidCutter
    
The commands for a Fedora install via this method are:

    dnf copr enable suspiria/VidCutter
    dnf install vidcutter

####openSUSE

VidCutter is available via the Packman third-party repository. Instructions to enable it can be found here:

   https://en.opensuse.org/Additional_package_repositories#Packman

####AppImage

An AppImage version is also available on the releases page to help all other Linux users.

***

###PyPi

If you're familiar with Python and PyPi then you can always try that option too but avoid installing PyQt5 from through pip and instead run with your distributions own PyQt5 offering. PyQt5 is known as some of the following names under various distros: python-pyqt5, python3-pyqt5, python3-qt5 etc. Using your distro's version ensures a more seamless look & feel with the app integrating with your distro's look & feel + widget sets. Installing all via PyPi will still work, but won't look as nice..

If installing via PyPi, be aware to also ensure you have the following tools also installed via your package manager or any other means it doesn't matter so long as they are installed:

    - libmpv (Arch: mpv, Ubuntu: libmpv1, Fedora: mpv-libs via RPMFusion, openSUSE: libmpv1)
    - FFmpeg (ffmpeg in all places, if on older Linux then you may have libav-tools instead which will also work)
    - mediainfo (mediainfo in all/most places. mainly needs to be the CLI version)

Fedora and RedHat users need to enable the RPMFusion repository in order to access mpv packages and just about anything multimedia-wise. Chances are you know what I'm talking about here but if not here are some simple steps to get VidCutter working in Fedora 25, the same should apply for any other RPM based distro... until I get off my lazy butt and try to learn RPM packaging (oh how horrible it looks though).... if anyone wants to help in this area by all means do!

***

## Fedora Installation Walkthrough

NOTE: a Fedora25 RPM package is now included in release builds so use that. The following remains for reference or troubleshooting.

1. Enable RPMFusion Free repository on your system if not already added. Follow the instructions here for your distro/version

    https://rpmfusion.org/Configuration
    
2. Run 'dnf update' to ensure your system is all up to date.  

3. Install the following packages, PyQt5 is from Fedora base repo and the rest should all come from RPMFusion (Fedora doesn't allow mpv/ffmpeg in their repos due to the free as in beer philosophy. if you dont know what i am talking about, head to www.fsf.org to read up on this stuff if interested)

4. Package list is:

    - python3-qt5
    - mpv-libs
    - ffmpeg
    - mediainfo
    - python3-setuptools

5. Download VidCutter3 source code to temp folder location and install via python setuptools as follows:
    ```
    $ wget https://github.com/ozmartian/vidcutter/archive/master.tar.gz
    
    $ tar zxf master.tar.gz
    
    $ rm master.tar.gz
    
    $ cd vidcutter-master
    
    $ sed -i "s/pypi/rpm/" "vidcutter/__init__.py"
    
    $ sudo python3 setup.py install
    ```
6. That's all folks!

***

## Command-line for debugging (Linux/macOS only)
  ```
  $ vidcutter --help

  Usage: vidcutter [options] [video]
    The simply FAST & ACCURATE video cutter & joiner

  Options:
    --edl <edl file>  Preloads clip index from a previously saved EDL file.
                      NOTE: You must also set the video argument for this to work.
    -d, --debug       Output all info, warnings and errors to the console. This
                      will basically output what is being logged to file to the
                      console stdout. Mainly useful for debugging problems with
                      your system video and/or audio stack and codec
                      configuration.
    -v, --version     Displays version information.
    -h, --help        Displays this help.

  Arguments:
    video             Preloads the video file in app.
  ```
