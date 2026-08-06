"""
QR Code & Barcode Scanner - Android App
Dung Android Intent de quet QR/Barcode (ZXing app) + xuat Excel.
Build: buildozer android debug
"""
 
import datetime
import os
import threading
 
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
 
# Android imports - chi load khi chay tren Android
ANDROID_OK = False
if platform == "android":
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent         = autoclass("android.content.Intent")
        ANDROID_OK     = True
    except Exception:
        ANDROID_OK = False
 
KV = """
ScreenManager:
    ScanScreen:
        name: "scan"
    ListScreen:
        name: "list"
 
<ScanScreen>:
    BoxLayout:
        orientation: "vertical"
 
        BoxLayout:
            size_hint_y: None
            height: "56dp"
            padding: "12dp", "8dp"
            spacing: "8dp"
            canvas.before:
                Color:
                    rgba: 0.098, 0.463, 0.824, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "QR & Barcode Scanner"
                font_size: "18sp"
                bold: True
                color: 1, 1, 1, 1
            Button:
                text: "Danh sach"
                size_hint_x: None
                width: "110dp"
                background_color: 0.263, 0.627, 0.278, 1
                on_release: app.go_list()
 
        BoxLayout:
            orientation: "vertical"
            padding: "24dp"
            spacing: "16dp"
 
            Label:
                text: "Nhan nut de quet ma QR / Barcode"
                font_size: "16sp"
                color: 0.3, 0.3, 0.3, 1
                halign: "center"
                text_size: self.size
 
            Button:
                text: "QUET MA QR / BARCODE"
                font_size: "18sp"
                bold: True
                size_hint_y: None
                height: "80dp"
                background_color: 0.098, 0.463, 0.824, 1
                on_release: app.start_scan()
 
            Label:
                id: scan_status
                text: "Chua quet ma nao"
                font_size: "14sp"
                color: 0.46, 0.46, 0.46, 1
                halign: "center"
                text_size: self.size
 
            Label:
                text: "* Can cai ZXing Barcode Scanner tren dien thoai"
                font_size: "12sp"
                color: 0.7, 0.5, 0.1, 1
                halign: "center"
                text_size: self.size
 
<ListScreen>:
    BoxLayout:
        orientation: "vertical"
 
        BoxLayout:
            size_hint_y: None
            height: "56dp"
            padding: "8dp"
            spacing: "8dp"
            canvas.before:
                Color:
                    rgba: 0.098, 0.463, 0.824, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "< Quay lai"
                size_hint_x: None
                width: "90dp"
                background_color: 0, 0, 0, 0
                color: 1, 1, 1, 1
                on_release: app.go_scan()
            Label:
                text: "Danh sach QR"
                font_size: "18sp"
                bold: True
                color: 1, 1, 1, 1
            Button:
                text: "Xuat Excel"
                size_hint_x: None
                width: "110dp"
                background_color: 0.263, 0.627, 0.278, 1
                on_release: app.export_excel()
            Button:
                text: "Xoa het"
                size_hint_x: None
                width: "80dp"
                background_color: 0.898, 0.224, 0.208, 1
                on_release: app.clear_all()
 
        ScrollView:
            GridLayout:
                id: qr_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: "1dp"
                padding: "4dp"
 
        BoxLayout:
            size_hint_y: None
            height: "36dp"
            padding: "12dp", "4dp"
            canvas.before:
                Color:
                    rgba: 0.94, 0.94, 0.94, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                id: count_label
                text: "0 ma"
                color: 0.46, 0.46, 0.46, 1
                font_size: "13sp"
                halign: "left"
                text_size: self.size
 
<QRItem>:
    size_hint_y: None
    height: "52dp"
    padding: "10dp", "4dp"
    spacing: "8dp"
    canvas.before:
        Color:
            rgba: root.bg_color
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.idx_text
        size_hint_x: None
        width: "36dp"
        color: 0.098, 0.463, 0.824, 1
        bold: True
        font_size: "13sp"
        halign: "center"
        text_size: self.size
    Label:
        text: root.qr_text
        color: 0.13, 0.13, 0.13, 1
        font_size: "12sp"
        halign: "left"
        text_size: self.size
    Label:
        text: root.time_text
        size_hint_x: None
        width: "145dp"
        color: 0.46, 0.46, 0.46, 1
        font_size: "11sp"
        halign: "right"
        text_size: self.size
"""
 
 
class ScanScreen(Screen):
    pass
 
 
class ListScreen(Screen):
    pass
 
 
class QRItem(BoxLayout):
    idx_text  = StringProperty("")
    qr_text   = StringProperty("")
    time_text = StringProperty("")
    bg_color  = ListProperty([1, 1, 1, 1])
 
 
class QRScanApp(App):
    def build(self):
        self.scan_data = []
        self.seen_qrs  = set()
        return Builder.load_string(KV)
 
    def go_list(self):
        self.root.current = "list"
 
    def go_scan(self):
        self.root.current = "scan"
 
    # ── Scan via Android Intent (ZXing) ───────────────────────────────────────
    def start_scan(self):
        if not ANDROID_OK:
            self._show_manual_input()
            return
        try:
            activity = PythonActivity.mActivity
            intent   = Intent("com.google.zxing.client.android.SCAN")
            intent.putExtra("SCAN_MODE", "QR_CODE_MODE,PRODUCT_MODE")
            activity.startActivityForResult(intent, 0)
            activity.bind(on_activity_result=self._on_scan_result)
        except Exception as e:
            self._update_status(f"Loi: {e}\nCan cai ZXing Barcode Scanner")
 
    def _on_scan_result(self, requestCode, resultCode, data):
        RESULT_OK = -1
        if resultCode == RESULT_OK and data is not None:
            result = data.getStringExtra("SCAN_RESULT")
            fmt    = data.getStringExtra("SCAN_RESULT_FORMAT") or "QRCODE"
            if result:
                Clock.schedule_once(
                    lambda _: self._register_code(result, fmt), 0)
 
    # ── Desktop fallback: manual input popup ──────────────────────────────────
    def _show_manual_input(self):
        from kivy.uix.popup import Popup
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
 
        box = BoxLayout(orientation="vertical", padding=12, spacing=8)
        ti  = TextInput(hint_text="Nhap noi dung ma QR...",
                        multiline=False, size_hint_y=None, height="44dp")
        btn = Button(text="Them", size_hint_y=None, height="44dp",
                     background_color=(0.098, 0.463, 0.824, 1))
        box.add_widget(ti)
        box.add_widget(btn)
 
        popup = Popup(title="Nhap ma QR (test)",
                      content=box, size_hint=(0.9, 0.35))
 
        def _add(*_):
            if ti.text.strip():
                self._register_code(ti.text.strip(), "MANUAL")
            popup.dismiss()
 
        btn.bind(on_release=_add)
        ti.bind(on_text_validate=_add)
        popup.open()
 
    # ── Data ──────────────────────────────────────────────────────────────────
    def _register_code(self, data: str, code_type: str = "QRCODE"):
        if not data or data in self.seen_qrs:
            return
        self.seen_qrs.add(data)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        idx = len(self.scan_data) + 1
        self.scan_data.append({"index": idx, "type": code_type,
                                "qr": data, "time": now})
        self._update_status(f"Da quet {idx} ma")
 
        item = QRItem(
            idx_text  = str(idx),
            qr_text   = data[:50] + ("..." if len(data) > 50 else ""),
            time_text = now,
            bg_color  = [0.89, 0.95, 1, 1] if idx % 2 == 0 else [1, 1, 1, 1])
 
        self.root.get_screen("list").ids.qr_list.add_widget(item)
        self.root.get_screen("list").ids.count_label.text = f"{idx} ma"
 
    def _update_status(self, msg):
        try:
            self.root.get_screen("scan").ids.scan_status.text = msg
        except Exception:
            pass
 
    def clear_all(self):
        self.scan_data.clear()
        self.seen_qrs.clear()
        self.root.get_screen("list").ids.qr_list.clear_widgets()
        self.root.get_screen("list").ids.count_label.text = "0 ma"
        self._update_status("Chua quet ma nao")
 
    # ── Excel export ──────────────────────────────────────────────────────────
    def export_excel(self):
        if not self.scan_data:
            self._toast("Chua co du lieu.")
            return
        threading.Thread(target=self._write_excel, daemon=True).start()
 
    def _write_excel(self):
        try:
            from xlsx_writer import write_xlsx
        except Exception as e:
            Clock.schedule_once(
                lambda _: self._toast(f"Loi import xlsx_writer: {e}"), 0)
            return
 
        if platform == "android":
            try:
                from android.storage import primary_external_storage_path
                folder = os.path.join(primary_external_storage_path(), "Download")
            except Exception:
                folder = "/sdcard/Download"
        else:
            folder = os.path.expanduser("~")
 
        os.makedirs(folder, exist_ok=True)
        fname = f"QR_Scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path  = os.path.join(folder, fname)
 
        try:
            write_xlsx(path, self.scan_data)
            Clock.schedule_once(
                lambda _: self._toast(f"Da luu: {fname}"), 0)
        except Exception as ex:
            Clock.schedule_once(
                lambda _: self._toast(f"Loi: {ex}"), 0)
 
    def _toast(self, msg):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        p = Popup(title="Thong bao",
                  content=Label(text=msg, halign="center"),
                  size_hint=(0.85, 0.22), auto_dismiss=True)
        p.open()
        Clock.schedule_once(lambda _: p.dismiss(), 3)
 
 
if __name__ == "__main__":
    QRScanApp().run()
