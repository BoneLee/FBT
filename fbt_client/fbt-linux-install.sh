#!/bin/bash
fbt_zip_line_at=112  #这个值是指这个脚本的行数加1
fbt_data_dir="$HOME/.fbt"
install_dir="$HOME"
fbt_link="$fbt_data_dir/fbt"

function uninstall_fbt {
    if [ -f $fbt_link ] ; then
      fbt_exe=`readlink -f $fbt_link`
      installed_dir=`dirname $fbt_exe`
      if [ -d $installed_dir ] ; then
        echo "Found previous install: $installed_dir"
        rm -rf $installed_dir
        echo "Deleted OK."
      fi
      rm -f $fbt_link
    fi
    
    if [ -d $fbt_data_dir ] ; then
      rm -rf "$fbt_data_dir/node_modules"
    fi
}

function install_fbt {
    tail -n +$fbt_zip_line_at $0 >/tmp/fbt.tar.bz2 # $0表示脚本本身，这个命令用来把从$fbt_zip_line_at开始的内容写入一个/tmp目录里
    cd /tmp
    tar xjf /tmp/fbt.tar.bz2  #TODO remove f
    find /tmp/fbt -name "*~" -exec rm {} \;
    if [ ! -d $fbt_data_dir ]; then
      mkdir $fbt_data_dir
    fi
    cp -r /tmp/fbt/node_modules $fbt_data_dir
    if [ -d "$install_dir/fbt" ] ; then  
      rm -rf "$install_dir/fbt"
    fi
    mv /tmp/fbt $install_dir 
    if [ ! -d $fbt_data_dir ] ; then  
      mkdir $fbt_data_dir -p
    fi
    if [ -f $fbt_link ] ; then rm -f $fbt_link; fi
    ln -s "$install_dir/fbt/fbt" "$fbt_link"

#    fbt_desktop=fbt.desktop
#    if [ -f $fbt_desktop ] ; then rm -f $fbt_desktop; fi
#    echo "[Desktop Entry]" >>$fbt_desktop
#    echo "Type=Application" >>$fbt_desktop
#    echo "Exec=$install_dir/fbt/fbt" >>$fbt_desktop
#    echo "Icon=$install_dir/fbt/logo.png" >>$fbt_desktop
#    echo "Terminal=false" >>$fbt_desktop
#    echo "Name=FBT" >>$fbt_desktop
#    chmod +rx $fbt_desktop
#    mv $fbt_desktop "$install_dir/fbt/"

    echo "Install completed. Please double click fbt to run..."
    nautilus "$install_dir/fbt"    
}

#function check_prestitute {
#    ; #[[ `ldd --version` =~ [1-9]+.[0-9]+.[0-9]+ ]] && glibc_version=$BASH_REMATCH
#}

while :
    do
      # If error exists, display it
      if [ "$ERR_MSG" != "" ]; then
        echo "Error: $ERR_MSG"
        echo ""
      fi

    echo "Welcome to fbt linux installer. Note that fbt must run on GLIBC version >= 2.15."
    echo "Enter a number to select to do. "
    echo "1) install fbt"
    echo "2) uninstall fbt"
    echo "3) exit"
    read number
    
    case $number in
      1) read -p "Enter directory name to install(default is $HOME/fbt):" fbt_install_dir
         fbt_install_dir=`echo $fbt_install_dir|sed -e 's/^ *//' -e 's/ *$//'`
         if [ "$fbt_install_dir" != "" ]; then
           install_dir=$fbt_install_dir
         fi
         if [ ! -d $install_dir ] ; then
           mkdir $install_dir -p
         fi
    
         if [ -d $install_dir ] ; then
            #check_prestitute
            uninstall_fbt
            echo "Installing fbt..." 
            install_fbt
         else
            echo "Install failed. Can't create $installed_dir directory."
         fi
         read -p "Click any key to exit" pass
         exit
         ;;
      2) echo "Uninstalling fbt..." 
         uninstall_fbt
         echo "Uninstall completed."
         read -p "Press any key to exit" pass
         exit
         ;;
      3) exit
         ;;
      *) ERR_MSG="Please enter a valid option!"
         ;;
    esac
      # This will clear the screen so we can redisplay the menu.
      clear
done
