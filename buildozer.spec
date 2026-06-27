[app]
title = Metronoming
package.name = metronoming
package.domain = example.metronoming
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,MODIFY_AUDIO_SETTINGS
android.api = 31
android.minapi = 24
android.ndk = 25c
android.logcat_filters = *:S python:D
p4a.bootstrap = sdl2
