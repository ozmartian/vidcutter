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
 
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

%description
 Qt5 based GUI for simple cutting and joining of your videos without the need for
 reencoding. VidCutter focuses on getting the job done using the best settings using
 tried and true tech in its arsenal via mpv and FFmpeg.

 NOTE:
 You will need to enable RPMFusion's free repository before installing this package.


%package -n     %{pkg_name}
Summary:        %{summary}
%{?python_provide:%python_provide %{pkg_name}}
 
Requires:       python3-qt5, mpv-libs, mediainfo, ffmpeg, python3-setuptools
%description -n %{pkg_name}
 Qt5 based GUI for simple cutting and joining of your videos without the need for
 reencoding. VidCutter focuses on getting the job done using the best settings using
 tried and true tech in its arsenal via mpv and FFmpeg.

 NOTE:
 You will need to enable RPMFusion's free repository before installing this package.


%prep
%autosetup -n %{pkg_name}-%{version}

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

%changelog
* Sun Mar 05 2017 Pete Alexandrou <pete@ozmartians.com> - 3.0.0-1
- Initial package.
