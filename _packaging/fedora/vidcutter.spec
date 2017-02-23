# Created by pyp2rpm-3.2.2
%global pypi_name vidcutter
%global srcname vidcutter

Name:           %{srcname}
Version:        3.0.0
Release:        1%{?dist}
Summary:        FFmpeg based video cutter & joiner with a modern PyQt5 GUI

License:        GPLv3+
URL:            http://vidcutter.ozmartians.com
Source0:        
BuildArch:      noarch
 
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

%description
 FFmpeg based video cutter & joiner with a modern PyQt5 GUI

%package -n     %{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide %{srcname}}
 
Requires:       python3-PyQt5
Requires:       python3-setuptools
%description -n %{srcname}
 FFmpeg based video cutter & joiner with a modern PyQt5 GUI

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
* Fri Feb 10 2017 Pete Alexandrou <pete@ozmartians.com> - 3.0.0-1
- Initial package.