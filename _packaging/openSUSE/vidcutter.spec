Name:           vidcutter
Version:        4.0.0
Release:        0
Summary:        the simplest + fastest video cutter & joiner
License:        GPL-3.0+
Group:          Productivity/Multimedia/Video/Editors and Convertors
Url:            http://vidcutter.ozmartians.com/
Source0:        https://github.com/ozmartian/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildRequires:  desktop-file-utils
BuildRequires:  hicolor-icon-theme
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  mpv-devel
BuildRequires:  update-desktop-files
Requires:       ffmpeg
Requires:       libmpv1
Requires:       mediainfo
Requires:       python3-qt5
Requires:       python3-opengl
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
The simplest & sexiest tool for cutting and joining your videos without the need for
re-encoding or a diploma in multimedia. VidCutter focuses on getting the job done
using tried and true tech in its arsenal via mpv and FFmpeg.

%prep
%setup -q
sed -i "s/pypi/rpm/" vidcutter/__init__.py

%build
python3 setup.py build

%install
python3 setup.py install --root %{buildroot}

%post
%desktop_database_post
%icon_theme_cache_post

%postun
%desktop_database_postun
%icon_theme_cache_postun

%files
%defattr(-,root,root)
%doc LICENSE README.md
%{_bindir}/%{name}
%{python3_sitelib}/%{name}-%{version}-py*.egg-info/
%{python3_sitelib}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/16x16/apps/%{name}.png
%{_datadir}/icons/hicolor/22x22/apps/%{name}.png
%{_datadir}/icons/hicolor/24x24/apps/%{name}.png
%{_datadir}/icons/hicolor/32x32/apps/%{name}.png
%{_datadir}/icons/hicolor/48x48/apps/%{name}.png
%{_datadir}/icons/hicolor/64x64/apps/%{name}.png
%{_datadir}/icons/hicolor/128x128/apps/%{name}.png
%{_datadir}/icons/hicolor/256x256/apps/%{name}.png
%{_datadir}/icons/hicolor/512x512/apps/%{name}.png
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/mime/packages/x-%{name}.xml
%{_datadir}/pixmaps/%{name}.svg

%changelog
