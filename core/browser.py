import os
import time
import logging
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

try:
    from webdriver_manager.chrome import ChromeDriverManager

    _HAS_WDM = True
except ImportError:
    _HAS_WDM = False

from config import CONFIG

logger = logging.getLogger(__name__)


class BrowserDriver:
    """封装 Chrome 浏览器驱动的创建与会话管理。"""

    def __init__(
        self,
        headless: Optional[bool] = None,
        user_data_dir: Optional[str] = None,
        window_size: Optional[Tuple[int, int]] = None,
    ):
        self.headless = headless if headless is not None else CONFIG["headless"]
        self.user_data_dir = user_data_dir or CONFIG["user_data_dir"]
        self.window_size = window_size or CONFIG["window_size"]
        self.driver: Optional[webdriver.Chrome] = None

    def build_options(self) -> Options:
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": CONFIG["download_dir"],
                "profile.managed_default_content_settings.images": 2,
            },
        )
        return options

    def start(self) -> webdriver.Chrome:
        options = self.build_options()
        service = Service(ChromeDriverManager().install()) if _HAS_WDM else None
        if service is not None:
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(CONFIG["page_load_timeout"])
        self.driver.implicitly_wait(CONFIG["implicit_wait"])
        logger.info("浏览器已启动 (headless=%s)", self.headless)
        return self.driver

    def quit(self):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
            logger.info("浏览器已关闭")


class DouyinMusicConsole:
    """抖音音乐控制台自动化操作封装。"""

    URL = CONFIG["target_url"]

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    # ---------- 导航 & 登录 ----------
    def open(self) -> bool:
        try:
            self.driver.get(self.URL)
            time.sleep(3)
            logger.info("已打开: %s", self.driver.current_url)
            return True
        except TimeoutException:
            logger.error("页面加载超时")
            return False

    def is_logged_in(self) -> bool:
        """简单判断是否已登录：根据 URL 是否跳转回登录页或是否存在登录按钮。"""
        url = self.driver.current_url.lower()
        if "login" in url or "sign" in url:
            return False
        login_hints = ("登录", "登陆", "login")
        page_text = self.driver.page_source
        return not any(h in page_text for h in login_hints) or "console" in url

    def require_login(self, wait_seconds: int = 120) -> bool:
        """首次使用需要人工扫码登录；后续会复用 user_data_dir 中的 cookie。"""
        if self.is_logged_in():
            return True
        logger.warning(
            "检测到未登录，请在 %s 秒内使用抖音 APP 扫码完成登录...", wait_seconds
        )
        for _ in range(wait_seconds // 3):
            if self.is_logged_in():
                logger.info("登录成功")
                return True
            time.sleep(3)
        logger.error("登录等待超时")
        return False

    # ---------- 导航菜单 ----------
    def goto_section(self, keyword: str) -> bool:
        """点击侧边栏包含指定关键词的条目（例如「创作音乐」「作品管理」）。"""
        try:
            locator = (
                By.XPATH,
                f"//*[self::a or self::button or self::div][contains(normalize-space(.), '{keyword}')]",
            )
            el = self.wait.until(EC.element_to_be_clickable(locator))
            el.click()
            time.sleep(2)
            logger.info("已跳转至: %s", keyword)
            return True
        except (TimeoutException, ElementClickInterceptedException) as e:
            logger.warning("无法定位/点击 %s: %s", keyword, e)
            return False

    # ---------- 上传音乐 ----------
    def upload_music(self, file_path: str, title: Optional[str] = None) -> bool:
        """在控制台找到上传按钮并选择文件。"""
        if not os.path.exists(file_path):
            logger.error("文件不存在: %s", file_path)
            return False
        try:
            file_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            file_input.send_keys(os.path.abspath(file_path))
            logger.info("已选择文件: %s", file_path)
            time.sleep(3)

            if title:
                self._fill_title(title)

            submit = self._find_submit_button()
            if submit:
                submit.click()
                logger.info("已提交上传")
                return True
            return False
        except (TimeoutException, NoSuchElementException) as e:
            logger.error("上传失败: %s", e)
            return False

    def _fill_title(self, title: str) -> None:
        try:
            inputs = self.driver.find_elements(
                By.XPATH, "//input[@placeholder and not(@type='file')]"
            )
            if inputs:
                inputs[0].clear()
                inputs[0].send_keys(title)
                logger.info("已填写标题: %s", title)
        except Exception as e:
            logger.debug("填写标题失败: %s", e)

    def _find_submit_button(self):
        for text in ("发布", "提交", "确认", "保存", "上传", "Publish", "Submit"):
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    f"//button[contains(normalize-space(.), '{text}')] | //*[@role='button'][contains(normalize-space(.), '{text}')]",
                )
                return btn
            except NoSuchElementException:
                continue
        return None

    # ---------- 作品管理 ----------
    def list_works(self, max_items: int = 20):
        """简单抓取作品列表的标题文本，返回列表。"""
        try:
            self.goto_section("作品管理")
            cards = self.driver.find_elements(
                By.XPATH, "//*[self::div or self::li][contains(@class, 'item') or contains(@class, 'card')]"
            )[:max_items]
            return [c.text.strip().splitlines()[0] for c in cards if c.text.strip()]
        except Exception as e:
            logger.warning("抓取作品列表失败: %s", e)
            return []

    # ---------- 自动创作/AI 音乐 ----------
    def auto_create_music(self, prompt: str, lyrics: Optional[str] = None) -> bool:
        """定位到 AI 创作入口，填写提示词与歌词，触发生成。"""
        try:
            self.goto_section("创作音乐")
            time.sleep(2)

            prompt_box = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//textarea | //input[@type='text' and not(@type='file')]")
                )
            )
            prompt_box.clear()
            prompt_box.send_keys(prompt)
            logger.info("已填写 prompt: %s", prompt[:40])

            if lyrics:
                try:
                    lyrics_boxes = self.driver.find_elements(By.TAG_NAME, "textarea")
                    if len(lyrics_boxes) >= 2:
                        lyrics_boxes[1].clear()
                        lyrics_boxes[1].send_keys(lyrics)
                        logger.info("已填写歌词")
                except Exception:
                    pass

            gen_btn = self._find_submit_button() or self.driver.find_element(
                By.XPATH, "//button"
            )
            gen_btn.click()
            logger.info("已触发音乐生成")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logger.error("自动创作失败: %s", e)
            return False
