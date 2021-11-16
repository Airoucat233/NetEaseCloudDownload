## NetEaseCloudDownload
### 简介
这是一个批量下载网易云歌单的python脚本，主要功能是批量下载网易云歌单中所有**非VIP仅试听且没有下架的曲目(变灰）**，并且添加完整的ID3信息(标题,歌手,封面图)，可用于上传至云盘匹配曲库
### 主要依赖
1. requests 发送请求调用接口
2. mutagen 修改音乐文件ID3信息
3. selenium 网页自动化工具 PS:选择下载高音质(320K+)时需要用到此工具到另一个站点http://tool.liumingye.cn/music搜索并下载(才不是因为我还没搞明白网易云API才这么弄的)
### 使用
#### 1.命令行运行
首先下载本项目源码
```
git clone https://github.com/Airoucat233/NetEaseCloudDownload.git
```
```
cd NetEaseCloudDownload
```