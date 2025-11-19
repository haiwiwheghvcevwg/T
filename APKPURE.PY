# ════════════════════════════════════════════════════════════════════════════
# 🔍 APKPure Scraper - Advanced Web Scraper with Cloudflare Bypass
# ════════════════════════════════════════════════════════════════════════════
# المطور: @omarxarafp | instagram.com/omarxarafp
# الوظيفة: سكرابر قوي لاستخراج التطبيقات من APKPure مع تجاوز Cloudflare
# Function: Powerful scraper to extract apps from APKPure with Cloudflare bypass
# ════════════════════════════════════════════════════════════════════════════
import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin, quote
# ════════════════════════════════════════════════════════════════════════════
# ⚙️ إعداد Cloudscraper | Cloudscraper Configuration
# ════════════════════════════════════════════════════════════════════════════
# إنشاء جلسة cloudscraper لتجاوز Cloudflare تلقائياً
# Create cloudscraper session to bypass Cloudflare automatically
scraper=cloudscraper.create_scraper(browser={'browser':'chrome','platform':'windows','mobile':False},delay=10,disableCloudflareV1=False)
# ════════════════════════════════════════════════════════════════════════════
# 🌐 روابط APKPure | APKPure URLs
# ════════════════════════════════════════════════════════════════════════════
BASE_URLS=['https://apkpure.com','https://apkpure.net','https://m.apkpure.com']
# ════════════════════════════════════════════════════════════════════════════
# 🔍 دالة البحث الرئيسية | Main Search Function
# ════════════════════════════════════════════════════════════════════════════
def scrapeApp(query):
 """
 دالة البحث والاستخراج الرئيسية
 Main search and extraction function
 Args:
 query (str): اسم التطبيق للبحث عنه | Application name to search for
 Returns:
 dict: بيانات التطبيق بصيغة JSON | Application data in JSON format
 """
 try:
  print(f"🔍 البحث عن | Searching for: {query}")
  query=query.strip().lower()
  app_url=search_app(query)
  if not app_url:
   return{'success':False,'error':'لم يتم العثور على التطبيق | Application not found'}
  print(f"✅ تم العثور على الرابط | Found URL: {app_url}")
  app_data=extract_app_data(app_url)
  if not app_data:
   return{'success':False,'error':'فشل استخراج بيانات التطبيق | Failed to extract app data'}
  download_url=get_download_link(app_url)
  if not download_url:
   return{'success':False,'error':'فشل الحصول على رابط التحميل | Failed to get download link'}
  app_data['downloadUrl']=download_url
  app_data['success']=True
  print(f"✅ تم استخراج البيانات بنجاح | Data extracted successfully")
  return app_data
 except Exception as e:
  print(f"❌ خطأ في السكرابر | Scraper error: {str(e)}")
  return{'success':False,'error':str(e)}
# ════════════════════════════════════════════════════════════════════════════
# 🔎 دالة البحث عن التطبيق | App Search Function
# ════════════════════════════════════════════════════════════════════════════
def search_app(query):
 """
 البحث عن التطبيق في APKPure
 Search for app in APKPure
 Args:
 query (str): اسم التطبيق | Application name
 Returns:
 str: رابط صفحة التطبيق | Application page URL
 """
 try:
  for base_url in BASE_URLS:
   try:
    search_url=f"{base_url}/search?q={quote(query)}"
    print(f"🌐 محاولة البحث في | Trying search at: {search_url}")
    response=scraper.get(search_url,timeout=30)
    if response.status_code!=200:
     print(f"⚠️ رمز الاستجابة | Response code: {response.status_code}")
     continue
    soup=BeautifulSoup(response.text,'html.parser')
    first_result=None
    first_result=soup.select_one('.search-results .first a')or soup.select_one('.search-dl a')or soup.select_one('ul[class*="search"] li a')or soup.select_one('div[class*="search-result"] a')
    if not first_result:
     first_result=soup.select_one('a[href*="/"][href*="-"]')
    if first_result and first_result.get('href'):
     app_path=first_result.get('href')
     if app_path.startswith('/'):
      return urljoin(base_url,app_path)
     elif app_path.startswith('http'):
      return app_path
   except Exception as e:
    print(f"⚠️ خطأ في البحث | Search error at {base_url}: {str(e)}")
    continue
  direct_url=f"{BASE_URLS[0]}/{query}"
  print(f"🔗 محاولة الرابط المباشر | Trying direct URL: {direct_url}")
  response=scraper.get(direct_url,timeout=30)
  if response.status_code==200:
   return direct_url
  return None
 except Exception as e:
  print(f"❌ خطأ في دالة البحث | Search function error: {str(e)}")
  return None
# ════════════════════════════════════════════════════════════════════════════
# 📥 دالة استخراج بيانات التطبيق | Extract App Data Function
# ════════════════════════════════════════════════════════════════════════════
def extract_app_data(url):
 """
 استخراج جميع بيانات التطبيق من صفحته
 Extract all app data from its page
 Args:
 url (str): رابط صفحة التطبيق | Application page URL
 Returns:
 dict: بيانات التطبيق | Application data
 """
 try:
  print(f"📄 استخراج البيانات من | Extracting data from: {url}")
  response=scraper.get(url,timeout=30)
  if response.status_code!=200:
   return None
  soup=BeautifulSoup(response.text,'html.parser')
  name=soup.select_one('h1')or soup.select_one('.title_link')or soup.select_one('[itemprop="name"]')
  name=name.get_text(strip=True)if name else 'Unknown'
  package=soup.select_one('span:-soup-contains("Package name")')or soup.select_one('[class*="package"]')
  package=package.get_text(strip=True).replace('Package name:','').strip()if package else 'unknown'
  version=soup.select_one('[itemprop="version"]')or soup.select_one('.version')or soup.select_one('span:-soup-contains("Version")')
  version=version.get_text(strip=True).replace('Version','').strip()if version else '1.0'
  size=soup.select_one('[itemprop="fileSize"]')or soup.select_one('span:-soup-contains("MB")')or soup.select_one('span:-soup-contains("KB")')
  size=size.get_text(strip=True)if size else 'Unknown'
  last_update=soup.select_one('[itemprop="datePublished"]')or soup.select_one('p:-soup-contains("Update on")')
  last_update=last_update.get_text(strip=True).replace('Update on','').strip()if last_update else None
  description=soup.select_one('[itemprop="description"]')or soup.select_one('.description')or soup.select_one('div[class*="content"]')
  description=description.get_text(strip=True)[:500]if description else 'لا يوجد وصف متاح'
  image=soup.select_one('[itemprop="image"]')or soup.select_one('img.icon')or soup.select_one('img[src*="icon"]')
  image=image.get('src')if image else None
  if image and not image.startswith('http'):
   image=urljoin(url,image)
  return{'name':name,'package':package,'version':version,'size':size,'lastUpdate':last_update,'description':description,'image':image}
 except Exception as e:
  print(f"❌ خطأ في استخراج البيانات | Data extraction error: {str(e)}")
  return None
# ════════════════════════════════════════════════════════════════════════════
# 🔗 دالة الحصول على رابط التحميل | Get Download Link Function
# ════════════════════════════════════════════════════════════════════════════
def get_download_link(url):
 """
 الحصول على رابط التحميل المباشر
 Get direct download link
 Args:
 url (str): رابط صفحة التطبيق | Application page URL
 Returns:
 str: رابط التحميل المباشر | Direct download link
 """
 try:
  print(f"🔗 الحصول على رابط التحميل | Getting download link from: {url}")
  response=scraper.get(url,timeout=30)
  if response.status_code!=200:
   return None
  soup=BeautifulSoup(response.text,'html.parser')
  download_btn=soup.select_one('a[href*="download"]')or soup.select_one('.download-btn')or soup.select_one('a:-soup-contains("Download")')or soup.select_one('[class*="download"]')
  if not download_btn:
   download_page=url+'/download'if not url.endswith('/download')else url
  else:
   download_page=download_btn.get('href')
   if download_page and not download_page.startswith('http'):
    download_page=urljoin(url,download_page)
  print(f"📄 صفحة التحميل | Download page: {download_page}")
  response=scraper.get(download_page,timeout=30)
  if response.status_code!=200:
   return None
  soup=BeautifulSoup(response.text,'html.parser')
  direct_link=soup.select_one('a[href*="download.apkpure"]')or soup.select_one('a[href*="d.apkpure"]')or soup.select_one('a[href$=".apk"]')or soup.select_one('a[href$=".xapk"]')or soup.select_one('#download_link')
  if direct_link and direct_link.get('href'):
   link=direct_link.get('href')
   if not link.startswith('http'):
    link=urljoin(download_page,link)
   return link
  scripts=soup.find_all('script')
  for script in scripts:
   if script.string:
    matches=re.findall(r'(https?://[^\s"\']+\.(?:apk|xapk))',script.string)
    if matches:
     return matches[0]
  package_match=re.search(r'/([^/]+)(?:/download)?$',url.rstrip('/'))
  if package_match:
   package=package_match.group(1)
   possible_links=[f"https://download.apkpure.com/b/APK/{package}?version=latest",f"https://d.apkpure.com/b/APK/{package}",f"https://download.apkpure.net/apk/{package}"]
   for link in possible_links:
    try:
     test_response=scraper.head(link,timeout=10,allow_redirects=True)
     if test_response.status_code==200:
      return test_response.url
    except:
     continue
  return None
 except Exception as e:
  print(f"❌ خطأ في الحصول على رابط التحميل | Download link error: {str(e)}")
  return None
# ════════════════════════════════════════════════════════════════════════════
# 🧪 اختبار السكرابر | Test Scraper
# ════════════════════════════════════════════════════════════════════════════
if __name__=='__main__':
 print('════════════════════════════════════════════════════════════════')
 print('🧪 اختبار السكرابر | Testing Scraper')
 print('════════════════════════════════════════════════════════════════')
 test_query='whatsapp'
 result=scrapeApp(test_query)
 print('\n📋 النتيجة | Result:')
 print(json.dumps(result,indent=2,ensure_ascii=False))
 print('════════════════════════════════════════════════════════════════')
