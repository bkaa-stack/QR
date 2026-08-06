"""
QR Code & Barcode Scanner - Android App
ZXing Android Embedded (bundle trong APK) + luu data JSON.
Build: buildozer android debug
"""
 
import datetime
import json
import os
import threading
 
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
 
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
                text: "San sang quet"
                font_size: "14sp"
                color: 0.46, 0.46, 0.46, 1
                halign: "center"
                text_size: self.size
 
            Label:
                text: "Ho tro: QR Code, EAN-13, Code128, UPC-A, v.v."
                font_size: "12sp"
                color: 0.2, 0.6, 0.2, 1
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
 
 
def _data_path():
    """Duong dan file luu data JSON."""
    if platform == "android":
        try:
            from android.storage import app_storage_path
            base = app_storage_path()
        except Exception:
            base = "/sdcard"
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "qrscanner_data.json")
 
 
class QRScanApp(App):
    def build(self):
        self.scan_data = []
        self.seen_qrs  = set()
        return Builder.load_string(KV)
 
    def on_start(self):
        # Dang ky callback nhan ket qua tu ZXing - hoan toan lazy
        if platform == "android":
            try:
                from android.activity import bind as android_bind
                android_bind(on_activity_result=self._on_scan_result)
            except Exception:
                pass
        # Load data da luu
        self._load_data()
 
    # ── Persistence ───────────────────────────────────────────────────────────
    def _load_data(self):
        path = _data_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for d in saved:
                self.scan_data.append(d)
                self.seen_qrs.add(d["qr"])
                self._add_item_to_list(d)
            count = len(self.scan_data)
            if count:
                self.root.get_screen("list").ids.count_label.text = f"{count} ma"
                self._update_status(f"Da tai {count} ma tu lan truoc")
        except Exception:
            pass
 
    def _save_data(self):
        try:
            path = _data_path()
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.scan_data, f, ensure_ascii=False)
        except Exception:
            pass
 
    # ── Navigation ────────────────────────────────────────────────────────────
    def go_list(self):
        self.root.current = "list"
 
    def go_scan(self):
        self.root.current = "scan"
 
    # ── Scan via direct Intent toi CaptureActivity ───────────────────────────
    # Request code rieng de nhan dung ket qua
    SCAN_REQUEST_CODE = 49374
 
    def start_scan(self):
        if platform != "android":
            self._show_manual_input()
            return
        # startActivityForResult phai chay tren Android UI thread
        try:
            from android.runnable import run_on_ui_thread
        except Exception:
            self._update_status("Loi: khong load duoc android.runnable")
            return
 
        @run_on_ui_thread
        def _do_scan():
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent         = autoclass("android.content.Intent")
                activity       = PythonActivity.mActivity
                intent         = Intent()
                intent.setClassName(
                    activity,
                    "com.journeyapps.barcodescanner.CaptureActivity")
                activity.startActivityForResult(intent, self.SCAN_REQUEST_CODE)
            except Exception as e:
                Clock.schedule_once(
                    lambda _: self._update_status(f"Loi: {e}"), 0)
 
        _do_scan()
 
    def _on_scan_result(self, request_code, result_code, intent):
        """Callback tu android.activity.bind - nhan ket qua ZXing."""
        if request_code != self.SCAN_REQUEST_CODE:
            return
        if result_code != -1 or intent is None:
            return
        try:
            content = intent.getStringExtra("SCAN_RESULT")
            fmt     = intent.getStringExtra("SCAN_RESULT_FORMAT") or "QRCODE"
            if content:
                Clock.schedule_once(
                    lambda _: self._register_code(content, fmt), 0)
        except Exception as e:
            Clock.schedule_once(
                lambda _: self._update_status(f"Loi doc ket qua: {e}"), 0)
 
    # ── Desktop fallback ──────────────────────────────────────────────────────
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
        entry = {"index": idx, "type": code_type, "qr": data, "time": now}
        self.scan_data.append(entry)
        self._add_item_to_list(entry)
        self._update_status(f"Da quet {idx} ma")
        self._save_data()
 
    def _add_item_to_list(self, d):
        idx  = d["index"]
        item = QRItem(
            idx_text  = str(idx),
            qr_text   = d["qr"][:50] + ("..." if len(d["qr"]) > 50 else ""),
            time_text = d["time"],
            bg_color  = [0.89, 0.95, 1, 1] if idx % 2 == 0 else [1, 1, 1, 1])
        self.root.get_screen("list").ids.qr_list.add_widget(item)
        self.root.get_screen("list").ids.count_label.text = f"{len(self.scan_data)} ma"
 
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
        self._save_data()
 
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
