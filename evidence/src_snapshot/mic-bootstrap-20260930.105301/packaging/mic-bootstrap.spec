%define _build_name_fmt    %%{ARCH}/%%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.vanish.rpm
%define __os_install_post %{nil}
%define nodebug 1

#Apply new change from mic

Name:		mic-bootstrap
VCS:   tools/mic-bootstrap#51f241d86ecc960aaa2d4440d7da82aa45d5dbe5
Version:	1.0
Release:	1
AutoReqProv:    0
Provides:       %{name}
ExclusiveArch:  x86_64 %ix86

Summary:	mic bootstrap
Group:		System/Tools
License:	GPLv2
URL:		http://www.tizen.org/
Source100:      baselibs.conf
Source101:      rpmlintrc

BuildRequires:	rpm
BuildRequires:	gnutar
#BuildRequires:	!rpmlint !rpmlint-min !rpmlint-tizen
BuildRequires:  python3-rpm
BuildRequires:  python3-zypp
BuildRequires:  xmlsec1
BuildRequires:  kmod-compat
BuildRequires:  mic
#BuildRequires:  busybox
BuildRequires:  rpm-security-plugin
BuildRequires:  bmap-tools
BuildRequires:  e2fsprogs
BuildRequires:  kpartx
BuildRequires:  dosfstools
BuildRequires:  parted
BuildRequires:  zip
BuildRequires:  openssl3
BuildRequires:  btrfs-progs
BuildRequires:  squashfs
BuildRequires:  cryptsetup
BuildRequires:  verity-tools
BuildRequires:  f2fs-tools
BuildRequires:  curl
BuildRequires:  python3
BuildRequires:  brotli
BuildRequires:  attr
BuildRequires:  upgrade-tools
BuildRequires:  erofs-utils

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
gnutar -T filestoinclude1 -cpf - | ( cd %buildroot/bootstrap && gnutar -xpf - )
# tar copy /usr/bin and /usr/sbin to /bin and /sbin to fix symblic lost in tar
(cd /usr/bin && gnutar -cpf - *) | (cd %buildroot/bootstrap/bin && gnutar -xpf -)
(cd /usr/sbin && gnutar -cpf - *) | (cd %buildroot/bootstrap/sbin && gnutar -xpf -)
# mic runs plain `tar` inside the bootstrap to pack loop images; force it to
# GNU tar because bsdtar auto-detects holes and writes sparse pax archives
# that lthor cannot flash
ln -sf gnutar %buildroot/bootstrap/bin/tar
ln -sf gnutar %buildroot/bootstrap/usr/bin/tar
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

