# Created with the help of pyp2rpm-3.2.2
%global pkg_name vidcutter

Name:           %{pkg_name}
Version:        3.0.0
Release:        1%{?dist}
Summary:       the simple & fast video cutter & joiner with the help of mpv + FFmpeg

License:        GPLv3+
URL:            http://vidcutter.ozmartians.com
Source0:       https://github.com/ozmartian/%{pkg_name}/archive/master.tar.gz
BuildArch:      noarch
 
BuildRequires:  python3-devel, python3-setuptools
Requires:          python3-qt5, mpv-libs, mediainfo, ffmpeg

%description
 The simplest & sexiest tool for cutting and joining your videos without the need for
 re-encoding or a diploma in multimedia. VidCutter focuses on getting the job done
 using tried and true tech in its arsenal via mpv and FFmpeg.

 NOTE:
 You will need to enable RPMFusion's free repository before installing this package.

 Dependency list:

    - python3-qt5  (Fedora)
    - python3-setuptools (Fedora)
    - mpv-libs (RPMFusion)
    - ffmpeg (RPMFusion)
    - mediainfo (RPMFusion)

%prep
%autosetup -n %{pkg_name}-master

# Remove bundled egg-info
rm -rf %{pkg_name}.egg-info

# Change packager to prevent PyPi package installation so that we use
# Fedora RPMs as dependencies instead
sed -i "s/pypi/rpm/" vidcutter/__init__.py

%build
%py3_build

%install
%py3_install


%files -n %{pkg_name}
%license vidcutter/LICENSE.html LICENSE
%doc README.md
%{python3_sitelib}/%{pkg_name}
%{python3_sitelib}/%{pkg_name}-%{version}-py?.?.egg-info
%{_bindir}/vidcutter
%{_datadir}/applications/vidcutter.desktop
%{_datadir}/icons/hicolor/128x128/apps/vidcutter.png
%{_datadir}/icons/hicolor/22x22/apps/vidcutter.png
%{_datadir}/icons/hicolor/24x24/apps/vidcutter.png
%{_datadir}/icons/hicolor/256x256/apps/vidcutter.png
%{_datadir}/icons/hicolor/32x32/apps/vidcutter.png
%{_datadir}/icons/hicolor/48x48/apps/vidcutter.png
%{_datadir}/icons/hicolor/512x512/apps/vidcutter.png
%{_datadir}/icons/hicolor/64x64/apps/vidcutter.png
%{_datadir}/icons/hicolor/scalable/apps/vidcutter.svg
%{_datadir}/pixmaps/vidcutter.svg


%changelog
* Sun Mar 05 2017 Pete Alexandrou <pete@ozmartians.com> - 3.0.0-1
- Initial packaging.