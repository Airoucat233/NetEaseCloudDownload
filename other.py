import json
import logging
import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB ,ID3NoHeaderError
import requests, os, time
from requests.cookies import cookiejar_from_dict
from scrapy.selector import Selector
import chardet
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

config_path = './config.json'
dir_path = r'./MusicDownLoad'
dir_cover=dir_path + os.sep +"Cover"
failed_music=[]
# def check_charset(file_path):
#     with open(file_path, "rb") as f:
#         data = f.read(4)
#         charset = chardet.detect(data)['encoding']
#     return charset

class Download_netease_cloud_music():
    def __init__(self):
        if not os.path.exists(config_path):
            with open(config_path,'w') as f:
                f.write(json.dumps({'user':{'username':'','password':''}}))
        config = {}
        with open(config_path, 'r') as f:
            config = json.loads(f.read())
        self.username=config.get('user').get('username')
        self.password=config.get('user').get('password')
        self.cookies=''
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
            'Referer': 'http://music.163.com/'}
        self.login()
        self.main_url = 'http://music.163.com/'
        self.session = requests.Session()
        self.session.headers = self.headers
        self.session.cookies=cookiejar_from_dict(self.cookies)

    def login(self):
        if not self.username or not self.password:
            self.username=input('请输入用户名:')
            self.password = input('请输入密码:')
            config = {}
            with open(config_path,'r') as f:
                config = json.loads(f.read())
                config['user']['username'] = self.username
                config['user']['password'] = self.password
            with open(config_path, 'w') as f:
                f.write(json.dumps(config))
        t = int(time.time())
        url='https://netease-cloud-music-api-gamma-orpin.vercel.app/login/cellphone'
        url += "?timestamp=" + str(t)
        res = requests.post(url,data={f"phone":f"{self.username}","password":f"{self.password}"},headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"})
        json_obj=json.loads(res.text)
        if json_obj.get('code')==200:
            print('登陆成功')

            self.cookies=self.getCookieDict(json_obj.get('cookie'))

    def getCookieDict(self,cook):
        cookies = {}  # 初始化cookies字典变量
        for line in cook.split(';'):  # 按照字符：进行划分读取
            # 其设置为1就会把字符串拆分成2份
            if line != "":
                name, value = line.strip().split('=')
                cookies[name] = value  # 为字典cookies添加内容
        return cookies

    def get_songurls(self, playlist):
        '''进入所选歌单页面，得出歌单里每首歌各自的ID 形式就是“song?id=64006"'''
        url = self.main_url + 'playlist?id=%d' % playlist
        re = self.session.get(url)  # 直接用session进入网页，懒得构造了
        sel = Selector(text=re.text)  # 用scrapy的Selector，懒得用BS4了
        songurls = sel.xpath('//ul[@class="f-hide"]/li/a/@href').extract()
        return songurls  # 所有歌曲组成的list
        #['/song?id=64006', '/song?id=63959', '/song?id=25642714', '/song?id=63914', '/song?id=4878122', '/song?id=63650']

    def get_songinfo(self, songurl):
        """根据songid进入每首歌信息的网址，得到歌曲的信息"""
        url = self.main_url + songurl
        re = self.session.get(url)
        sel = Selector(text=re.text)
        songinfo={}
        songinfo['id']=url.split('=')[1]
        songinfo['name']=sel.xpath("//em[@class='f-ff2']/text()").extract_first().replace('/','-').replace(':',' ').replace('"','“')
        songinfo['singer']='&'.join(sel.xpath("//p[@class='des s-fc4']/span/a/text()").extract())
        songinfo['album'] = sel.xpath('//p[text()="所属专辑："]/a/text()')[0].root
        songinfo['path'] = dir_path + os.sep + songinfo['name'] + '.mp3'  # 文件路径
        songinfo['path_cover'] = dir_cover+os.sep+songinfo['album'].replace(':',' ').replace('/','-').replace('"','“')+ '.jpg'# 封面路径
        if not os.path.exists(songinfo['path_cover']):
            songinfo['cover_url']=sel.xpath('//img[@class="j-img"]/@data-src').extract_first()
        #songname = singer + '-' + song_name
        return songinfo

    def remove_sep(self,s:str):#去除多个歌手间的分隔符，不能因为分隔符不同就不匹配
        return s.replace(',','').replace(' ','').replace('&','')
    def found_at_least_one(self,driver):#供WebDriverWait.until调用
        return len(driver.find_elements(By.XPATH, "//div[@id=\'player\']/div/ol/li")) > 0
    def get_high_quality(self,driver,song_name,singer,quality='320K'):
        quality_map={
            '128K':'标准',
            '320K':'高品',
            'FLAC':'FLAC'
        }
        url='http://tool.liumingye.cn/music/?page=audioPage&type=YQD&name=%s'%song_name

        try:
            driver.get(url)
            WebDriverWait(driver, 8).until(self.found_at_least_one)#//div[text()="这里有点空哦…"]
            elements = driver.find_elements(By.XPATH,"//div[@id='player']/div/ol/li")
            # if len(elements) > 0:
            for el in elements:
                name = el.find_element(By.XPATH, "span[@class='aplayer-list-title']").get_attribute("textContent")
                author = el.find_element(By.XPATH, "span[@class='aplayer-list-author']").get_attribute("textContent")
                if name == song_name and self.remove_sep(author) == self.remove_sep(singer):
                    dl_button = el.find_element(By.XPATH,"span[@class='aplayer-list-download iconfont icon-xiazai']")
                    # ActionChains(driver).move_to_element(dl_button).click().perform()
                    driver.execute_script('arguments[0].click()', dl_button)
                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, 'm-download')))
                    return driver.find_element(By.XPATH, "//label[text()='%s']/../../input" % quality_map[quality]).get_attribute("value")
                    # driver.find_element(By.XPATH, "//label[text()='%s']/../../div[2]/a"%quality_map[quality]).click()
                    # if quality_map[quality]=='FLAC':
                    #     suffix = '.flac'
                    # else:
                    #     suffix = '.mp3'
                    # file_path = os.path.join(download_dir,song_name+' - '+singer+suffix)
                    # WebDriverWait(driver,20).until(lambda d:os.path.exists(file_path))
                    # if os.path.exists(file_path):
                    #     os.rename(file_path,file_path.replace(' - '+singer,''))
        except Exception as e:
            logging.error("浏览器操作期间发生了错误-->\n",e)

    def download_song(self, songurl, dir_path):
        '''根据歌曲url，下载mp3文件'''
        songinfo= self.get_songinfo(songurl)  # 根据歌曲url得出ID、歌名
        #song_url = 'http://music.163.com/song/media/outer/url?id=%s.mp3' % songinfo['id']
        song_url = self.get_high_quality(self.driver,songinfo['name'],songinfo['singer'], '320K')

        if songinfo.get('cover_url'):#避免重复下载同一个专辑封面
            try:
                res = requests.get(songinfo['cover_url'], headers=self.headers,cookies=self.cookies)
                with open(songinfo['path_cover'], "wb+") as f:
                    f.write(res.content)
            except Exception as e:
                logging.error(f"${songinfo['name']} 封面下载失败!")
        try:
            res = requests.get(song_url, headers=self.headers,cookies=self.cookies)
            if os.path.exists(songinfo['path']):
                songinfo['path']=songinfo['path'].replace('.mp3',' .mp3')
            with open(songinfo['path'], "wb+") as f:
                f.write(res.content)
        except Exception as e:
            logging.error(f"${songinfo['name']} 下载失败!")
        return songinfo

    def setSongInfo(self,songinfo):
        try:
            audio = ID3(songinfo['path'])
        except ID3NoHeaderError:
            logging.error(f"${songinfo['path']}->没有ID3信息,新建中...")
            try:
                audio = mutagen.File(songinfo['path'], easy=False)
                audio.add_tags()
            except mutagen.MutagenError:
                logging.error(f"${songinfo['path']}->新建ID3信息失败,请检查音频文件能否正常打开")
                failed_music.append(songinfo['name'])
                return
            logging.error(f"新建ID3标签完成")
        except mutagen.MutagenError:
            logging.error(f"${songinfo['path']}->没有这个文件")
            failed_music.append(songinfo['name'])
            return
        audio.update_to_v23()  # 把可能存在的旧版本升级为2.3
        if os.path.exists(songinfo['path_cover']):
            img = open(songinfo['path_cover'], 'rb')
            s=img.read()
            img.close()
            audio['APIC'] = APIC(  # 插入专辑图片
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc=u'Cover',
                data=s
            )
        audio['TIT2'] = TIT2(  # 插入歌名
            encoding=3,
            text=[songinfo['name']]
        )
        audio['TPE1'] = TPE1(  # 插入第一演奏家、歌手、等
            encoding=3,
            text=[songinfo['singer']]
        )
        audio['TALB'] = TALB(  # 插入专辑名称
            encoding=3,
            text=[songinfo['album']]
        )
        audio.save()  # 记得要保存

    def work(self, playlist):
        if not os.path.exists(dir_cover):
            os.makedirs(dir_cover)
        songurls = self.get_songurls(playlist)  # 输入歌单编号，得到歌单所有歌曲的url
        chrome_options = Options()
        #chrome_options.add_argument('--headless')  # 无窗口启动chrome
        chrome_options.add_experimental_option("prefs", {"download.default_directory": dir_path})
        self.driver = webdriver.Chrome(options=chrome_options)
        try:
            for songurl in songurls:
                songinfo=self.download_song(songurl, dir_path)# 下载歌曲
                print(f"${songinfo['name']} 处理完成")
                self.setSongInfo(songinfo)#添加ID3信息
        except Exception as e:
            logging.error(e)
        finally:
            self.driver.close()




if __name__ == '__main__':
    d = Download_netease_cloud_music()
    d.work(7056793458)
    logging.error("下载失败或添加ID3信息失败的音乐:->"+failed_music.__str__())
