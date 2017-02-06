1.  create directories under ~/

    <code>#  mkdir -p ~/{BUILD,RPMS,SOURCES,SPECS,SRPMS}</code>

2. copy source tar to SOURCEs directory:

    <code># cp open-vm-tools-10.0.5-3227872.tar.gz ~/SOURCES </code>
    
3.  run rpmbuild command

    <code># rpmbuild -bb open-vm-tools.spec</code>
