# Maintained by app author Pete Alexandrou <pete AT ozmartians DOT com>
# for copr repo build + unitedrpms
%global pkg_name vidcutter

Name:           %{pkg_name}
Version:        5.0.0
Release:        1%{?dist}
Summary:        the simplest + fastest video cutter & joiner
Group:          Applications/Multimedia
License:        GPLv3+
URL:            http://vidcutter.ozmartians.com

Source0:        https://github.com/ozmartian/%{pkg_name}/archive/%{version}.tar.gz
BuildArch:      x86 x86_64
 
BuildRequires:  python3-devel, python3-setuptools, mpv-libs-devel
Requires:       python3-qt5, mpv-libs, mediainfo, ffmpeg, python3-pyopengl

%description
     The simplest & sexiest tool for cutting and joining your videos without the need for
     re-encoding or a diploma in multimedia. VidCutter focuses on getting the job done
     using tried and true tech in its arsenal via mpv and FFmpeg.

%prep
%autosetup -n %{pkg_name}-%{version}

# Remove bundled egg-info
rm -rf %{pkg_name}.egg-info

%build
%define debug_package %{nil}
%py3_build

%install
%py3_install

%files -n %{pkg_name}
%license LICENSE
%doc README.md
%{python3_sitearch}/%{pkg_name}
%{python3_sitearch}/%{pkg_name}-%{version}-py?.?.egg-info
%{_bindir}/%{pkg_name}
%{_datadir}/applications/%{pkg_name}.desktop
%{_datadir}/icons/hicolor/16x16/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/128x128/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/22x22/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/24x24/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/256x256/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/32x32/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/48x48/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/512x512/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/64x64/apps/%{pkg_name}.png
%{_datadir}/icons/hicolor/scalable/apps/%{pkg_name}.svg
%{_datadir}/appdata/%{pkg_name}.appdata.xml
%{_datadir}/mime/packages/x-%{pkg_name}.xml
%{_datadir}/pixmaps/%{pkg_name}.svg

%changelog
* Thu Nov 16 2017 Pete Alexandrou <pete AT ozmartians DOT com> 5.0.0-1
- 5.0.0 release
* Thu Aug 03 2017 Pete Alexandrou <pete AT ozmartians DOT com> 4.0.0-1
- 4.0.0 release
* Mon May 29 2017 Pete Alexandrou <pete AT ozmartians DOT com> 3.5.0-1
- 3.5.0 release
* Tue May 09 2017 Pete Alexandrou <pete AT ozmartians DOT com> 3.2.0-1
- latest release
* Sun Mar 05 2017 Pete Alexandrou <pete AT ozmartians DOT com> - 3.0.1-2
- mageia + epel repos included
* Sun Mar 05 2017 Pete Alexandrou <pete AT ozmartians DOT com> - 3.0.1-1
- version bump
* Sun Mar 05 2017 Pete Alexandrou <pete AT ozmartians DOT com> - 3.0.0-1
- Initial packaging
