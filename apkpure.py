#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكرابر احترافي للتطبيقات من Google Play Store
يدعم البحث بالعربية والإنجليزية، تحميل APK/XAPK، واستخراج ملفات OBB تلقائياً
"""

import requests
import argparse
import json
import os
import time
import zipfile
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_play_scraper import app as gplay_app, search as gplay_search
from bs4 import BeautifulSoup
from urllib.parse import quote

# ===================== الإعدادات الثابتة =====================

# Headers لتجنب الحظر
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

# مجلدات التحميل
DOWNLOADS_DIR = Path("downloads")
OBB_DIR = DOWNLOADS_DIR / "obb"
LOGS_DIR = Path("logs")

# إعدادات إعادة المحاولة
MAX_RETRIES = 5
RETRY_DELAY = 3
TIMEOUT = 30

# قفل للكتابة
log_lock = Lock()


# ===================== وظائف مساعدة =====================

def create_directories():
    """إنشاء المجلدات المطلوبة"""
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    OBB_DIR.mkdir(exist_ok=True, parents=True)
    LOGS_DIR.mkdir(exist_ok=True)


def sanitize_filename(filename: str, package_name: Optional[str] = None) -> str:
    """تنظيف اسم الملف من الرموز المحجوزة"""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\x00']
    cleaned = filename
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
    
    cleaned = '_'.join(cleaned.split())
    while '__' in cleaned:
        cleaned = cleaned.replace('__', '_')
    cleaned = cleaned.strip('_')
    
    if not cleaned or len(cleaned) < 1:
        if package_name:
            cleaned = package_name.replace('.', '_')
        else:
            cleaned = 'app'
    
    windows_reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 
                       'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                       'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 
                       'LPT6', 'LPT7', 'LPT8', 'LPT9']
    if cleaned.upper() in windows_reserved:
        cleaned = f"{cleaned}_app"
    
    max_length = 100
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip('_')
    
    return cleaned


def search_app(query: str) -> Optional[Dict]:
    """البحث عن تطبيق في Google Play - محسّن للبحث العربي"""
    # إذا كان الإدخال package name مباشرة
    if '.' in query and ' ' not in query and not any(c in query for c in ['/', '\\', '?']):
        print(f"✓ تم اكتشاف package name: {query}")
        try:
            app_info = gplay_app(query, lang='ar', country='us')
            return app_info
        except:
            try:
                app_info = gplay_app(query, lang='en', country='us')
                return app_info
            except:
                print(f"❌ فشل جلب معلومات التطبيق: {query}")
                return None
    
    print(f"🔍 البحث عن: {query}")
    
    # استراتيجيات بحث متعددة
    search_strategies = [
        {'lang': 'ar', 'country': 'sa'},  # السعودية بالعربية
        {'lang': 'ar', 'country': 'ae'},  # الإمارات بالعربية
        {'lang': 'ar', 'country': 'eg'},  # مصر بالعربية
        {'lang': 'ar', 'country': 'us'},  # أمريكا بالعربية
        {'lang': 'en', 'country': 'us'},  # أمريكا بالإنجليزية
        {'lang': 'en', 'country': 'gb'},  # بريطانيا بالإنجليزية
    ]
    
    results = None
    for strategy in search_strategies:
        try:
            results = gplay_search(query, **strategy, n_hits=10)
            if results:
                print(f"✓ تم العثور على نتائج ({strategy['lang']}/{strategy['country']})")
                break
        except:
            continue
    
    if not results:
        print(f"❌ لا توجد نتائج للبحث: {query}")
        return None
    
    try:
        # أخذ أول نتيجة
        first_result = results[0]
        package_name = first_result['appId']
        
        # جلب معلومات التطبيق الكاملة بالعربية أولاً
        try:
            app_info = gplay_app(package_name, lang='ar', country='sa')
        except:
            try:
                app_info = gplay_app(package_name, lang='ar', country='us')
            except:
                app_info = gplay_app(package_name, lang='en', country='us')
        
        print(f"✓ تم العثور على: {app_info['title']} ({package_name})")
        
        return app_info
        
    except Exception as e:
        print(f"❌ خطأ في البحث: {str(e)}")
        return None


def get_apkcombo_xapk_link(package_name: str) -> Optional[str]:
    """الحصول على رابط XAPK من APKCombo"""
    try:
        print(f"🔗 البحث عن XAPK في APKCombo...")
        
        # محاولة الحصول على XAPK
        url = f"https://apkcombo.com/{package_name}/download/xapk"
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # البحث عن رابط التحميل
            download_btn = soup.select_one('a.variant, a[href*="download"]')
            
            if download_btn:
                download_page = download_btn.get('href')
                if download_page and isinstance(download_page, str):
                    if not download_page.startswith('http'):
                        download_page = f"https://apkcombo.com{download_page}"
                    
                    # الحصول على الرابط النهائي
                    resp2 = requests.get(download_page, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
                    soup2 = BeautifulSoup(resp2.text, 'html.parser')
                    
                    direct_link = soup2.select_one('a#download-link, a[href*=".xapk"]')
                    if direct_link:
                        final_url = direct_link.get('href')
                        if final_url and isinstance(final_url, str):
                            print(f"✓ تم العثور على رابط XAPK")
                            return final_url
        
        return None
        
    except Exception as e:
        print(f"⚠️  فشل البحث عن XAPK: {str(e)}")
        return None


def get_apkcombo_apk_link(package_name: str) -> Optional[str]:
    """الحصول على رابط APK من APKCombo"""
    try:
        print(f"🔗 البحث عن APK في APKCombo...")
        
        url = f"https://apkcombo.com/{package_name}/download/apk"
        
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_button = soup.select_one('a.variant')
        if not download_button:
            download_button = soup.select_one('a[href*="download"]')
        
        if download_button:
            download_page = download_button.get('href')
            if download_page and isinstance(download_page, str):
                if not download_page.startswith('http'):
                    download_page = f"https://apkcombo.com{download_page}"
                
                response2 = requests.get(download_page, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                
                direct_link = soup2.select_one('a#download-link')
                if direct_link:
                    final_url = direct_link.get('href')
                    if final_url and isinstance(final_url, str):
                        print(f"✓ تم العثور على رابط APK")
                        return final_url
        
        return None
        
    except Exception as e:
        print(f"⚠️  فشل APKCombo: {str(e)}")
        return None


def get_apkpure_download_link(package_name: str, prefer_xapk: bool = False) -> Optional[Tuple[str, str]]:
    """الحصول على رابط تحميل من APKPure - يدعم XAPK"""
    try:
        print(f"🔗 البحث في APKPure...")
        
        # محاولة الروابط المباشرة
        urls_to_try = []
        
        if prefer_xapk:
            # محاولة XAPK أولاً للألعاب
            urls_to_try.extend([
                (f"https://d.apkpure.com/b/XAPK/{package_name}?version=latest", 'xapk'),
                (f"https://d.apkpure.com/b/APK/{package_name}?version=latest", 'apk'),
            ])
        else:
            urls_to_try.extend([
                (f"https://d.apkpure.com/b/APK/{package_name}?version=latest", 'apk'),
                (f"https://d.apkpure.com/b/XAPK/{package_name}?version=latest", 'xapk'),
            ])
        
        for url, file_type in urls_to_try:
            try:
                response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    print(f"✓ تم العثور على رابط {file_type.upper()}")
                    return (response.url, file_type)
            except:
                continue
        
        return None
        
    except Exception as e:
        print(f"⚠️  فشل APKPure: {str(e)}")
        return None


def download_file(url: str, filename: str, desc: str = "تحميل") -> bool:
    """تحميل ملف مع شريط تقدم"""
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, tqdm(
            desc=desc,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            ncols=80,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]'
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في التحميل: {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)
        return False


def extract_obb_files(archive_path: str, package_name: str) -> bool:
    """استخراج ملفات OBB من XAPK - محسّن"""
    try:
        if not zipfile.is_zipfile(archive_path):
            return True
        
        print(f"📂 فحص محتويات الأرشيف...")
        
        obb_target_dir = OBB_DIR / package_name
        obb_target_dir.mkdir(exist_ok=True, parents=True)
        
        obb_found = False
        apk_found = False
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            
            # البحث عن ملفات OBB
            obb_files = [f for f in all_files if f.endswith('.obb')]
            
            # البحث عن ملفات APK داخل XAPK
            apk_files = [f for f in all_files if f.endswith('.apk') and not f.startswith('__')]
            
            if obb_files:
                print(f"✓ تم العثور على {len(obb_files)} ملف OBB")
                
                for obb_file in obb_files:
                    obb_filename = os.path.basename(obb_file)
                    target_path = obb_target_dir / obb_filename
                    
                    print(f"  📥 استخراج: {obb_filename}")
                    
                    with zip_ref.open(obb_file) as source, open(target_path, 'wb') as target:
                        file_size = zip_ref.getinfo(obb_file).file_size
                        
                        with tqdm(
                            total=file_size,
                            unit='B',
                            unit_scale=True,
                            desc=f"  {obb_filename[:30]}...",
                            ncols=80,
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}'
                        ) as pbar:
                            while True:
                                chunk = source.read(8192)
                                if not chunk:
                                    break
                                target.write(chunk)
                                pbar.update(len(chunk))
                    
                    obb_found = True
                
                print(f"✅ تم استخراج ملفات OBB إلى: {obb_target_dir}")
            else:
                print(f"ℹ️  لا توجد ملفات OBB في هذا الأرشيف")
            
            # استخراج APK الرئيسي إذا كان موجوداً
            if apk_files:
                main_apk = apk_files[0]  # أخذ أول APK
                apk_filename = os.path.basename(main_apk)
                apk_target = DOWNLOADS_DIR / f"{package_name}_main.apk"
                
                print(f"  📥 استخراج APK الرئيسي: {apk_filename}")
                
                with zip_ref.open(main_apk) as source, open(apk_target, 'wb') as target:
                    file_size = zip_ref.getinfo(main_apk).file_size
                    
                    with tqdm(
                        total=file_size,
                        unit='B',
                        unit_scale=True,
                        desc=f"  {apk_filename[:30]}...",
                        ncols=80,
                        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}'
                    ) as pbar:
                        while True:
                            chunk = source.read(8192)
                            if not chunk:
                                break
                            target.write(chunk)
                            pbar.update(len(chunk))
                
                print(f"✅ تم استخراج APK إلى: {apk_target}")
                apk_found = True
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في استخراج الأرشيف: {str(e)}")
        return False


def save_log(app_info: Dict, success: bool, error: Optional[str] = None):
    """حفظ سجل التحميل"""
    log_file = LOGS_DIR / "download_log.json"
    
    log_entry = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'package': app_info.get('appId', app_info.get('package', 'unknown')),
        'name': app_info.get('title', app_info.get('name', 'unknown')),
        'version': app_info.get('version', 'unknown'),
        'success': success,
        'error': error
    }
    
    with log_lock:
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                pass
        
        logs.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)


def download_app(query: str, format_type: str = 'auto') -> bool:
    """تحميل تطبيق كامل - محسّن لـ XAPK"""
    print(f"\n{'='*60}")
    print(f"🚀 بدء تحميل: {query}")
    print(f"{'='*60}\n")
    
    # البحث عن التطبيق
    app_info = search_app(query)
    if not app_info:
        return False
    
    package_name = app_info['appId']
    app_name = sanitize_filename(app_info['title'], package_name)
    version = app_info.get('version', 'latest')
    
    # تحديد ما إذا كان التطبيق لعبة كبيرة (يفضل XAPK)
    is_game = app_info.get('genre', '').lower() in ['game', 'games', 'ألعاب'] or \
              'game' in app_info.get('title', '').lower() or \
              'لعبة' in app_info.get('title', '')
    
    prefer_xapk = is_game or format_type == 'xapk'
    
    if prefer_xapk:
        print(f"🎮 تم اكتشاف لعبة - محاولة تحميل XAPK...")
    
    download_url = None
    file_type = 'apk'
    
    # محاولة 1: APKCombo XAPK (للألعاب)
    if prefer_xapk:
        download_url = get_apkcombo_xapk_link(package_name)
        if download_url:
            file_type = 'xapk'
    
    # محاولة 2: APKCombo APK
    if not download_url:
        download_url = get_apkcombo_apk_link(package_name)
        if download_url:
            file_type = 'apk'
    
    # محاولة 3: APKPure
    if not download_url:
        result = get_apkpure_download_link(package_name, prefer_xapk)
        if result:
            download_url, file_type = result
    
    if not download_url:
        print(f"❌ فشل الحصول على رابط تحميل من جميع المصادر")
        save_log(app_info, False, "لا يوجد رابط تحميل")
        print(f"\nℹ️  معلومات التطبيق:")
        print(f"   📦 الاسم: {app_info['title']}")
        print(f"   🔖 الإصدار: {version}")
        print(f"   📱 Package: {package_name}")
        print(f"   ⭐ التقييم: {app_info.get('score', 'N/A')}")
        print(f"   📥 التحميلات: {app_info.get('installs', 'N/A')}")
        print(f"\n💡 يمكنك تحميل التطبيق يدوياً من:")
        print(f"   🔗 https://apkcombo.com/{package_name}/download")
        print(f"   🔗 https://apkpure.com/{package_name}")
        return False
    
    filename = DOWNLOADS_DIR / f"{app_name}_v{version}.{file_type}"
    
    print(f"\n📥 التحميل: {app_info['title']} v{version}")
    print(f"📂 الملف: {filename}")
    print(f"📦 الصيغة: {file_type.upper()}")
    print(f"🔗 المصدر: {download_url[:60]}...\n")
    
    if not download_file(download_url, str(filename), desc=f"⬇️  {app_name[:30]}..."):
        save_log(app_info, False, "فشل التحميل")
        return False
    
    print(f"\n✅ تم التحميل بنجاح: {filename}")
    
    # استخراج محتويات XAPK (APK + OBB)
    if file_type == 'xapk':
        print(f"\n🎯 استخراج محتويات XAPK...")
        extract_obb_files(str(filename), package_name)
    
    save_log(app_info, True)
    
    print(f"\n{'='*60}")
    print(f"✅ اكتمل التحميل بنجاح!")
    if file_type == 'xapk':
        print(f"📁 ملفات OBB: {OBB_DIR / package_name}")
    print(f"{'='*60}\n")
    
    return True


def download_multiple_apps(queries: List[str], format_type: str = 'auto', max_threads: int = 3):
    """تحميل عدة تطبيقات"""
    print(f"\n{'='*60}")
    print(f"📋 تحميل {len(queries)} تطبيق باستخدام {max_threads} خيوط")
    print(f"{'='*60}\n")
    
    success_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_query = {
            executor.submit(download_app, query, format_type): query 
            for query in queries
        }
        
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"❌ خطأ في تحميل {query}: {str(e)}")
                failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 ملخص التحميل:")
    print(f"   ✅ نجح: {success_count}")
    print(f"   ❌ فشل: {failed_count}")
    print(f"   📁 المجلد: {DOWNLOADS_DIR.absolute()}")
    print(f"   📁 ملفات OBB: {OBB_DIR.absolute()}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='🚀 سكرابر احترافي للتطبيقات - APK/XAPK Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:
  %(prog)s واتساب
  %(prog)s "تيك توك"
  %(prog)s "ببجي" -f xapk
  %(prog)s whatsapp instagram pubg
  %(prog)s pubg freefire --threads 5
  %(prog)s --list apps.txt --threads 8
  %(prog)s com.whatsapp

الميزات:
✅ البحث بالعربية والإنجليزية (محسّن جداً)
✅ تحميل XAPK للألعاب تلقائياً
✅ استخراج ملفات OBB و APK من XAPK
✅ تحميل متعدد الخيوط
✅ حفظ سجل JSON

ملاحظة: 
- يبحث في Google Play ويحمل من APKCombo/APKPure
- يكتشف الألعاب تلقائياً ويحمل XAPK
        """
    )
    
    parser.add_argument(
        'apps',
        nargs='*',
        help='اسم التطبيق أو package name'
    )
    
    parser.add_argument(
        '--list', '-l',
        dest='app_list_file',
        help='ملف نصي يحتوي على قائمة تطبيقات'
    )
    
    parser.add_argument(
        '--format', '-f',
        dest='format_type',
        choices=['auto', 'apk', 'xapk'],
        default='auto',
        help='صيغة الملف (auto: تلقائي, apk, xapk)'
    )
    
    parser.add_argument(
        '--threads', '-t',
        dest='max_threads',
        type=int,
        default=3,
        help='عدد الخيوط للتحميل المتزامن (افتراضي: 3)'
    )
    
    args = parser.parse_args()
    
    create_directories()
    
    apps_to_download = []
    
    if args.apps:
        apps_to_download.extend(args.apps)
    
    if args.app_list_file:
        if os.path.exists(args.app_list_file):
            with open(args.app_list_file, 'r', encoding='utf-8') as f:
                file_apps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                apps_to_download.extend(file_apps)
        else:
            print(f"❌ الملف غير موجود: {args.app_list_file}")
            return
    
    if not apps_to_download:
        parser.print_help()
        print("\n❌ خطأ: يجب تحديد تطبيق واحد على الأقل للتحميل")
        return
    
    apps_to_download = list(dict.fromkeys(apps_to_download))
    
    if len(apps_to_download) == 1:
        download_app(apps_to_download[0], args.format_type)
    else:
        download_multiple_apps(apps_to_download, args.format_type, args.max_threads)


if __name__ == '__main__':
    main()
