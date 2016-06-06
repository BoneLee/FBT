#!/bin/bash
echo "Before packing, please ensure that nodejs is installed and npm command works."
echo "Also gcc, 新手须知.pdf  is needed."

node_version=`node -v`
if [ "$node_version" = "v0.10.32" ];then
    echo "node version v0.10.32 check OK."
else
    echo "node version v0.10.32 check failed."
    exit
fi

gcc_version=`ldd --version |head -n 1 | grep -o '[0-9.]*$'`
if [ `echo "$gcc_version >= 2.15" | bc -l` -eq 1 ]; then
    echo "gcc version >= 2.15 check OK."
else
    echo "gcc version >=2.15 check failed."
    exit
fi

echo "Choose platform first"
echo "1) linux 32 bit"
echo "2) linux 64 bit"
read number

node_webkit=node-webkit-v0.10.4-linux-ia32.tar.gz
platform=32
case $number in
  1) echo "OK. you choose 32 bit."
    ;;
  2) echo "OK. you choose 64 bit."
    node_webkit=node-webkit-v0.10.4-linux-x64.tar.gz
    platform=64
    ;;
  *) echo "Please enter a valid option! exit...."
    exit
    ;;
esac

if [ -f $node_webkit ]; then 
  echo "$node_webkit found here."; 
else
  echo "$node_webkit not found here. please download it first."; 
  exit; 
fi

echo "extract nodewebkit..."
tar xzf $node_webkit

if [ -d fbt ]; then rm -rf fbt; fi
mv `echo $node_webkit|sed -e "s/.tar.gz//"`  fbt

cd fbt_node_client
echo "rm *~ files."
find . -name "*~" -exec rm {} \;
cd ..

rm -rf fbt_node_client_pack
cp -r fbt_node_client fbt_node_client_pack
cd fbt_node_client_pack
rm -f node.exe
rm -rf nat_download # v4 nat removed
#rm -f nat_download/stun_Mac
#rm -f nat_download/stun_Win.exe
#if [ $platform == 32 ]; then
#    rm -f nat_download/stun_Linux64
#else
#    rm -f nat_download/stun_Linux
#    mv nat_download/stun_Linux64 nat_download/stun_Linux
#fi
rm -rf node_modules
npm cache clean
npm install

cp fbtLogo2.png ../fbt/logo.png
cp -r node_modules ../fbt/
cp ../新手须知.pdf ../fbt/
zip -r ../fbt.nw *
echo "fbt.nw generated."
cd ..

cat fbt/nw fbt.nw >fbt/fbt
chmod a+rx fbt/fbt

echo "rm unwanted nw and nwsnapshot."
rm fbt/nw
rm fbt/nwsnapshot

echo "pack fbt..."
tar cjf fbt.tar.bz2 fbt/
echo "fbt.tar.bz2 generated."

cat fbt-linux-install.sh fbt.tar.bz2 >fbt-linux-$platform-installer.run
echo "fbt-linux-$platform-installer.run generated."

rm -rf fbt
rm -f fbt.nw
rm -f fbt.tar.bz2
echo "all over."
