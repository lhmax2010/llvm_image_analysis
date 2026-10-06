%define _build_name_fmt    %%{ARCH}/%%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.vanish.rpm
%define __os_install_post %{nil}
%define nodebug 1

Name:		mic-bootstrap
Version:	1.0
Release:	1
AutoReqProv:    0
Provides:       %{name}
ExclusiveArch:  i586

Summary:	mic bootstrap
Group:		System/Tools
License:	GPLv2
URL:		http://www.tizen.org/
Source100:      baselibs.conf

BuildRequires:	rpm
BuildRequires:  rpm-python
BuildRequires:  util-linux
BuildRequires:  coreutils
BuildRequires:  python-xml
BuildRequires:  python-zypp
BuildRequires:  kmod
BuildRequires:  psmisc
BuildRequires:  grep
BuildRequires:  lsof
BuildRequires:  mic
#BuildRequires:  busybox
BuildRequires:  syslinux
BuildRequires:  syslinux-extlinux
#BuildRequires:  rpm-security-plugin

%description
used for mic bootstrap, this package will be repackaged for i586 and arm libs.
it provides a x86 bootstrap environment for unified usage, especially to speed
up the performance of arm image creation.

%prep

%build

%install
%if %nodebug
set +x
%endif

mkdir -p %buildroot
mkdir -p %buildroot/bootstrap
rpm -qla > filestoinclude1

# ignore files - construct sed script
sedtmp="sedtmp.$$"
echo "s#^%{_docdir}.*##" >> $sedtmp
echo "s#^%{_mandir}.*##" >> $sedtmp
echo "s#^%{_infodir}.*##" >> $sedtmp
# ignore pyc and pyo
echo "s#^.*\.pyc\$##" >> $sedtmp
echo "s#^.*\.pyo\$##" >> $sedtmp

# ignore default filesystem files
for i in `rpm -ql filesystem`; do
  echo "s#^${i}\$##" >> $sedtmp
done

#finish up
echo "/^\$/d" >> $sedtmp

#execute
sed -f $sedtmp -i filestoinclude1

# tar copy to bootstrap dir under buildroot
# prefix /bootstrap will fix conflicts
tar -T filestoinclude1 -cpf - | ( cd %buildroot/bootstrap && tar -xpf - )
rm filestoinclude1

# Todo: refractor
# no directories, in filelist
find %buildroot >  filestoinclude2
cat filestoinclude2 | sed -e "s#%{buildroot}##g" | uniq | sort > filestoinclude1
for i in `cat filestoinclude1`; do
# no directories
  if test -h %buildroot/$i || ! test -d %buildroot/$i; then
    #
    echo "$i" >> filestoinclude
  fi
done
rm filestoinclude1
rm filestoinclude2

set -x

%clean
rm -rf $RPM_BUILD_ROOT

%files -f filestoinclude

