name: Build Android APK
 
on:
  push:
    branches: [ main, master ]
  workflow_dispatch:
 
jobs:
  build-apk:
    runs-on: ubuntu-22.04
    timeout-minutes: 90
 
    steps:
      - name: Checkout source
        uses: actions/checkout@v4
 
      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"
 
      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            git zip unzip wget \
            openjdk-17-jdk \
            build-essential ccache \
            libncurses5 libncurses5-dev \
            libffi-dev libssl-dev libbz2-dev zlib1g-dev \
            libsqlite3-dev libreadline-dev \
            autoconf automake libtool pkg-config lld
 
          sudo update-java-alternatives -s java-1.17.0-openjdk-amd64 2>/dev/null || true
          echo "JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> $GITHUB_ENV
          echo "/usr/lib/jvm/java-17-openjdk-amd64/bin" >> $GITHUB_PATH
 
      - name: Install Buildozer
        run: |
          pip install --upgrade pip wheel setuptools
          pip install buildozer cython
 
      - name: Configure pre-installed Android SDK for Buildozer
        run: |
          # GitHub Actions runner da co san Android SDK tai /usr/local/lib/android/sdk
          # Chi can tao symlink de Buildozer tim thay sdkmanager
          SDK=/usr/local/lib/android/sdk
 
          # Accept licenses
          yes | $SDK/cmdline-tools/latest/bin/sdkmanager --licenses 2>/dev/null || true
 
          # Cai build-tools neu chua co
          $SDK/cmdline-tools/latest/bin/sdkmanager \
            "build-tools;33.0.2" "platforms;android-33" 2>/dev/null || true
 
          # Tao cau truc thu muc Buildozer can
          BDIR=$HOME/.buildozer/android/platform
          mkdir -p $BDIR
 
          # Symlink SDK vao duong dan Buildozer mong doi
          ln -sfn $SDK $BDIR/android-sdk
 
          # Tao tools/bin/sdkmanager symlink (Buildozer tim o day)
          mkdir -p $BDIR/android-sdk/tools/bin
          ln -sf $SDK/cmdline-tools/latest/bin/sdkmanager \
                 $BDIR/android-sdk/tools/bin/sdkmanager
          ln -sf $SDK/cmdline-tools/latest/bin/avdmanager \
                 $BDIR/android-sdk/tools/bin/avdmanager
 
          echo "ANDROID_SDK_ROOT=$BDIR/android-sdk" >> $GITHUB_ENV
          echo "$SDK/cmdline-tools/latest/bin" >> $GITHUB_PATH
          echo "$SDK/platform-tools" >> $GITHUB_PATH
          echo "$SDK/build-tools/33.0.2" >> $GITHUB_PATH
 
      - name: Cache Android NDK r25b
        uses: actions/cache@v4
        with:
          path: ~/.buildozer/android/platform/android-ndk-r25b
          key: ndk-r25b-v3
 
      - name: Build APK
        run: |
          export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
          export PATH=$JAVA_HOME/bin:$PATH
          buildozer -v android debug 2>&1
 
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: QRScanner-APK
          path: bin/*.apk
          retention-days: 30
