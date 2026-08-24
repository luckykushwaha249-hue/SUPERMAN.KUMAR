[app]

title = SUPERMAN.KUMAR
package.name = supermankumar
package.domain = org.llbstudent

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy==2.3.0,pillow,plyer

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

# Sirf camera/storage chahiye - internet ki zaroorat nahi (OCR offline hai)
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Google ML Kit - on-device text recognition, bina API key ke
android.enable_androidx = True
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0

[buildozer]
log_level = 2
warn_on_root = 1
