[app]
title = QR Scanner Excel
package.name = qrscannerexcel
package.domain = com.vero
 
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
 
version = 1.0.0
 
requirements = python3,kivy,android
 
orientation = portrait
fullscreen = 0
 
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
 
android.allow_backup = True
 
# Bundle ZXing Android Embedded - khong can cai them app de quet
android.gradle_dependencies = com.journeyapps:zxing-android-embedded:4.3.0
 
# Khai bao CaptureActivity cua ZXing trong AndroidManifest
android.add_activities = com.journeyapps.barcodescanner.CaptureActivity
 
[buildozer]
log_level = 2
warn_on_root = 1
