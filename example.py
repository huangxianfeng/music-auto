import os
import time
from dotenv import load_dotenv
from douyin_music import BrowserManager, DouyinMusicConsole


def main():
    load_dotenv()

    browser_manager = BrowserManager(
        headless=False,
        slow_mo=100,
        cookie_path="cookies.json"
    )

    try:
        browser_manager.start()
        browser_manager.load_cookies()

        console = DouyinMusicConsole(browser_manager)

        username = os.getenv("DOUYIN_USERNAME")
        password = os.getenv("DOUYIN_PASSWORD")

        if not username or not password:
            print("Please set DOUYIN_USERNAME and DOUYIN_PASSWORD in .env file")
            return

        login_success = console.login(username, password)
        
        if login_success:
            print("Login successful!")

            overview = console.get_data_overview()
            print("Data Overview:", overview)

            songs = console.get_songs_list()
            print(f"Found {len(songs)} songs")
            for song in songs:
                print(f"- {song['name']} by {song['artist']} ({song['status']})")

            time.sleep(5)
            console.logout()
        else:
            print("Login failed!")

    finally:
        browser_manager.stop()


if __name__ == "__main__":
    main()