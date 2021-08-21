from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import os

# class for handling web scraping via Selenium
# Selenium is needed for sites with complex login systems or designs (such as the use of Javascript) that make using standard download methods difficult or impossible
class SeleniumInstance:
    def __init__(self):
        self.driver = None
        self.attemptedDriver = False
        # dictionary of login status for sites using Selenium to scrape - key is site name, data is a tuple where first element is whether you are logged in, second is whether login has been attempted
        self.loginStates = {"wsj":(False,False), "apnews":(True,True), "washingtonpost":(True,True)} # no need to login to Associated Press so just setting that source to True

    # intialize Chrome webdriver for selenium use on certain sources (returns driver is successful)
    def initializeDriver(self):
        try:
            options = Options()
            options.headless = True
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.driver = webdriver.Chrome(options=options, executable_path='/usr/bin/chromedriver')
            self.driver.set_window_size(1200, 600) # even though we're headless this helps us avoid issues for some reason
        except Exception as e:
            print("Selenium Driver Error:",e)
            self.driver = None
        self.attemptedDriver = True

    def isLoggedIn(self,source): # checks whether you're logged into a site
        return self.loginStates[source][0] == True
    
    def hasAttemptedLogin(self,source): # checks whether you've attempted login (necessary for avoiding login retries after failure)
        return self.loginStates[source][1] == True

    # log into a specific source
    def login(self,source):
        getattr(self,source+"_login")() # all login functions need to follow this format
        return self.isLoggedIn(source)

    def wsj_login(self):
        if self.driver:
            try:
                login_url = "https://accounts.wsj.com/login"
                self.driver.get(login_url)
                wait = WebDriverWait(self.driver,30)
                userNameReady = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"input.username"))) # wait until username can be typed in
                # as of July 2020, WSJ seems to be randomly showing two different login screens
                # one is basic: enter username, then password, then hit "Sign In" button
                # the second requires an extra step: enter username, hit "Continue" button, enter password in box that appears, then "Sign In"
                # whichever button ("Sign In" vs. "Continue") does not have style tag attached determines which process is used
                try: 
                    # if no exception triggers at this line, then basic login process used (this block is basically an if/else)
                    BasicLoginAtStart = WebDriverWait(self.driver,5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.basic-login-submit")))
                    userNameReady.send_keys(os.environ['WSJ_EMAIL']) # type in username
                    containerID = "basic-login"
                except Exception: # Continue button not hidden (or doesn't exist, which will likely means an error will occur, probably due too site reformatting) - use alternate process
                    userNameReady.send_keys(os.environ['WSJ_EMAIL'])
                    ContinueReady = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.continue-submit")))
                    ContinueReady.click()
                    containerID = "password-login"
                passwordSelector = 'div#%s input[name="password"]' % (containerID,)
                passwordReadyToEnter = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,passwordSelector)))
                passwordReadyToEnter.click()
                passwordReadyToEnter.send_keys(os.environ['WSJ_PASSWORD'])
                loginSelector = 'div #%s button.basic-login-submit' % (containerID,)
                loginReady = WebDriverWait(self.driver,5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,loginSelector)))
                loginReady.click()
                redirectedToHomePage = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#customer-nav-full-name"))) # wait until username appears on WSJ homepage after login to confirm login status
                self.loginStates['wsj'] = (True,True)
            except Exception as e:
                print("WSJ Login Error: ",e)
                self.loginStates['wsj'] = (False,True)