<div style="width:100%; height:120px; position:relative;">
    <div style="float:left; position:absolute; left:10px;">
        <img src="https://travis-ci.org/ozmartian/vidcutter.svg?branch=master" />
        <br/><br/>
        <b>Homepage:</b> <a href="http://vidcutter.ozmartians.com" target="_blank">http://vidcutter.ozmartians.com</a>
    </div>
    <div style="float:right; right:10px; position:absolute;">
        <img src="https://raw.githubusercontent.com/ozmartian/vidcutter/master/data/icons/vidcutter.png" style="width:120px;" />
    </div>
</div>

<hr noshade size="1" />

Cross-platform Qt5 based app for quick and easy video trimming/splitting and merging/joining for simple quick edits.
FFmpeg drives the backend with a stylishly hand edited Qt5 UI. FFmpeg static binary is supplied for Windows installations.
For non-windows, use your o/s package manager if on Linux and homebrew for Mac OS X to manage FFmpeg. It is most likely already installed on your Linux or macOS machine.

----[ Linux Users ]----

Install via PyPi as a last resort only if you are using a Linux distribution that is NOT related to ArchLinux or Ubuntu/Debian.

ArchLinux users can install directly from AUR, package is available in both stable and git-latest versions:

    AUR: vidcutter, vidcutter-git

Ubuntu/Mint/Debian users can install via Launchpad PPA.

    ppa:ozmartian/apps

If you are new to PPAs then just issue the following commands in a terminal:

    sudo add-apt-repository ppa:ozmartian/apps
    sudo apt-get update

You should now be able to search for vidcutter in your chosen package management software (synaptic, Ubuntu software centre, apt-get etc.)


----[ Windows + macOS Users ]----

It is highly recommended that you install using the native installers for Windows and macOS made available at the app's homepage:

    http://vidcutter.ozmartians.com
