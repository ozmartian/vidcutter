%global pkgname com.ozmartians.VidCutter

Name:           vidcutter
Version:        6.0.0
Release:        0
Summary:        the simplest + fastest media cutter & joiner
License:        GPL-3.0+
Url:            https://vidcutter.ozmartians.com
Source0:        https://github.com/ozmartian/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source99:       %{name}-rpmlintrc
BuildRequires:  fdupes
BuildRequires:  hicolor-icon-theme
BuildRequires:  python3-setuptools
%if 0%{?is_opensuse}
BuildRequires:  mpv-devel
BuildRequires:  python3-devel
BuildRequires:  python3-Cython
%if 0%{?suse_version} <= 1320
BuildRequires:  update-desktop-files
BuildRequires:  desktop-file-utils
%endif
%endif
%if 0%{?mageia}
Group:			Video/Editors and Converters
%ifarch x86_64
BuildRequires:	python-pkg-resources
BuildRequires:	lib64raw1394-devel
BuildRequires:	lib64lua-devel
BuildRequires:	lib64mpv-devel
BuildRequires:	lib64python3-devel
BuildRequires:  python3-cython
%else
BuildRequires:	python-pkg-resources
BuildRequires:	libraw1394-devel
BuildRequires:	liblua-devel
BuildRequires:	libmpv-devel
BuildRequires:	libpython3-devel
BuildRequires:  python3-cython
%endif
%else
Group:          Productivity/Multimedia/Video/Editors and Convertors
%endif
Requires:       ffmpeg
Requires:       mediainfo
Requires:       python3-qt5
Requires:       python3-opengl
%if 0%{?is_opensuse}
Requires:		libmpv1
Requires:       python3-typing
%endif
%if 0%{?mageia}
%ifarch x86_64
Requires:		lib64mpv1
Requires:		python3-qt5-core
Requires:		python3-qt5-dbus
Requires:		python3-qt5-gui
Requires:		python3-qt5-network
Requires:		python3-qt5-widgets
Requires:		python3-qt5-x11extras
%else
Requires:		libmpv1
Requires:		python3-qt5-core
Requires:		python3-qt5-dbus
Requires:		python3-qt5-gui
Requires:		python3-qt5-network
Requires:		python3-qt5-widgets
Requires:		python3-qt5-x11extras
%endif
%endif

%description
A modern, simple to use, constantly evolving and hella fast MEDIA CUTTER + JOINER
w/ frame-accurate SmartCut technology + Qt5, libmpv, FFmpeg and MediaInfo powering
the backend.

%prep
%setup -q

%build
python3 setup.py build

%install
python3 setup.py install --root %{buildroot}
%fdupes -s %{buildroot}%{_datadir}

%if 0%{?suse_version} <= 1320
%post
%desktop_database_post
%icon_theme_cache_post

%postun
%desktop_database_postun
%icon_theme_cache_postun
%endif

%files
%defattr(-,root,root)
%doc README.md
%license LICENSE
%if 0%{?suse_version} < 1500
%dir %{_datadir}/metainfo
%endif
%{_bindir}/%{name}
%{python3_sitearch}/%{name}-%{version}-py*.egg-info/
%{python3_sitearch}/%{name}/
%{_datadir}/icons/hicolor/16x16/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/22x22/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/24x24/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/32x32/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/48x48/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/64x64/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/128x128/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/256x256/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/512x512/apps/%{pkgname}.png
%{_datadir}/icons/hicolor/scalable/apps/%{pkgname}.svg
%{_datadir}/applications/%{pkgname}.desktop
%{_datadir}/metainfo/%{pkgname}.appdata.xml
%{_datadir}/mime/packages/%{pkgname}.xml
%{_datadir}/doc/%{name}/
%{_datadir}/doc/%{name}/CHANGELOG
%{_datadir}/doc/%{name}/LICENSE
%{_datadir}/doc/%{name}/README.md


%changelog
