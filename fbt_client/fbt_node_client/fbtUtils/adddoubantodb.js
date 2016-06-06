//使用c:\MongoDB\bin>mongo localhost:27017/fbt --shell e:\fbt\src\fbt\fbt_node_client\fbtUtils\adddoubantodb.js

//在shell中使用js脚本可以直接这样写
//mongo host:port/dbname --shell jsname.js;
//load("E:\\fbt\\src\\fbt\\fbt_node_client\\fbtUtils\\douban.js");
//var douban = require('douban');
//var a=douban.getInfo('南京', callback(info));
//print(info.id);

db = connect("localhost:27017/fbt");
//print(db.getCollectionNames());
//db.all_resources.update({"file_name":"ubuntu-14.04"},{"$set":{"info":"ubuntu_info"}});
//a=db.all_resources.findOne({"file_name":"ubuntu-14.04"});
//a.info="ubuntu_add";
//print(a.info);
var count=0;

/*i=db.all_resources.findOne({"main_type":0,"exportinfo":null},{"file_name":1}); 
print(i.file_name);
t=db.all_resources.findOne({"file_name":i.file_name});
print(t.main_type);
for (j in i) print(j);
print(i.file_hash,i.file_size);
s=i.file_hash.toString();
i1=s.indexOf('(');
i2=s.indexOf(')');
//fid=i.file_hash.toString().substr(11,10)+'_'+i.file_size;
fid=i.file_hash.toString().substr(i1+1,i2-i1-1)+'_'+i.file_size;
print(fid);
tmp=db.all_resources.findOne({"file_id":fid})
print(tmp.file_hash);*/

total=db.all_resources.find({"main_type":0,"exportinfo":null}).count();
while(1)
{
    i=db.all_resources.findOne({"main_type":0,"exportinfo":null},{"file_name":1}); //0movie 1play
    if (i==null)
        break;
    fname=i.file_name;
    //print(fname);
    //query ->info
    db.all_resources.update({"file_name":fname,"exportinfo":null},{"$set":{"exportinfo":'1'}});
    //tmp=db.all_resources.findOne({"file_name":fname})
    count++;
    if (count % 100==0) print(count+'/'+total);
};

print("modified files:");
print(count);