import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- あなたのStreamlitアプリのURLに書き換えてください ---
STREAMLIT_URL = "https://crewai-gemini-ec-automator.streamlit.app" # 例

def wake_up():
    print("🚀 アプリの起動を確認中...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(STREAMLIT_URL)
        time.sleep(10) # 読み込み待ち
        
        # 「Yes, get this app back up（スリープ解除）」ボタンを探してクリック
        try:
            wake_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button"))
            )
            wake_button.click()
            print("✅ スリープ解除ボタンをクリックしました。アプリが起きました！")
            time.sleep(10) # 起動完了まで待機
        except:
            print("ℹ️ アプリは既に起きています。正常です。")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    wake_up()