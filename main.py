"""
QR Code Scanner & Excel Exporter – Android App (Kivy + KivyMD)
Build APK:  buildozer android debug
"""
 
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import platform
import datetime, os, threading
 
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
 
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_OK = True
except ImportError:
    OPENPYXL_OK = False
 
KV = """
ScreenManager:
    ScanScreen:
    ListScreen:
 
<ScanScreen>:
    name: "scan"
    MDBoxLayout:
        orientation: "vertical"
 
        MDTopAppBar:
            title: "QR Scanner"
            right_action_items:
                [["format-list-bulleted", lambda x: app.go_list()]]
            md_bg_color: app.theme_cls.primary_color
 
        # Camera preview
        ZBarCam:
            id: zbarcam
            on_symbols: app.on_qr_detected(*args)
 
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            padding: "8dp"
            spacing: "8dp"
 
            MDRaisedButton:
                text: "Xem danh sách"
                on_release: app.go_list()
                md_bg_color: app.theme_cls.primary_color
 
            MDLabel:
                id: scan_status
                text: "Chưa quét mã nào"
                halign: "center"
 
<ListScreen>:
    name: "list"
    MDBoxLayout:
        orientation: "vertical"
 
        MDTopAppBar:
            title: "Danh sách QR"
            left_action_items:
                [["arrow-left", lambda x: app.go_scan()]]
            right_action_items:
                [["microsoft-excel", lambda x: app.export_excel()],
                 ["delete-sweep", lambda x: app.clear_all()]]
            md_bg_color: app.theme_cls.primary_color
 
        ScrollView:
            MDList:
                id: qr_list
 
        MDBoxLayout:
            size_hint_y: None
            height: "40dp"
            padding: "8dp", "4dp"
 
            MDLabel:
                id: count_label
                text: "0 mã QR"
                halign: "left"
                theme_text_color: "Secondary"
"""
 
 
class ScanScreen(Screen):
    pass
 
 
class ListScreen(Screen):
    pass
 
 
class QRScanApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style     = "Light"
        self.scan_data  = []
        self.seen_qrs   = set()
        return Builder.load_string(KV)
 
    # ── Navigation ─────────────────────────────────────────────────────────
    def go_list(self):
        self.root.current = "list"
 
    def go_scan(self):
        self.root.current = "scan"
 
    # ── QR detected ────────────────────────────────────────────────────────
    def on_qr_detected(self, zbarcam, symbols):
        if not symbols:
            return
        for sym in symbols:
            self._register_qr(sym.data.decode("utf-8", errors="replace"))
 
    def _register_qr(self, data: str):
        if data in self.seen_qrs:
            return
        self.seen_qrs.add(data)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        idx = len(self.scan_data) + 1
        self.scan_data.append({"index": idx, "qr": data, "time": now})
 
        # Update scan status
        scan_lbl = self.root.get_screen("scan").ids.scan_status
        scan_lbl.text = f"Đã quét {idx} mã"
 
        # Add row to list
        from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
        item = TwoLineIconListItem(
            text=data[:60] + ("…" if len(data) > 60 else ""),
            secondary_text=now)
        icon = IconLeftWidget(icon="qrcode")
        item.add_widget(icon)
 
        qr_list = self.root.get_screen("list").ids.qr_list
        qr_list.add_widget(item)
 
        count_lbl = self.root.get_screen("list").ids.count_label
        count_lbl.text = f"{idx} mã QR"
 
        Snackbar(text=f"✓  {data[:40]}").open()
 
    # ── Clear all ──────────────────────────────────────────────────────────
    def clear_all(self):
        def _do(*_):
            self.scan_data.clear()
            self.seen_qrs.clear()
            self.root.get_screen("list").ids.qr_list.clear_widgets()
            self.root.get_screen("list").ids.count_label.text = "0 mã QR"
            self.root.get_screen("scan").ids.scan_status.text = "Chưa quét mã nào"
            if self._dialog:
                self._dialog.dismiss()
 
        self._dialog = MDDialog(
            title="Xác nhận",
            text="Xóa tất cả dữ liệu đã quét?",
            buttons=[
                MDFlatButton(text="HỦY",
                             on_release=lambda x: self._dialog.dismiss()),
                MDFlatButton(text="XÓA", on_release=_do),
            ])
        self._dialog.open()
 
    # ── Excel export ───────────────────────────────────────────────────────
    def export_excel(self):
        if not OPENPYXL_OK:
            Snackbar(text="Thiếu openpyxl!").open()
            return
        if not self.scan_data:
            Snackbar(text="Chưa có dữ liệu.").open()
            return
 
        threading.Thread(target=self._write_excel, daemon=True).start()
 
    def _write_excel(self):
        if platform == "android":
            from android.storage import primary_external_storage_path
            folder = os.path.join(primary_external_storage_path(),
                                  "Download")
        else:
            folder = os.path.expanduser("~")
 
        os.makedirs(folder, exist_ok=True)
        fname = f"QR_Scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path  = os.path.join(folder, fname)
 
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "QR Scan Data"
 
            thin   = Side(style="thin", color="B0BEC5")
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
 
            # Title
            ws.merge_cells("A1:C1")
            c = ws["A1"]
            c.value     = "QR Code Scan Report"
            c.font      = Font(bold=True, size=14, color="1565C0", name="Calibri")
            c.alignment = Alignment(horizontal="center")
 
            ws["A2"] = "Ngày xuất:"
            ws["B2"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            ws["A3"] = "Tổng số mã:"
            ws["B3"] = len(self.scan_data)
            ws["A2"].font = Font(bold=True)
            ws["A3"].font = Font(bold=True)
 
            # Header
            hdr_fill  = PatternFill("solid", fgColor="1976D2")
            hdr_font  = Font(bold=True, color="FFFFFF", name="Calibri")
            hdr_align = Alignment(horizontal="center", vertical="center")
            for col, h in enumerate(["STT", "Nội dung QR Code", "Thời gian quét"], 1):
                cell           = ws.cell(row=5, column=col, value=h)
                cell.font      = hdr_font
                cell.fill      = hdr_fill
                cell.alignment = hdr_align
                cell.border    = border
 
            even_fill = PatternFill("solid", fgColor="E3F2FD")
            for row_i, d in enumerate(self.scan_data, 6):
                fill = even_fill if row_i % 2 == 0 else PatternFill()
                for col, val in [(1, d["index"]), (2, d["qr"]), (3, d["time"])]:
                    cell           = ws.cell(row=row_i, column=col, value=val)
                    cell.fill      = fill
                    cell.border    = border
                    cell.font      = Font(name="Calibri", size=10)
                    cell.alignment = Alignment(
                        vertical="center",
                        horizontal="center" if col in (1, 3) else "left",
                        wrap_text=(col == 2))
 
            ws.column_dimensions["A"].width = 8
            ws.column_dimensions["B"].width = 55
            ws.column_dimensions["C"].width = 22
            ws.freeze_panes = "A6"
 
            wb.save(path)
            Clock.schedule_once(
                lambda _: Snackbar(text=f"Đã lưu: {fname}").open(), 0)
        except Exception as ex:
            Clock.schedule_once(
                lambda _: Snackbar(text=f"Lỗi: {ex}").open(), 0)
 
 
if __name__ == "__main__":
    QRScanApp().run()