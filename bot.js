// ════════════════════════════════════════════════════════════════════════════
// 🤖 APKPure WhatsApp Bot - Professional Android Apps Downloader
// ════════════════════════════════════════════════════════════════════════════
// المطور: @omarxarafp | instagram.com/omarxarafp
// الإصدار: 1.0.0 | تاريخ: 2025
// ════════════════════════════════════════════════════════════════════════════

import {makeWASocket,DisconnectReason,useMultiFileAuthState,fetchLatestBaileysVersion,makeCacheableSignalKeyStore} from '@whiskeysockets/baileys';
import pino from 'pino';
import axios from 'axios';
import PQueue from 'p-queue';
import fs from 'fs-extra';
import path from 'path';
import {fileURLToPath} from 'url';

// ════════════════════════════════════════════════════════════════════════════
// 📁 إعداد المسارات والمتغيرات الأساسية | Setup Paths & Basic Variables
// ════════════════════════════════════════════════════════════════════════════
const __filename=fileURLToPath(import.meta.url);
const __dirname=path.dirname(__filename);
const AUTH_DIR='./auth_info'; // مجلد حفظ الجلسة | Session folder
const DOWNLOADS_DIR='./downloads'; // مجلد التحميلات المؤقت | Temp downloads folder
const SERVER_URL='http://localhost:3000/search'; // رابط السيرفر الوسيط | Python server URL
const SIGNATURE='━━━━━━━━━━━━━━━━━\nتابعني على إنستغرام ❤️\ninstagram.com/omarxarafp\n━━━━━━━━━━━━━━━━━'; // التوقيع في نهاية كل رسالة | Signature footer

// ════════════════════════════════════════════════════════════════════════════
// 🎯 إنشاء قائمة انتظار للطلبات | Create Request Queue
// ════════════════════════════════════════════════════════════════════════════
// قائمة انتظار ذكية تتعامل مع 15 طلب في نفس الوقت لتجنب الضغط الزائد
// Smart queue handling 15 concurrent requests to avoid overload
const requestQueue=new PQueue({concurrency:15,timeout:120000,throwOnTimeout:true});

// ════════════════════════════════════════════════════════════════════════════
// 🚀 دالة بدء البوت الرئيسية | Main Bot Initialization Function
// ════════════════════════════════════════════════════════════════════════════
async function startBot(){
console.log('════════════════════════════════════════════════════════════════');
console.log('🚀 جاري بدء بوت APKPure WhatsApp Bot...');
console.log('🚀 Starting APKPure WhatsApp Bot...');
console.log('════════════════════════════════════════════════════════════════');
// إنشاء مجلدات ضرورية إن لم تكن موجودة | Create necessary folders if not exist
await fs.ensureDir(AUTH_DIR);
await fs.ensureDir(DOWNLOADS_DIR);
// تحميل بيانات الجلسة من المجلد | Load session data from folder
const {state,saveCreds}=await useMultiFileAuthState(AUTH_DIR);
// جلب أحدث إصدار من Baileys | Fetch latest Baileys version
const {version}=await fetchLatestBaileysVersion();
console.log(`✅ استخدام إصدار Baileys: ${version.join('.')}`);
// ════════════════════════════════════════════════════════════════════════════
// 🔌 إنشاء اتصال WhatsApp | Create WhatsApp Connection
// ════════════════════════════════════════════════════════════════════════════
const sock=makeWASocket({
version,
logger:pino({level:'silent'}), // تعطيل السجلات المزعجة | Disable annoying logs
printQRInTerminal:false, // منع طباعة QR (نستخدم Pairing Code فقط) | Prevent QR printing
browser:['Windlws','Chrome','1.0.0'], // معلومات المتصفح | Browser info
auth:{
creds:state.creds,
keys:makeCacheableSignalKeyStore(state.keys,pino({level:'silent'}))
},
generateHighQualityLinkPreview:true, // معاينات الروابط عالية الجودة | High quality link previews
syncFullHistory:false, // عدم مزامنة السجل الكامل (توفير الموارد) | Don't sync full history
markOnlineOnConnect:true, // الظهور أونلاين عند الاتصال | Show online on connect
connectTimeoutMs:60000, // مهلة الاتصال 60 ثانية | Connection timeout
defaultQueryTimeoutMs:60000, // مهلة الاستعلام الافتراضية | Default query timeout
keepAliveIntervalMs:30000 // إرسال نبضة كل 30 ثانية | Keep alive pulse every 30s
});
// ════════════════════════════════════════════════════════════════════════════
// 🔐 معالج تحديث بيانات الاعتماد | Credentials Update Handler
// ════════════════════════════════════════════════════════════════════════════
sock.ev.on('creds.update',saveCreds);
// ════════════════════════════════════════════════════════════════════════════
// 🔗 معالج تحديث الاتصال | Connection Update Handler
// ════════════════════════════════════════════════════════════════════════════
sock.ev.on('connection.update',async(update)=>{
const{connection,lastDisconnect,qr}=update;
// إذا تم الاتصال بنجاح | If connected successfully
if(connection==='open'){
console.log('✅ تم الاتصال بواتساب بنجاح! | Connected to WhatsApp successfully!');
console.log('🤖 البوت جاهز لاستقبال الطلبات | Bot is ready to receive requests');
}
// إذا تم إغلاق الاتصال | If connection closed
if(connection==='close'){
const statusCode=(lastDisconnect?.error)?.output?.statusCode;
console.log('❌ تم قطع الاتصال | Connection closed:',lastDisconnect?.error?.message);
// إعادة الاتصال دائماً إلا في حالة تسجيل خروج صريح | Always reconnect except explicit logout
if(statusCode!==DisconnectReason.loggedOut){
console.log('🔄 جاري إعادة الاتصال... | Reconnecting...');
setTimeout(()=>startBot(),5000); // إعادة الاتصال بعد 5 ثواني | Reconnect after 5s
}else{
console.log('🚪 تم تسجيل الخروج | Logged out');
await fs.remove(AUTH_DIR); // حذف بيانات الجلسة | Delete session data
console.log('🔄 قم بإعادة تشغيل البوت للحصول على كود جديد | Restart bot for new pairing code');
}
}
// نظام Pairing Code (رمز الاقتران 6 أرقام) | Pairing Code System (6-digit code)
if(!sock.authState.creds.registered&&!connection){
console.log('📱 لم يتم تسجيل الدخول بعد | Not logged in yet');
console.log('📱 الرجاء إدخال رقم الهاتف (مع رمز الدولة بدون +) | Enter phone number (with country code, no +)');
console.log('📱 مثال | Example: 966501234567');
// في بيئة الإنتاج، استخدم readline أو متغيرات البيئة
// In production, use readline or environment variables
const phoneNumber=process.env.PHONE_NUMBER||''; // ضع رقمك هنا | Put your number here
if(phoneNumber){
try{
const code=await sock.requestPairingCode(phoneNumber);
console.log(`🔐 كود الاقتران | Pairing Code: ${code}`);
console.log('📱 أدخل هذا الكود في واتساب: الإعدادات > الأجهزة المرتبطة > ربط جهاز');
console.log('📱 Enter this code in WhatsApp: Settings > Linked Devices > Link a Device');
console.log('⏳ في انتظار الربط... البوت سيبقى يعمل | Waiting for pairing... Bot will keep running');
}catch(err){
console.error('❌ خطأ في طلب كود الاقتران | Error requesting pairing code:',err.message);
console.log('🔄 سيتم المحاولة مرة أخرى | Will retry...');
}
}
}
});
// ════════════════════════════════════════════════════════════════════════════
// 💬 معالج الرسائل الواردة | Incoming Messages Handler
// ════════════════════════════════════════════════════════════════════════════
sock.ev.on('messages.upsert',async({messages,type})=>{
if(type!=='notify')return; // تجاهل الرسائل غير المباشرة | Ignore non-direct messages
for(const msg of messages){
try{
// تجاهل رسائل البوت نفسه | Ignore bot's own messages
if(msg.key.fromMe)continue;
// استخراج نص الرسالة | Extract message text
const messageText=msg.message?.conversation||msg.message?.extendedTextMessage?.text||'';
const chatId=msg.key.remoteJid; // معرف المحادثة | Chat ID
// تجاهل الرسائل الفارغة | Ignore empty messages
if(!messageText.trim())continue;
console.log(`📩 رسالة جديدة من | New message from: ${chatId}`);
console.log(`📝 النص | Text: ${messageText}`);
// إضافة الطلب إلى قائمة الانتظار | Add request to queue
await requestQueue.add(async()=>{
await handleMessage(sock,chatId,messageText,msg);
});
}catch(err){
console.error('❌ خطأ في معالجة الرسالة | Error processing message:',err.message);
}
}
});
// ════════════════════════════════════════════════════════════════════════════
// ⚠️ معالج الأخطاء العامة | Global Error Handler
// ════════════════════════════════════════════════════════════════════════════
sock.ev.on('error',err=>{
console.error('❌ خطأ في البوت | Bot error:',err);
});
return sock;
}
// ════════════════════════════════════════════════════════════════════════════
// 💬 دالة معالجة الرسائل | Message Handler Function
// ════════════════════════════════════════════════════════════════════════════
async function handleMessage(sock,chatId,messageText,originalMsg){
const text=messageText.trim().toLowerCase();
try{
// ════════════════════════════════════════════════════════════════════════════
// 🏠 أمر البداية | Start Command
// ════════════════════════════════════════════════════════════════════════════
if(text==='/start'||text==='مرحبا'||text==='مرحبا'||text==='start'||text==='hi'||text==='hello'){
const welcomeMsg=`╔══════════════════════════╗
║  🤖 *أهلاً بك في بوت APKPure* 🤖  ║
╚══════════════════════════╝

📱 *مرحباً بك في أفضل بوت لتحميل تطبيقات الأندرويد!*

✨ *كيفية الاستخدام:*
فقط أرسل اسم التطبيق الذي تريده باللغة الإنجليزية

📋 *أمثلة:*
• whatsapp
• tiktok
• instagram
• capcut
• telegram
• facebook

⚡ *المميزات:*
✓ تحميل سريع وآمن 100%
✓ أحدث الإصدارات
✓ روابط مباشرة
✓ يدعم APK و XAPK
✓ خدمة 24/7

🎯 *جرب الآن!* اكتب اسم أي تطبيق وسأحمله لك فوراً 🚀

${SIGNATURE}`;
await sock.sendMessage(chatId,{text:welcomeMsg},{quoted:originalMsg});
return;
}
// ════════════════════════════════════════════════════════════════════════════
// 🔍 البحث عن التطبيق | Search for App
// ════════════════════════════════════════════════════════════════════════════
// إرسال رسالة انتظار | Send waiting message
await sock.sendMessage(chatId,{text:`🔍 *جاري البحث عن:* ${messageText}\n⏳ الرجاء الانتظار...\n\n${SIGNATURE}`},{quoted:originalMsg});
// إضافة رد فعل للرسالة الأصلية | Add reaction to original message
await sock.sendMessage(chatId,{react:{text:'⏳',key:originalMsg.key}});
// إرسال الطلب إلى السيرفر الوسيط | Send request to Python server
console.log(`🌐 إرسال طلب إلى السيرفر | Sending request to server: ${messageText}`);
const response=await axios.post(SERVER_URL,{query:messageText},{timeout:120000,headers:{'Content-Type':'application/json'}});
const data=response.data;
// التحقق من نجاح الطلب | Check if request successful
if(!data.success){
await sock.sendMessage(chatId,{react:{text:'❌',key:originalMsg.key}});
await sock.sendMessage(chatId,{text:`😔 *عذراً، لم أجد التطبيق*\n\n❌ ${data.error||'حاول مرة أخرى'}\n\n💡 *نصيحة:*\n• تأكد من كتابة الاسم بالإنجليزية\n• تحقق من الإملاء\n• جرب اسم مختلف للتطبيق\n\n${SIGNATURE}`},{quoted:originalMsg});
return;
}
// ════════════════════════════════════════════════════════════════════════════
// 📤 إرسال معلومات التطبيق | Send App Info
// ════════════════════════════════════════════════════════════════════════════
const infoMsg=`🟢 *تم العثور على التطبيق بنجاح!*

📱 *الاسم:* ${data.name}
📦 *الإصدار:* ${data.version}
📏 *الحجم:* ${data.size}
${data.lastUpdate?`✨ *آخر تحديث:* ${data.lastUpdate}\n`:''}
✏️ *الوصف:*
${data.description?data.description.substring(0,300)+'...':'غير متوفر'}

⬇️ *جاري تحميل الملف...*

${SIGNATURE}`;
// إرسال الرسالة مع صورة التطبيق إن وجدت | Send message with app image if available
if(data.image){
try{
const imageBuffer=await downloadFile(data.image);
await sock.sendMessage(chatId,{image:imageBuffer,caption:infoMsg},{quoted:originalMsg});
}catch(err){
console.error('⚠️ فشل تحميل الصورة | Failed to download image:',err.message);
await sock.sendMessage(chatId,{text:infoMsg},{quoted:originalMsg});
}
}else{
await sock.sendMessage(chatId,{text:infoMsg},{quoted:originalMsg});
}
// تغيير رد الفعل إلى تحميل | Change reaction to downloading
await sock.sendMessage(chatId,{react:{text:'⬇️',key:originalMsg.key}});
// ════════════════════════════════════════════════════════════════════════════
// 📥 تحميل وإرسال ملف APK/XAPK | Download & Send APK/XAPK File
// ════════════════════════════════════════════════════════════════════════════
console.log(`📥 جاري تحميل الملف | Downloading file: ${data.downloadUrl}`);
const fileBuffer=await downloadFile(data.downloadUrl);
// تحديد امتداد الملف | Determine file extension
const fileExt=data.downloadUrl.includes('.xapk')?'xapk':'apk';
const fileName=`${data.name.replace(/[^a-zA-Z0-9]/g,'_')}_v${data.version}_apkpure.com.${fileExt}`;
const filePath=path.join(DOWNLOADS_DIR,fileName);
// حفظ الملف مؤقتاً | Save file temporarily
await fs.writeFile(filePath,fileBuffer);
console.log(`💾 تم حفظ الملف | File saved: ${filePath}`);
// تحميل صورة التطبيق كـ thumbnail | Download app image as thumbnail
let thumbnail=null;
if(data.image){
try{
thumbnail=await downloadFile(data.image);
}catch(err){
console.error('⚠️ فشل تحميل thumbnail:',err.message);
}
}
// إرسال الملف كـ document | Send file as document
await sock.sendMessage(chatId,{
document:{url:filePath},
fileName:fileName,
mimetype:'application/vnd.android.package-archive',
jpegThumbnail:thumbnail,
caption:`✅ *تم التحميل بنجاح!*\n\n📱 *${data.name}*\n📦 *الإصدار:* ${data.version}\n📏 *الحجم:* ${data.size}\n\n${SIGNATURE}`
},{quoted:originalMsg});
// تغيير رد الفعل إلى نجاح | Change reaction to success
await sock.sendMessage(chatId,{react:{text:'✅',key:originalMsg.key}});
console.log(`✅ تم إرسال الملف بنجاح | File sent successfully: ${fileName}`);
// ════════════════════════════════════════════════════════════════════════════
// 🗑️ حذف الملف من المجلد | Delete File from Folder
// ════════════════════════════════════════════════════════════════════════════
try{
await fs.unlink(filePath);
console.log(`🗑️ تم حذف الملف من المجلد | File deleted: ${filePath}`);
}catch(err){
console.error('⚠️ فشل حذف الملف | Failed to delete file:',err.message);
}
}catch(err){
console.error('❌ خطأ في معالجة الطلب | Error processing request:',err.message);
await sock.sendMessage(chatId,{react:{text:'❌',key:originalMsg.key}});
await sock.sendMessage(chatId,{text:`❌ *حدث خطأ أثناء معالجة طلبك*\n\n🔧 ${err.message}\n\n💡 الرجاء المحاولة مرة أخرى\n\n${SIGNATURE}`},{quoted:originalMsg});
}
}
// ════════════════════════════════════════════════════════════════════════════
// 📥 دالة تحميل الملفات | File Download Function
// ════════════════════════════════════════════════════════════════════════════
async function downloadFile(url){
try{
const response=await axios.get(url,{responseType:'arraybuffer',timeout:300000,maxContentLength:500*1024*1024,maxBodyLength:500*1024*1024});
return Buffer.from(response.data);
}catch(err){
console.error(`❌ فشل تحميل الملف | Failed to download: ${url}`,err.message);
throw new Error('فشل تحميل الملف');
}
}
// ════════════════════════════════════════════════════════════════════════════
// 🎬 نقطة البداية | Entry Point
// ════════════════════════════════════════════════════════════════════════════
startBot().catch(err=>{
console.error('❌ فشل بدء البوت | Failed to start bot:',err);
process.exit(1);
});
// ════════════════════════════════════════════════════════════════════════════
// 🛡️ معالجات الإغلاق الآمن | Safe Shutdown Handlers
// ════════════════════════════════════════════════════════════════════════════
process.on('unhandledRejection',(err)=>{
console.error('❌ Unhandled Rejection:',err);
});
process.on('uncaughtException',(err)=>{
console.error('❌ Uncaught Exception:',err);
});
