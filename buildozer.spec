[app]
title = QR Scanner Excel
package.name = qrscannerexcel
package.domain = com.vero
 
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
 
version = 1.0.0
 
requirements = python3,kivy==2.3.0,kivymd==1.2.0,openpyxl,android
 
orientation = portrait
fullscreen = 0
 
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
 
android.allow_backup = True
 
[buildozer]
log_level = 2
warn_on_root = 1
