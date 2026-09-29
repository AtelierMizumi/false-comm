Name:           false-comm
Version:        2.0.0
Release:        1%{?dist}
Summary:        Realistic, stealth Git commit history synthesizer for developers

License:        MIT
URL:            https://github.com/AtelierMizumi/false-comm
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  python3-wheel
BuildRequires:  python3-hatchling
Requires:       git
Requires:       python3 >= 3.12
Requires:       python3-pydantic
Requires:       python3-pyyaml
Requires:       python3-rich
Requires:       python3-typer

%description
false-comm synthesizes organic, statistically natural Git commit histories
using Negative Binomial distributions, realistic intra-day working hours
with jitter, multi-country holiday calendars, and meaningful semantic file diffs.
Includes instant atomic rollback and multi-day commit replay.

%prep
%autosetup

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files false_comm

# Install completions
install -d %{buildroot}%{_datadir}/bash-completion/completions
install -m 0644 packaging/completions/bash %{buildroot}%{_datadir}/bash-completion/completions/false-comm
install -m 0644 packaging/completions/bash %{buildroot}%{_datadir}/bash-completion/completions/fc

install -d %{buildroot}%{_datadir}/zsh/site-functions
install -m 0644 packaging/completions/zsh %{buildroot}%{_datadir}/zsh/site-functions/_false-comm
install -m 0644 packaging/completions/zsh %{buildroot}%{_datadir}/zsh/site-functions/_fc

install -d %{buildroot}%{_datadir}/fish/vendor_completions.d
install -m 0644 packaging/completions/fish %{buildroot}%{_datadir}/fish/vendor_completions.d/false-comm.fish
install -m 0644 packaging/completions/fish %{buildroot}%{_datadir}/fish/vendor_completions.d/fc.fish

# Install man page
install -d %{buildroot}%{_mandir}/man1
install -m 0644 packaging/man/false-comm.1 %{buildroot}%{_mandir}/man1/false-comm.1

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/false-comm
%{_bindir}/fc
%{_datadir}/bash-completion/completions/*
%{_datadir}/zsh/site-functions/*
%{_datadir}/fish/vendor_completions.d/*
%{_mandir}/man1/false-comm.1*

%changelog
* Sun Sep 29 2026 false-comm contributors <thuanc177@gmail.com> - 2.0.0-1
- Initial 2.0.0 release of false-comm
