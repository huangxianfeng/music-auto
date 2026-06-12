import time
from typing import Optional, Dict, List
from .browser_manager import BrowserManager


class DouyinMusicConsole:
    BASE_URL = "https://music.douyin.com/console"

    def __init__(self, browser_manager: BrowserManager):
        self.browser = browser_manager
        self.is_logged_in = False

    def navigate(self):
        self.browser.go_to(self.BASE_URL)
        self.browser.wait_for_navigation()

    def login(self, username: str, password: str) -> bool:
        self.navigate()
        
        try:
            if self._check_login_status():
                self.is_logged_in = True
                return True

            login_btn = self.browser.wait_for_element('button:has-text("登录")', timeout=10000)
            if login_btn:
                self.browser.click('button:has-text("登录")')

            self.browser.wait_for_element('input[name="mobile"]', timeout=10000)
            self.browser.type('input[name="mobile"]', username)
            self.browser.type('input[name="password"]', password)

            self.browser.click('button:has-text("登录")')
            
            time.sleep(5)
            
            if self._check_login_status():
                self.is_logged_in = True
                self.browser.save_cookies()
                return True
            
            return False
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def _check_login_status(self) -> bool:
        try:
            self.browser.wait_for_element('span:has-text("控制台")', timeout=5000)
            return True
        except:
            return False

    def get_songs_list(self) -> List[Dict]:
        if not self.is_logged_in:
            raise Exception("Not logged in")

        songs = []
        try:
            self.browser.click('a:has-text("歌曲管理")')
            self.browser.wait_for_navigation()
            
            song_items = self.browser.page.query_selector_all('.song-item')
            for item in song_items:
                name_elem = item.query_selector('.song-name')
                artist_elem = item.query_selector('.artist-name')
                status_elem = item.query_selector('.status')
                song_info = {
                    'name': name_elem.text_content() if name_elem else '',
                    'artist': artist_elem.text_content() if artist_elem else '',
                    'status': status_elem.text_content() if status_elem else ''
                }
                songs.append(song_info)
        except Exception as e:
            print(f"Failed to get songs list: {e}")
        
        return songs

    def get_data_overview(self) -> Dict:
        if not self.is_logged_in:
            raise Exception("Not logged in")

        overview = {}
        try:
            self.browser.click('a:has-text("数据概览")')
            self.browser.wait_for_navigation()
            
            overview_items = self.browser.page.query_selector_all('.overview-item')
            for item in overview_items:
                label_elem = item.query_selector('.label')
                value_elem = item.query_selector('.value')
                label = label_elem.text_content() if label_elem else ''
                value = value_elem.text_content() if value_elem else ''
                overview[label] = value
        except Exception as e:
            print(f"Failed to get data overview: {e}")
        
        return overview

    def upload_song(
        self,
        audio_path: str,
        song_name: str,
        artist_name: str,
        cover_path: Optional[str] = None
    ) -> bool:
        if not self.is_logged_in:
            raise Exception("Not logged in")

        try:
            self.browser.click('a:has-text("上传歌曲")')
            self.browser.wait_for_navigation()

            self.browser.click('input[type="file"][accept="audio/*"]')
            self.browser.page.set_input_files('input[type="file"][accept="audio/*"]', audio_path)

            self.browser.type('input[name="songName"]', song_name)
            self.browser.type('input[name="artistName"]', artist_name)

            if cover_path:
                self.browser.click('input[type="file"][accept="image/*"]')
                self.browser.page.set_input_files('input[type="file"][accept="image/*"]', cover_path)

            self.browser.click('button:has-text("提交")')
            
            time.sleep(10)
            
            success_alert = self.browser.page.query_selector('.success-alert')
            return success_alert is not None
        except Exception as e:
            print(f"Failed to upload song: {e}")
            return False

    def logout(self):
        try:
            self.browser.click('.user-avatar')
            self.browser.click('button:has-text("退出登录")')
            self.is_logged_in = False
        except Exception as e:
            print(f"Logout failed: {e}")