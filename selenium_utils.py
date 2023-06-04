import sys
import time
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from print_utils import Printer


class Download_Data:
    def __init__(self, link) -> None:
        self.chrome_driver = "./chromedriver_mac_arm64/chromedriver"
        self.options = webdriver.ChromeOptions()
        self.prefs = {"download.default_directory": str(Path().parent.absolute())}
        self.options.add_experimental_option("prefs", self.prefs)
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            chrome_options=self.options,
        )
        self.link = link

    def setUp(self):
        task = f"opening {self.link}"
        Printer.yellow(task)
        self.driver.get(self.link)
        Printer.green("success: " + task)

    def download(self):
        task = f"downloading from {self.link}"
        Printer.yellow(task)
        self.driver.implicitly_wait(5)
        dropdown = Select(
            self.driver.find_element(By.ID, "downloadSelect")
        ).select_by_visible_text("Bitcoin")
        download_button = self.driver.find_element(By.ID, "downloadButton").click()
        time.sleep(5)
        Printer.green("success: " + task)

    def tearDown(self):
        self.driver.close()
        Printer.red("closing webdriver")

    def run(self):
        self.setUp()
        self.download()
        self.tearDown()
