import os
import shutil
f=open(r"F:\零度梦幻\Carplay\车载 1.txt",encoding='utf-8')
s=f.read()
f.close()
play_list=s.split('\n')
print(play_list)
num=0
for m in play_list:
    if os.path.exists(m):
        dst_file=m.replace('./Mp3、','./CarPlayList')
        dst_path=os.path.dirname(dst_file)
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        shutil.copy(m,dst_path)
        num+=1
        print(m," 成功复制至-> ",dst_path)
print(f"成功复制 {num} 个文件")
# os.makedirs('./CarPlayList/参考.py')
# shutil.copy('./参考.py','./CarPlayList/参考.py')