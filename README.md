# NetEaseCloudDownload
###更新日志
2021-11-18:保存歌单ID至config.json,不必每次都输入歌单ID
## 简介
这是一个批量下载网易云歌单的python脚本，主要功能是批量下载网易云歌单中所有**非VIP仅试听且没有下架的曲目(变灰）**，并且添加完整的ID3信息(标题,歌手,封面图)，可用于上传至云盘匹配曲库
## 使用场景
1. 在网易云听到喜欢的歌
2. 收藏至一个专用待下载歌单,将该歌单ID根据程序运行提示输入下载整个歌单3
3. 将下载的本地文件上传至云盘,清空待下载歌单待下次使用
## 主要依赖
1. `requests` 发送请求调用接口
2. `mutagen` 修改音乐文件ID3信息
3. `selenium` 网页自动化工具 PS:选择下载高音质(320K+)时需要用到此工具到[另一个站点](http://tool.liumingye.cn/music)搜索并下载(才不是因为我还没搞明白网易云API才这么弄的)
## 使用
### 写在前面
使用selenium库必须安装浏览器和相应版本的浏览器驱动(本项目中是`chrome`和`chromedriver`)这里给出Windows下的具体做法,linux下更为复杂可以参考[这篇文章](https://www.cnblogs.com/brady-wang/p/11977391.html)
1. 安装chrome浏览器,如果已经安装,查看一下版本号
2. 到[chromedriver镜像站](http://npm.taobao.org/mirrors/chromedriver/)相应版本目录下下载`chromedriver_win32.zip`
3. 解压后将`chromedriver.exe`放到python根目录下(注意区分是否virtualenv,见下文)
### Windows
#### 下载打包后的exe可执行文件双击运行
```

```
#### 直接运行源码
1. 命令行下通过git下载本项目源码并进入该目录(我用的CMD而不是Git bash)
```
git clone https://github.com/Airoucat233/NetEaseCloudDownload.git

cd NetEaseCloudDownload
```
2. 如果你想为这个程序单独设置一个python依赖环境,可以使用`virtualenv`
```bash
pip install virtualenv      #安装

virtualenv env      #创建一个虚拟环境,env为虚拟环境目录名，目录名自定义

env\Scripts\activate        #执行该路径下的activate.bat激活环境

env\Scripts\deactivate      #停止

env\Scripts\pip install -r requirements.txt #用该环境的pip安装依赖列表中的依赖
```
安装完的依赖就放到了`NetEaseCloudDownload\env\Lib\site-packages`,不影响系统python环境

如果不在意这个,可以直接运行下面命令安装依赖
```bash
pip install -r requirements.txt
```
3. 运行源码
```
#当前目录为NetEaseCloudDownload

env\Scripts\python src\main.py       #设置了virtualenv

python src\main.py      #没设置virtualenv

# 一些选项
python src\main.py <歌单ID或链接> -u <用户名> -p <密码>
python src\main.py --show-browser #显示浏览器操作(仅Windows下)
```
4. 生成exe可执行程序
```
env\Scripts\pyinstaller -F src/main.py --distpath <生成路径> -n <文件名>
```
执行完成后再dist目录可以看到`main.exe`
### Linux
Linux下安装依赖和Windows命令行方式差不多,只不过注意一下系统的目录分隔符由反斜杠`\` 改成斜杠`/`，这里不再重复

**特别注意**

由于此项目用到了`selenium`操作chrome浏览器,chrome浏览器在linux下不能以root权限运行，所以我们需要以**其他用户**的身份运行。如果你clone项目时由于在目录中权限不足而使用了`sudo git clone`的话,clone下来的文件夹权限对其他用户是没有写入权限的(程序中写入音乐文件需要权限)，所以最好是直接修改一下目录的权限
```
sudo chmod 777 NetEaseCloudDownload
```
