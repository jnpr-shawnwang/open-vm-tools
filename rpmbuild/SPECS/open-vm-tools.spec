################################################################################
### Copyright 2013-15 VMware, Inc.  All rights reserved.
###
### RPM SPEC file for building open-vm-tools packages.
###
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of version 2 of the GNU General Public License as
### published by the Free Software Foundation.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
################################################################################

%global _hardened_build 1
%global majorversion    10.0
%global minorversion    5
%global toolsbuild      3227872
%global toolsversion    %{majorversion}.%{minorversion}
%global toolsdaemon     vmtoolsd
#%global vgauthdaemon    vgauthd

Name:             open-vm-tools
Version:          %{toolsversion}
Release:          jmp%{?dist}
Summary:          Open Virtual Machine Tools for virtual machines hosted on VMware
Group:            Applications/System
License:          GPLv2
URL:              http://%{name}.sourceforge.net/
Source0:          http://sourceforge.net/projects/%{name}/files/%{name}/stable-%{majorversion}.x/%{name}-%{version}-%{toolsbuild}.tar.gz
#Source1:          %{toolsdaemon}.service
#Source2:          %{vgauthdaemon}.service
%if 0%{?rhel} >= 6
ExclusiveArch:    x86_64
%else
ExclusiveArch:    %{ix86} x86_64
%endif

BuildRequires:          autoconf
BuildRequires:          automake
BuildRequires:          libtool
BuildRequires:          gcc-c++
BuildRequires:          doxygen
# Fuse is optional and enables vmblock-fuse
BuildRequires:          fuse-devel
BuildRequires:          glib2-devel >= 2.14.0
BuildRequires:          gtk2-devel >= 2.4.0
BuildRequires:          gtkmm24-devel
BuildRequires:          libdnet-devel
BuildRequires:          libicu-devel
BuildRequires:          libmspack-devel
BuildRequires:          libX11-devel
BuildRequires:          libXext-devel
BuildRequires:          libXi-devel
BuildRequires:          libXinerama-devel
BuildRequires:          libXrandr-devel
BuildRequires:          libXrender-devel
BuildRequires:          libXtst-devel
BuildRequires:          openssl-devel
BuildRequires:          pam-devel
BuildRequires:          procps-devel
#BuildRequires:          systemd
BuildRequires:          xerces-c-devel
#BuildRequires:          xml-security-c-devel

Requires:               initscripts
Requires:               coreutils
Requires:               net-tools
Requires:               grep
Requires:               sed
#Requires:               systemd
Requires:               tar
Requires:               which

%description
The %{name} project is an open source implementation of VMware Tools. It
is a suite of open source virtualization utilities and drivers to improve the
functionality, user experience and administration of VMware virtual machines.
This package contains only the core user-space programs and libraries of
%{name}.

%package          desktop
Summary:          User experience components for Open Virtual Machine Tools
Group:            System Environment/Libraries
Requires:         %{name}%{?_isa} = %{version}-%{release}

%description      desktop
This package contains only the user-space programs and libraries of
%{name} that are essential for improved user experience of VMware virtual
machines.

%package          devel
Summary:          Development libraries for Open Virtual Machine Tools
Group:            Development/Libraries
Requires:         %{name}%{?_isa} = %{version}-%{release}

%description      devel
This package contains only the user-space programs and libraries of
%{name} that are essential for developing customized applications for
VMware virtual machines.

%prep
%setup -q -n %{name}-%{version}-%{toolsbuild}

%build
# Use _DEFAULT_SOURCE to suppress warning until upstream
# is fixed. Refer https://sourceware.org/bugzilla/show_bug.cgi?id=16632.
export CFLAGS="$RPM_OPT_FLAGS -D_DEFAULT_SOURCE"
export CXXLAGS="$RPM_OPT_FLAGS -D_DEFAULT_SOURCE"
# Required for regenerating configure script when
# configure.ac get modified
autoreconf -i

# configure from open-vm-tools 10.0.5 is missing 'x' bit
chmod a+x configure
%configure \
    --without-kernel-modules \
    --disable-static \
    --enable-deploypkg \
    --without-xmlsecurity
sed -i -e 's! -shared ! -Wl,--as-needed\0!g' libtool
make %{?_smp_mflags}

%install
export DONT_STRIP=1
make install DESTDIR=%{buildroot}

# Remove exec bit from config files
chmod a-x %{buildroot}%{_sysconfdir}/pam.d/*
chmod a-x %{buildroot}%{_sysconfdir}/vmware-tools/*.conf
#chmod a-x %{buildroot}%{_sysconfdir}/vmware-tools/vgauth/schemas/*

# Remove the DOS line endings
sed -i "s|\r||g" README

# Remove "Encoding" key from the "Desktop Entry"
sed -i "s|^Encoding.*$||g" %{buildroot}%{_sysconfdir}/xdg/autostart/vmware-user.desktop

# Remove unnecessary files from packaging
find %{buildroot}%{_libdir} -name '*.la' -delete
rm -fr %{buildroot}%{_defaultdocdir}
rm -f docs/api/build/html/FreeSans.ttf

# Move vm-support to /usr/bin
mv %{buildroot}%{_sysconfdir}/vmware-tools/vm-support %{buildroot}%{_bindir}

# Systemd unit files
#install -p -m 644 -D %{SOURCE1} %{buildroot}%{_unitdir}/%{toolsdaemon}.service
#install -p -m 644 -D %{SOURCE2} %{buildroot}%{_unitdir}/%{vgauthdaemon}.service

# 'make check' in open-vm-tools rebuilds docs and ends up regenerating
# the font file. We can add %%check secion once 'make check' is fixed
# upstream

%post
if [ -e %{_bindir}/vmware-guestproxycerttool ]; then
   mkdir -p %{_sysconfdir}/vmware-tools/GuestProxyData/server
   mkdir -p -m 0700 %{_sysconfdir}/vmware-tools/GuestProxyData/trusted
   %{_bindir}/vmware-guestproxycerttool -g &> /dev/null || /bin/true
fi
/sbin/ldconfig
#%systemd_post %{vgauthdaemon}.service
#%systemd_post %{toolsdaemon}.service

%preun
#%systemd_preun %{toolsdaemon}.service
#%systemd_preun %{vgauthdaemon}.service

# Tell VMware that open-vm-tools is being uninstalled
if [ "$1" = "0" -a                      \
     -e %{_bindir}/vmware-checkvm -a    \
     -e %{_bindir}/vmware-rpctool ] &&  \
     %{_bindir}/vmware-checkvm &> /dev/null; then
   %{_bindir}/vmware-rpctool 'tools.set.version 0' &> /dev/null || /bin/true
fi

%postun
/sbin/ldconfig
#%systemd_postun_with_restart %{toolsdaemon}.service
#%systemd_postun_with_restart %{vgauthdaemon}.service
# Cleanup GuestProxy certs if open-vm-tools is being uninstalled
if [ "$1" = "0" ]; then                  \
   rm -rf %{_sysconfdir}/vmware-tools/GuestProxyData &> /dev/null || /bin/true
fi

%post devel -p /sbin/ldconfig

%postun devel -p /sbin/ldconfig

%files
%doc AUTHORS ChangeLog COPYING NEWS README
%config(noreplace) %{_sysconfdir}/pam.d/*
%{_sysconfdir}/vmware-tools/
%config(noreplace) %{_sysconfdir}/vmware-tools/*.conf
#%config %{_sysconfdir}/vmware-tools/vgauth/schemas/*
#%{_bindir}/VGAuthService
%{_bindir}/vmhgfs-fuse
%{_bindir}/vm-support
%{_bindir}/vmtoolsd
%{_bindir}/vmware-checkvm
%{_bindir}/vmware-guestproxycerttool
%{_bindir}/vmware-hgfsclient
%{_bindir}/vmware-rpctool
%{_bindir}/vmware-toolbox-cmd
#%{_bindir}/vmware-vgauth-cmd
%{_bindir}/vmware-xferlogs
%{_libdir}/libDeployPkg.so.*
%{_libdir}/libguestlib.so.*
%{_libdir}/libhgfs.so.*
#%{_libdir}/libvgauth.so.*
%{_libdir}/libvmtools.so.*
%dir %{_libdir}/%{name}/
%dir %{_libdir}/%{name}/plugins
%dir %{_libdir}/%{name}/plugins/common
%{_libdir}/%{name}/plugins/common/*.so
%dir %{_libdir}/%{name}/plugins/vmsvc
%{_libdir}/%{name}/plugins/vmsvc/*.so
%exclude %{_sbindir}/mount.vmhgfs
%{_datadir}/%{name}/
%exclude /sbin/
#%{_unitdir}/%{toolsdaemon}.service
#%{_unitdir}/%{vgauthdaemon}.service

%files desktop
%{_sysconfdir}/xdg/autostart/*.desktop
%{_bindir}/vmware-user-suid-wrapper
%{_bindir}/vmware-vmblock-fuse
%{_libdir}/%{name}/plugins/vmusr/

%files devel
%doc docs/api/build/*
%exclude %{_includedir}/libDeployPkg/
%{_includedir}/vmGuestLib/
%{_libdir}/pkgconfig/*.pc
%{_libdir}/libDeployPkg.so
%{_libdir}/libguestlib.so
%{_libdir}/libhgfs.so
#%{_libdir}/libvgauth.so
%{_libdir}/libvmtools.so

%changelog
* Fri Aug 14 2015 Richard W.M. Jones <rjones@redhat.com> - 9.10.2-4
- Enable PrivateTmp for additional hardening
  resolves: rhbz#1253698

* Wed Jul 29 2015 Richard W.M. Jones <rjones@redhat.com> - 9.10.2-3
- Enable deploypkg
  resolves: rhbz#1172335

* Mon Jul 27 2015 Richard W.M. Jones <rjones@redhat.com> - 9.10.2-2
- Disable vgauthd service in vmtoolsd.service file.
  resolves: rhbz#1172833

* Tue Jul 07 2015 Ravindra Kumar <ravindrakumar@vmware.com> - 9.10.2-1
- Package new upstream version open-vm-tools-9.10.2-2822639
- Removed the patches that are no longer needed
  resolves: rhbz#1172833

* Wed May 20 2015 Ravindra Kumar <ravindrakumar@vmware.com> - 9.10.0-2
- Claim ownership for /etc/vmware-tools directory
  resolves: rhbz#1223498

* Wed May 20 2015 Richard W.M. Jones <rjones@redhat.com> - 9.10.0-1
- Rebase to open-vm-tools 9.10.0 (synchronizing with F22)
  resolves: rhbz#1172833

* Fri Sep 19 2014 Richard W.M. Jones <rjones@redhat.com> - 9.4.0-6
- Really rebuild for updated procps
  resolves: rhbz#1140149

* Wed Sep 10 2014 Richard W.M. Jones <rjones@redhat.com> - 9.4.0-5
- Rebuild for updated procps
  resolves: rhbz#1140149

* Mon Aug 18 2014 Richard W.M. Jones <rjones@redhat.com> - 9.4.0-4
- Removed unnecessary package dependency on 'dbus'
- Moved 'vm-support' script to /usr/bin
- Added a call to 'tools.set.version' RPC to inform VMware
  platform when open-vm-tools has been uninstalled
- Add missing package dependency on 'which' (BZ#1045709)
- Add missing package dependencies (BZ#1045709, BZ#1077320)

* Tue Feb 11 2014 Richard W.M. Jones <rjones@redhat.com> - 9.4.0-3
- Only build on x86-64 for RHEL 7 (RHBZ#1054608).

* Wed Dec 04 2013 Richard W.M. Jones <rjones@redhat.com> - 9.4.0-2
- Rebuild for procps SONAME bump.

* Wed Nov 06 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.4.0-1
- Package new upstream version open-vm-tools-9.4.0-1280544.
- Added CUSTOM_PROCPS_NAME=procps and -Wno-deprecated-declarations
  for version 9.4.0.

* Thu Aug 22 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-11
- Added copyright and license text.
- Corrected summary for all packages. 

* Thu Aug 08 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-10
- Added options for hardening build (bug 990549). 
- Excluded unwanted file mount.vmhgfs from packaging (bug 990547).
- Removed deprecated key "Encoding" from "Desktop Entry" (bug 990552).

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 9.2.3-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jun  4 2013 Richard W.M. Jones <rjones@redhat.com> - 9.2.3-8
- RHEL 7 now includes libdnet, so re-enable it.

* Fri May 24 2013 Richard W.M. Jones <rjones@redhat.com> - 9.2.3-6
- +BR gcc-c++.  If this is missing it fails to build.
- On RHEL, disable libdnet.

* Mon May 06 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-5
- Renamed source file open-vm-tools.service -> vmtoolsd.service
  to match it with the service name.

* Wed May 01 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-4
- Bumped the release to pick the new service definition with
  no restart directive.

* Mon Apr 29 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-3
- open-vm-tools-9.2.3 require glib-2.14.0.

* Mon Apr 29 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-2
- Bumped the release to pick the new service definition.

* Thu Apr 25 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.3-1
- Package new upstream version open-vm-tools-9.2.3-1031360.
- Removed configure options CUSTOM_PROCPS_NAME (for libproc) and
  -Wno-deprecated-declarations as these have been addressed in
  open-vm-tools-9.2.3-1031360.

* Wed Apr 24 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-12
- Removed %%defattr and BuildRoot.
- Added ExclusiveArch.
- Replaced /usr/sbin/ldconfig with /sbin/ldconfig.

* Mon Apr 22 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-11
- Removed the conditional steps for old versions of Fedora and RHEL.

* Thu Apr 18 2013 Ravindra Kumar <ravindrakumar at vmware.com> - 9.2.2-10
- Addressed formal review comments from Simone Caronni.
- Removed %%check section because 'make check' brings font file back.

* Wed Apr 17 2013 Simone Caronni <negativo17@gmail.com> - 9.2.2-9
- Removed rm command in %%check section.
- Remove blank character at the beginning of each changelog line.

* Mon Apr 15 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-8
- Removed FreeSans.ttf font file from packaging.
- Added 'rm' command to remove font file in %%check section because
  'make check' adds it back.
- Added doxygen dependency back.

* Thu Apr 11 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-7
- Applied patch from Simone for removal of --docdir option from configure.
- Removed unnecessary --enable-docs option from configure.
- Removed doxygen dependency.

* Thu Apr 11 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-6
- Replaced vmtoolsd with a variable.
- Changed summary for subpackages to be more specific.
- Removed drivers.txt file as we don't really need it.
- Fixed vmGuestLib ownership for devel package.
- Removed systemd-sysv from Requires for Fedora 18+ and RHEL 7+.
- Made all "if" conditions consistent.

* Wed Apr 10 2013 Simone Caronni <negativo17@gmail.com> - 9.2.2-5
- Added RHEL 5/6 init script.
- Renamed SysV init script / systemd service file to vmtoolsd.
- Fixed ownership of files from review.
- Moved api documentation in devel subpackage.
- Removed static libraries.

* Tue Apr 09 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-4
- Applied part of review fixes patch from Simone Caronni for systemd setup.
- Replaced tabs with spaces all over.

* Tue Apr 09 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-3
- Applied review fixes patch from Simone Caronni.
- Added missing *.a and *.so files for devel package.
- Removed unnecessary *.la plugin files from base package.

* Mon Apr 08 2013 Ravindra Kumar <ravindrakumar@vmware.com> - 9.2.2-2
- Modified SPEC to follow the conventions and guidelines.
- Addressed review comments from Mohamed El Morabity.
- Added systemd script.
- Verified and built the RPMS for Fedora 18.
- Fixed rpmlint warnings.
- Split the UX components in a separate package for desktops.
- Split the help files in a separate package for help.
- Split the guestlib headers in a separate devel package.

* Mon Jan 28 2013 Sankar Tanguturi <stanguturi@vmware.com> - 9.2.2-1
- Initial SPEC file to build open-vm-tools for Fedora 17.
