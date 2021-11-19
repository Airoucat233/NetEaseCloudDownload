import sys
import re
import getopt
import json
import logging
import mutagen
import requests, os, time
from requests.cookies import cookiejar_from_dict
from scrapy.selector import Selector
# import chardet
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from util.tagAudio import modify

version = 'v1.6'
show_head = False  # 调试时方便控制浏览器是否显示
config_path = 'config.json'
dir_path = r'MusicDownLoad'
dir_cover = dir_path + os.sep + "Cover"
global_args = {'args': [], 'options': {}}
quality_list = [
    {'level': 0, 'br': '128K', 'desc': '标准', 'suffix': '.mp3'},
    {'level': 1, 'br': '320K', 'desc': '高品', 'suffix': '.mp3'},
    {'level': 2, 'br': 'FLAC', 'desc': 'FLAC', 'suffix': '.flac'}
]




class Download_netease_cloud_music():
    def __init__(self, playlist, username, password):
        if not os.path.exists(dir_cover):
            os.makedirs(dir_cover)
        config = check_config(config_path)
        if username:
            self.username = username
        else:
            self.username = config.get('user').get('username')
        if password:
            self.password = password
        else:
            self.password = config.get('user').get('password')
        if playlist:
            self.playlist = playlist
        else:
            self.playlist = config.get('playlist')

        self.filename_rep_rule = config.get('filename_rep_rule')
        self.cookies = ''
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
            'Referer': 'http://music.163.com/'}
        self.login()
        self.main_url = 'http://music.163.com/'
        self.session = requests.Session()
        self.session.headers = self.headers
        self.session.cookies = cookiejar_from_dict(self.cookies)
        self.failed_music = []
        self.music_quality = {}

        while not self.playlist:
            key_in = input("请输入要下载的歌单ID或链接:\n")
            if re.match('\d+', key_in):
                self.playlist = key_in
            elif re.search('music.163.com/(#/)?playlist\?id=\d+', key_in):
                self.playlist = re.search('id=\d+', key_in).group().replace('id=', '')
            else:
                print('无法识别歌单ID,请重新输入!')
                continue
            with open(config_path, 'r') as f:
                config = json.loads(f.read())
                config['playlist'] = self.playlist
            with open(config_path, 'w') as f:
                f.write(json.dumps(config,indent=4))
        while not self.music_quality:
            accept = input(
                "输入相应数字设置下载音乐的音质,直接输入回车默认320K：\n(注意:选择128K以上音质需要调用浏览器,速度会慢一些)\n  1、128Kbps  2、320Kbps  3、FLAC\n")
            try:
                if accept == '':
                    self.music_quality = quality_list[1]
                else:
                    self.music_quality = quality_list[int(accept) - 1]
            except Exception:
                print("输入无效请重新输入!")
                time.sleep(0.2)

    def login(self):
        if not self.username or not self.password:
            if not self.username:
                self.username = input('请输入用户名:')
            self.password = input('请输入密码:')
        t = int(time.time())
        url = 'https://netease-cloud-music-api-gamma-orpin.vercel.app/login/cellphone'
        url += "?timestamp=" + str(t)
        res = requests.post(url, data={f"phone": f"{self.username}", "password": f"{self.password}"},
                            headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"})
        json_obj = json.loads(res.text)
        if json_obj.get('code') == 200:
            print('登录成功')
            with open(config_path, 'r') as f:
                config = json.loads(f.read())
                config['user']['username'] = self.username
                config['user']['password'] = self.password
            with open(config_path, 'w') as f:
                f.write(json.dumps(config, indent=4))
            self.cookies = self.getCookieDict(json_obj.get('cookie'))

    def getCookieDict(self, cook):
        cookies = {}  # 初始化cookies字典变量
        for line in cook.split(';'):  # 按照字符：进行划分读取
            # 其设置为1就会把字符串拆分成2份
            if line != "":
                name, value = line.strip().split('=')
                cookies[name] = value  # 为字典cookies添加内容
        return cookies

    def get_songurls(self, playlist):
        '''进入所选歌单页面，得出歌单里每首歌各自的ID 形式就是“song?id=64006"'''
        url = self.main_url + 'playlist?id=%s' % playlist
        re = self.session.get(url)  # 直接用session进入网页，懒得构造了
        sel = Selector(text=re.text)  # 用scrapy的Selector，懒得用BS4了
        songurls = sel.xpath('//ul[@class="f-hide"]/li/a/@href').extract()
        return songurls  # 所有歌曲组成的list
        # ['/song?id=64006', '/song?id=63959', '/song?id=25642714', '/song?id=63914', '/song?id=4878122', '/song?id=63650']

    def replace_sepecial_char(self,string:str,rule_map:dict):
        new_str=string
        if rule_map:
            for k in rule_map.keys():
                new_str=new_str.replace(k,rule_map[k])
        else:
            logging.error('没有特殊字符替换字典,可能会发生由于文件名有特殊字符而创建失败的情况,请检查配置文件!')
        return new_str
    def get_songinfos(self, songurls):
        songinfos = []
        for songurl in songurls:
            """根据songid进入每首歌信息的网址，得到歌曲的信息"""
            url = self.main_url + songurl
            re = self.session.get(url)
            sel = Selector(text=re.text)
            songinfo = {}
            songinfo['id'] = url.split('=')[1]
            songinfo['name'] = sel.xpath("//em[@class='f-ff2']/text()").extract_first()
            songinfo['song_file_name']=self.replace_sepecial_char(songinfo['name'],self.filename_rep_rule)
            songinfo['singer'] = '&'.join(sel.xpath("//p[@class='des s-fc4']/span/a/text()").extract())
            songinfo['singer_file_name'] = self.replace_sepecial_char(songinfo['singer'], self.filename_rep_rule)
            songinfo['album'] = sel.xpath('//p[text()="所属专辑："]/a/text()')[0].root
            songinfo['album_file_name'] = self.replace_sepecial_char(songinfo['album'], self.filename_rep_rule)
            songinfo['path'] = dir_path + os.sep + songinfo['song_file_name'] + self.music_quality['suffix']  # 文件路径
            songinfo['path_cover'] = dir_cover + os.sep + songinfo['album_file_name'] + '.jpg'  # 封面路径
            if not os.path.exists(songinfo['path_cover']):
                songinfo['cover_url'] = sel.xpath('//img[@class="j-img"]/@data-src').extract_first()
            # songname = singer + '-' + song_name
            songinfos.append(songinfo)
        return songinfos

    def remove_sep(self, s: str):  # 去除多个歌手间的分隔符，不能因为分隔符不同就不匹配
        return s.replace(',', '').replace(' ', '').replace('&', '')

    def found_at_least_one(self, driver):  # 供WebDriverWait.until调用
        return len(driver.find_elements(By.XPATH, "//div[@id=\'player\']/div/ol/li")) > 0

    def get_high_quality(self, driver, song_name, singer, quality):
        url = 'http://tool.liumingye.cn/music/?page=audioPage&type=YQD&name=%s' % song_name

        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(self.found_at_least_one)  # //div[text()="这里有点空哦…"]
            elements = driver.find_elements(By.XPATH, "//div[@id='player']/div/ol/li")
            # if len(elements) > 0:
            print('在搜索结果中匹配...')
            print('歌名            ', '            歌手', '           匹配结果')
            for el in elements:
                name = el.find_element(By.XPATH, "span[@class='aplayer-list-title']").get_attribute("textContent")
                author = el.find_element(By.XPATH, "span[@class='aplayer-list-author']").get_attribute("textContent")
                if name == song_name and self.remove_sep(author) == self.remove_sep(singer):
                    print(name, '     ', author, '        ', '          成功')
                    dl_button = el.find_element(By.XPATH, "span[@class='aplayer-list-download iconfont icon-xiazai']")
                    # ActionChains(driver).move_to_element(dl_button).click().perform()
                    driver.execute_script('arguments[0].click()', dl_button)
                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, 'm-download')))
                    while quality['level'] >= 0:
                        download_url = driver.find_element(By.XPATH, "//label[text()='%s']/../../input" % quality[
                            'desc']).get_attribute("value")
                        if download_url == '' and quality['level'] != 0:
                            quality = quality_list[quality['level'] - 1]
                        else:
                            return download_url
                else:
                    print(name, '     ', author, '        ', '          失败')
            print('歌曲  ', song_name, '-', singer, ' 没有匹配结果')

        except Exception as e:
            logging.error(f"浏览器操作 获取 {song_name} - {singer} 期间发生了错误-->", e)

    def generate_pattern(self,match_str):
        pattern = ''
        for c in match_str:
            if c in ['\\', '/', '*', '?', '"', '<', '>', '|']:
                pattern += '.'
            elif c in ['.', '+']:
                pattern += f'\{c}'
            else:
                pattern += c
        return pattern
    def download_song(self, songinfo):
        '''根据歌曲url，下载mp3文件'''
        # songinfo= self.get_songinfo(songurl)  # 根据歌曲url得出ID、歌名
        if self.music_quality['br'] == '128K':
            song_url = 'http://music.163.com/song/media/outer/url?id=%s.mp3' % songinfo['id']
        else:
            song_url = self.get_high_quality(self.driver, songinfo['name'], songinfo['singer'], self.music_quality)

        if songinfo.get('cover_url'):  # 避免重复下载同一个专辑封面
            try:
                res = self.session.get(songinfo['cover_url'], headers=self.headers, cookies=self.cookies)
                print('封面res:请求url:', res.url, '\ncode', res.status_code, '\n字节数', res.content.__len__())
                with open(songinfo['path_cover'], "wb+") as f:
                    f.write(res.content)
            except Exception as e:
                logging.error(f"{songinfo['name']} 封面下载失败!")
        try:
            if os.path.exists(songinfo['path']):
                songinfo['path'] = songinfo['path'].replace(songinfo['song_file_name'],
                                                            songinfo['song_file_name'] + ' - ' + songinfo['singer_file_name'])
                if os.path.exists(songinfo['path']):
                    os.remove(songinfo['path'])
            res = self.session.get(song_url, headers=self.headers, cookies=self.cookies)
            print('歌曲res:请求url:', res.url, '\ncode', res.status_code, '\n字节数', res.content.__len__())
            if res.status_code == 200:  # 请求内容有效,直接写入
                with open(songinfo['path'], "wb+") as f:
                    f.write(res.content)
            else:  # 请求状态不对,尝试在浏览器中直接点击下载
                print(f'请求链接 {res.status_code} ,直接使用浏览器下载...')
                quality = self.music_quality
                file_path = os.path.join(dir_path, songinfo['name'] + ' - ' + songinfo['singer'] + quality['suffix'])
                while quality['level'] >= 0:
                    if quality['level']!=self.music_quality['level']:#如果音质自动调节并且后缀名变了，要更新文件名
                        songinfo['path'] = songinfo['path'].replace(self.music_quality['suffix'],quality['suffix'])
                        file_path = file_path.replace(self.music_quality['suffix'],quality['suffix'])
                    try:
                        element = self.driver.find_element(By.XPATH,"//label[text()='%s']/../../div[2]/a" % quality['desc'])
                        self.driver.execute_script('arguments[0].click()', element)
                    except Exception:
                        print(f"{songinfo['name']} 没有 {quality['br']} 音质的下载源,尝试切换低一级音质...")
                        if quality['level'] != 0:
                            quality = quality_list[quality['level'] - 1]
                        else:
                            logging.error(f"{songinfo['name']} 所有品质音源都下载失败")
                            break
                    if len(self.driver.window_handles) > 1:  # 点击下载后如果弹出新窗口,就切换过去获取地址栏url再请求一次
                        self.driver.switch_to.window(self.driver.window_handles[1])
                        try:
                            res1 = self.session.get(self.driver.current_url, headers=self.headers, cookies=self.cookies)
                            print('歌曲res1:请求url:', res1.url, '\ncode', res.status_code, '\n字节数', res.content.__len__())
                            if res1.status_code == 2000:
                                with open(songinfo['path'], "wb+") as f:
                                    f.write(res1.content)
                                break
                            else:
                                print(songinfo['name'], ' res1(第二次)请求无效，响应码 :', res.status_code)
                                raise Exception("连续两次请求无效,下载失败")
                        finally:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                    else:
                        if songinfo['name']==songinfo['song_file_name'] and songinfo['singer']==songinfo['singer_file_name']:
                            WebDriverWait(self.driver, 12).until(lambda d: os.path.exists(file_path))
                        else:
                            pattern = self.generate_pattern(songinfo['name'] + ' - ' + songinfo['singer'] + quality['suffix'])
                            file_path = wait_for_downloading(dir_path,12,pattern)
                        if not os.path.exists(songinfo['path']):  # 如果没有同名歌曲就把文件名里的歌手名去掉
                            os.rename(file_path, songinfo['path'])
                        break
        except Exception as e:
            if isinstance(e, TimeoutException):
                logging.error(f"{songinfo['name']} 下载超时!")
            else:
                logging.error(f"{songinfo['name']} 下载失败!", e)
            self.failed_music.append(songinfo)
        return songinfo

    def setSongInfo(self, songinfo):
        print(f'添加歌曲 {songinfo["name"]} 的标签信息...')
        try:
            modify(songinfo['path'],
                   title=songinfo['name'],
                   artist=songinfo['singer'],
                   album=songinfo['album'],
                   img_path=songinfo.get('path_cover'))
        except mutagen.MutagenError:
            os.remove(songinfo['path'])
            logging.error(f"{songinfo['path']}->添加标签信息失败,音频无效,已删除")
        except Exception as e:
            print(e)
        # try:
        #     audio = ID3(songinfo['path'])
        # except ID3NoHeaderError:
        #     print(f"{songinfo['path']}->没有ID3信息,新建中...")
        #     try:
        #         audio = mutagen.File(songinfo['path'], easy=False)
        #         if not hasattr(audio,'tags'):
        #             audio.add_tags()
        #     except mutagen.MutagenError:
        #         os.remove(songinfo['path'])
        #         logging.error(f"{songinfo['path']}->新建ID3信息失败,音频无效,已删除")
        #         if not songinfo in self.failed_music:
        #             self.failed_music.append(songinfo)
        #         return
        #     print(f"新建ID3标签完成")
        # except mutagen.MutagenError:
        #     logging.error(f"{songinfo['path']}->没有这个文件")
        #     if not songinfo in self.failed_music:
        #         self.failed_music.append(songinfo)
        #     return
        # if isinstance(audio,mutagen.mp3.MP3):
        #     audio.update_to_v23()  # 把可能存在的旧版本升级为2.3
        #
        # if os.path.exists(songinfo['path_cover']):
        #     img = open(songinfo['path_cover'], 'rb')
        #     s=img.read()
        #     img.close()

        # if os.path.exists(songinfo['path_cover']):
        #     img = open(songinfo['path_cover'], 'rb')
        #     s=img.read()
        #     img.close()
        #
        #     audio['APIC'] = APIC(  # 插入专辑图片
        #         encoding=3,
        #         mime='image/jpeg',
        #         type=3,
        #         desc=u'Cover',
        #         data=s
        #     )
        # audio['TIT2'] = TIT2(  # 插入歌名
        #     encoding=3,
        #     text=[songinfo['name']]
        # )
        # audio['TPE1'] = TPE1(  # 插入第一演奏家、歌手、等
        #     encoding=3,
        #     text=[songinfo['singer']]
        # )
        # audio['TALB'] = TALB(  # 插入专辑名称
        #     encoding=3,
        #     text=[songinfo['album']]
        # )
        # audio.save()  # 记得要保存

    def handle(self, songinfos):
        for songinfo in songinfos:
            try:
                self.download_song(songinfo)  # 下载歌曲
                self.setSongInfo(songinfo)  # 添加ID3信息
                print(f"{songinfo['name']} 处理完成")
            except Exception as e:
                print(f"{songinfo['name']} 处理期间发生错误!\n",e)
        print("-----------下载失败或添加ID3信息失败的音乐:--------------")
        for i in self.failed_music:
            print(i.get('name'))
        print("-----------------------------------------------------")

    def work(self):
        songurls = self.get_songurls(self.playlist)  # 输入歌单编号，得到歌单所有歌曲的url
        songinfos = self.get_songinfos(songurls)
        try:
            if self.music_quality['br'] != '128K':
                chrome_options = Options()
                if not global_args['options'].get('s') and not show_head:
                    chrome_options.add_argument('--headless')  # 无窗口启动chrome
                chrome_options.add_argument('–-no-sandbox')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument("window-size=1024,768")
                prefs = {"download.default_directory": os.path.abspath(dir_path), "download.prompt_for_download": False,
                         "profile.default_content_setting_values.automatic_downloads": 1}
                chrome_options.add_experimental_option("prefs", prefs)
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
                self.driver = webdriver.Chrome(options=chrome_options)
                print('浏览器运行中...')
            self.handle(songinfos)
            while len(self.failed_music) != 0:
                time.sleep(1)
                accept = input(
                    "是否尝试重新下载失败的音乐 ? 如果仍然失败,可能是网易云搜索不到这首歌,建议您去http://tool.liumingye.cn/music/?page=searchPage上换一个平台手动下载\n(y/n)?")
                if accept in ['y', 'Y', '']:
                    print('---------------------尝试处理下载失败的音乐----------------------')
                    fm = self.failed_music
                    self.failed_music = []
                    self.handle(fm)
                else:
                    break
        except Exception as e:
            logging.error(e)
        finally:
            if hasattr(self, 'driver'):
                print("关闭浏览器中...")
                self.driver.close()
                print("程序已退出")


def prase_args(argv):
    """选项
    -u : 用户名
    -p : 密码
    --show-browser 下载高音质时显示调用浏览器操作
    """
    kargs = {'u': None, 'p': None, 's': False}
    args = []
    try:
        opts, args = getopt.getopt(argv, "u:p:", ["help", "show-browser"])
    except getopt.GetoptError:
        print('参数格式错误!')
        print('格式: main.py <歌单ID> [-u <username> -p <password>]')
        print('   or: mian.py --help')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ['-u']:
            kargs['u'] = arg
        elif opt in ['-p']:
            if kargs.get('u') is None:
                print("请先输入用户名!")
                sys.exit(2)
            kargs['p'] = arg
        elif opt in ['--show-browser']:
            kargs['s'] = True
    if args == []:
        args.append(None)
    return kargs, args
#检查配置文件
def check_config(config_path):
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                    config = json.loads(f.read())
        except Exception:
            print("配置文件打开错误!")
            raise
    else:
        with open(config_path, 'w') as f:
            config = {
                "version": version,
                "user": {"username": '', "password": ''},
                "playlist": '',
                "filename_rep_rule": {':': ' ', '/': '_', '"': '“', '<': '(', '>': ')', '\\': '-', '*': '_', '?': '？','|': '_', }
            }
            f.write(json.dumps(config,indent=4))
            return  config
    if config.get('version') and config['version'] == version:
       return config
    else:#版本不对就更新config
        new_config = {
                    "version":version,
                    "user": {"username": config.get('user').get('username'), "password": config.get('user').get('password')},
                    "playlist": config.get('playlist'),
                    "filename_rep_rule":{':':' ','/':'_','"':'“','<':'(','>':')','\\':'-','*':'_','?':'？','|':'_',}
                }
        with open(config_path.replace('config.json','config_bak.json'), "w") as f:
            f.write(json.dumps(config,indent=4))

        with open(config_path, "w") as f:
            f.write(json.dumps(new_config,indent=4))
        return config
#等待文件下载完成
def wait_for_downloading(file_dir, wait_max_time, pattern=None):
    file_not_found = True
    end_time = time.time() + wait_max_time  # 设置下载超时时间
    while file_not_found:
        if (time.time() >= end_time):
            raise TimeoutException
        elif pattern == None:
            if os.path.exists(file_dir):
                file_not_found = False
        else:
            files = os.listdir(file_dir)
            for i in range(0, len(files)):
                if re.match(pattern, files[i]):
                    if not files[i].__contains__('.crdownload'):
                        file_not_found = False
                        return os.path.join(file_dir, files[i])
                    # print(re.search(file_reg,os.path.splitext(files[i])[0]))

if __name__ == '__main__':
    kargs, args = prase_args(sys.argv[1:])
    global_args['args'] = args
    global_args['options'] = kargs
    d = Download_netease_cloud_music(args[0], username=kargs['u'], password=kargs['p'])
    d.work()
