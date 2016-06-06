sudo apt-get -y install python-pip
sudo apt-get -y install python-dev
sudo pip install -Iv tornado==3.2.2
sudo pip install motor==0.4
sudo pip install mock
sudo pip install psutil
sudo pip install -Iv tornado-redis==2.4.18
sudo pip install redis==2.10.3 
sudo pip install hiredis
sudo pip install simplejson 
sudo pip install jieba
sudo apt-get install -y libfreetype6-dev
sudo apt-get install -y libjpeg-dev
sudo pip install pillow

sudo apt-get install -y libssl-dev
sudo apt-get install -y libffi-dev
sudo pip install cryptography
sudo pip install pypinyin
sudo pip install tornadoes
sudo pip install elasticsearch
sudo pip install qrcode

wget -c https://pypi.python.org/packages/source/f/futures/futures-2.1.6.tar.gz 
tar xzvf futures-2.1.6.tar.gz 
cd futures-2.1.6 
sudo python setup.py install

echo "******************************************"
echo "******************************************"
echo "Please ensure ulimit -n output >6000 first, then use supervisor."
echo "******************************************"
echo "******************************************"
