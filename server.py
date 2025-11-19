# ════════════════════════════════════════════════════════════════════════════
# 🌐 Flask Server - Python Middleware for APKPure Bot
# ════════════════════════════════════════════════════════════════════════════
# المطور: @omarxarafp | instagram.com/omarxarafp
# الوظيفة: سيرفر وسيط يستقبل طلبات البحث ويستدعي السكرابر
# Function: Middleware server receiving search requests and calling scraper
# ════════════════════════════════════════════════════════════════════════════

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os

# استيراد السكرابر من ملف APKPURE.PY
# Import scraper from APKPURE.PY file
try:
    from apkpure import scrapeApp
except ImportError:
    print("❌ Error: Cannot import scrapeApp from apkpure.py")
    print("❌ Make sure apkpure.py exists in the same directory")
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════════════
# ⚙️ إعداد Flask App | Flask App Configuration
# ════════════════════════════════════════════════════════════════════════════
app = Flask(__name__)
CORS(app)  # تفعيل CORS للسماح بالطلبات من أي مصدر | Enable CORS for cross-origin requests

# تكوين نظام السجلات | Configure logging system
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# 🏠 نقطة نهاية الصفحة الرئيسية | Homepage Endpoint
# ════════════════════════════════════════════════════════════════════════════
@app.route('/', methods=['GET'])
def home():
    """
    صفحة رئيسية بسيطة للتحقق من تشغيل السيرفر
    Simple homepage to verify server is running
    """
    return jsonify({
        'status': 'online',
        'service': 'APKPure WhatsApp Bot Server',
        'version': '1.0.0',
        'developer': '@omarxarafp',
        'instagram': 'instagram.com/omarxarafp',
        'endpoints': {
            '/search': 'POST - Search and download APK/XAPK files'
        }
    }), 200

# ════════════════════════════════════════════════════════════════════════════
# 🔍 نقطة نهاية البحث | Search Endpoint
# ════════════════════════════════════════════════════════════════════════════
@app.route('/search', methods=['POST'])
def search():
    """
    نقطة النهاية الرئيسية للبحث عن التطبيقات
    Main endpoint for searching applications
    
    Expected JSON body:
    {
        "query": "application_name"
    }
    
    Returns:
    {
        "success": true/false,
        "name": "App Name",
        "package": "com.app.package",
        "version": "1.0.0",
        "size": "50 MB",
        "description": "App description...",
        "image": "https://...",
        "downloadUrl": "https://...",
        "lastUpdate": "2025-01-01"
    }
    """
    try:
        # التحقق من وجود البيانات في الطلب | Verify request contains data
        if not request.is_json:
            logger.warning("⚠️ Request is not JSON")
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        # الحصول على البيانات | Get request data
        data = request.get_json()
        query = data.get('query', '').strip()
        
        # التحقق من وجود query | Verify query exists
        if not query:
            logger.warning("⚠️ Empty query received")
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 400
        
        logger.info(f"🔍 Searching for: {query}")
        
        # ════════════════════════════════════════════════════════════════════════
        # 🚀 استدعاء السكرابر | Call Scraper Function
        # ════════════════════════════════════════════════════════════════════════
        result = scrapeApp(query)
        
        # التحقق من نجاح السكراب | Verify scraping success
        if result.get('success'):
            logger.info(f"✅ Successfully found: {result.get('name')}")
            return jsonify(result), 200
        else:
            logger.warning(f"❌ Failed to find: {query}")
            return jsonify(result), 404
    
    except Exception as e:
        # معالجة الأخطاء غير المتوقعة | Handle unexpected errors
        logger.error(f"❌ Server error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

# ════════════════════════════════════════════════════════════════════════════
# 🏥 نقطة نهاية فحص الصحة | Health Check Endpoint
# ════════════════════════════════════════════════════════════════════════════
@app.route('/health', methods=['GET'])
def health():
    """
    نقطة نهاية للتحقق من صحة السيرفر
    Endpoint to check server health
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running perfectly'
    }), 200

# ════════════════════════════════════════════════════════════════════════════
# 🎬 نقطة البداية | Entry Point
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('════════════════════════════════════════════════════════════════')
    print('🌐 Starting APKPure Bot Flask Server...')
    print('🌐 جاري تشغيل سيرفر APKPure Bot...')
    print('════════════════════════════════════════════════════════════════')
    print('📡 Server running on: http://localhost:3000')
    print('🔍 Search endpoint: http://localhost:3000/search')
    print('🏥 Health check: http://localhost:3000/health')
    print('════════════════════════════════════════════════════════════════')
    print('✅ Server is ready to receive requests!')
    print('✅ السيرفر جاهز لاستقبال الطلبات!')
    print('════════════════════════════════════════════════════════════════')
    
    # تشغيل السيرفر | Run server
    # للإنتاج استخدم gunicorn أو uwsgi | For production use gunicorn or uwsgi
    app.run(
        host='0.0.0.0',  # الاستماع على جميع الواجهات | Listen on all interfaces
        port=3000,       # المنفذ | Port
        debug=False,     # تعطيل وضع التطوير للأداء | Disable debug for performance
        threaded=True    # تفعيل المعالجة المتعددة | Enable multi-threading
    )
