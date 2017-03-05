# Created by pyp2rpm-3.2.2
%global pypi_name vidcutter
%global srcname vidcutter

Name:           %{srcname}
Version:        3.0.0
Release:        1%{?dist}
Summary:       the simple & fast video cutter & joiner with the help of mpv + FFmpeg

License:        GPLv3+
URL:            http://vidcutter.ozmartians.com
Source0:        https://github.com/ozmartian/%{srcname}/archive/%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python3-devel, python3-setuptools

%description
 the simple & fast video cutter & joiner with the help of mpv + FFmpeg

%package -n     %{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide %{srcname}}
 
Requires:       python3-qt5, mpv-libs, mediainfo, ffmpeg, python3-setuptools
%description -n %{srcname}
 the simple & fast video cutter & joiner with the help of mpv + FFmpeg

%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install


%files -n %{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Sat Mar 04 2017 Pete Alexandrou <pete@ozmartians.com> - 3.0.0-1
- Initial package.