"""
Minimal XLSX writer - khong can openpyxl.
Su dung zipfile + XML thuan tuy - chay duoc tren moi Python/Android.
"""
 
import zipfile
import io
import datetime
 
 
def _esc(s):
    """XML escape."""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
 
 
def write_xlsx(path: str, scan_data: list):
    """
    Tao file xlsx tai `path` tu danh sach scan_data.
    Moi phan tu: {"index": int, "qr": str, "time": str}
    Cot: STT | QRCode | Time
    """
    # ── rels ──────────────────────────────────────────────────────────────────
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' \
           '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' \
           '</Relationships>'
 
    xl_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' \
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>' \
              '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' \
              '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>' \
              '</Relationships>'
 
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' \
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' \
        '<Default Extension="xml" ContentType="application/xml"/>' \
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' \
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' \
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' \
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>' \
        '</Types>'
 
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
               '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ' \
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' \
               '<sheets><sheet name="QR Scan Data" sheetId="1" r:id="rId1"/></sheets>' \
               '</workbook>'
 
    # ── Shared strings ────────────────────────────────────────────────────────
    strings = []
    str_index = {}
 
    def si(s):
        s = str(s)
        if s not in str_index:
            str_index[s] = len(strings)
            strings.append(s)
        return str_index[s]
 
    # ── Build rows ────────────────────────────────────────────────────────────
    rows_xml = []
 
    def row(r_num, cells):
        """cells: list of (col_letter, value, style_id)"""
        parts = [f'<row r="{r_num}">']
        for col, val, sid in cells:
            ref = f"{col}{r_num}"
            if isinstance(val, int):
                parts.append(f'<c r="{ref}" s="{sid}"><v>{val}</v></c>')
            else:
                parts.append(
                    f'<c r="{ref}" t="s" s="{sid}"><v>{si(val)}</v></c>')
        parts.append('</row>')
        return "".join(parts)
 
    # Row 1: title (merged A1:C1 done via mergeCells)
    export_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    rows_xml.append(row(1, [
        ("A", "QR Code & Barcode Scan Report", 2),
        ("B", "", 0), ("C", "", 0)]))
    rows_xml.append(row(2, [("A", "Ngay xuat:", 1),
                             ("B", export_time, 0), ("C", "", 0)]))
    rows_xml.append(row(3, [("A", "Tong so ma:", 1),
                             ("B", len(scan_data), 0), ("C", "", 0)]))
    rows_xml.append(row(4, [("A", "", 0), ("B", "", 0), ("C", "", 0)]))
    # Header row 5
    rows_xml.append(row(5, [("A", "STT", 3),
                             ("B", "QRCode", 3),
                             ("C", "Time", 3)]))
    # Data rows
    for i, d in enumerate(scan_data):
        r_num = i + 6
        sid   = 4 if r_num % 2 == 0 else 0
        rows_xml.append(row(r_num, [
            ("A", d["index"], sid),
            ("B", d["qr"],    sid),
            ("C", d["time"],  sid),
        ]))
 
    # ── Worksheet XML ─────────────────────────────────────────────────────────
    ws_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="5" topLeftCell="A6" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        '<cols>'
        '<col min="1" max="1" width="8" customWidth="1"/>'
        '<col min="2" max="2" width="60" customWidth="1"/>'
        '<col min="3" max="3" width="22" customWidth="1"/>'
        '</cols>'
        '<sheetData>'
        + "".join(rows_xml) +
        '</sheetData>'
        '<mergeCells><mergeCell ref="A1:C1"/></mergeCells>'
        '</worksheet>'
    )
 
    # ── Shared strings XML ────────────────────────────────────────────────────
    ss_items = "".join(
        f'<si><t xml:space="preserve">{_esc(s)}</t></si>'
        for s in strings)
    ss_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(strings)}" uniqueCount="{len(strings)}">'
        + ss_items +
        '</sst>'
    )
 
    # ── Styles XML ────────────────────────────────────────────────────────────
    # style 0=normal, 1=bold, 2=title, 3=header(blue bg white bold), 4=alt row
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="4">'
        '<font><sz val="11"/><name val="Calibri"/></font>'
        '<font><sz val="11"/><name val="Calibri"/><b/></font>'
        '<font><sz val="14"/><name val="Calibri"/><b/><color rgb="FF1565C0"/></font>'
        '<font><sz val="11"/><name val="Calibri"/><b/><color rgb="FFFFFFFF"/></font>'
        '</fonts>'
        '<fills count="4">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1976D2"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFE3F2FD"/></patternFill></fill>'
        '</fills>'
        '<borders count="2">'
        '<border><left/><right/><top/><bottom/><diagonal/></border>'
        '<border>'
        '<left style="thin"><color rgb="FFB0BEC5"/></left>'
        '<right style="thin"><color rgb="FFB0BEC5"/></right>'
        '<top style="thin"><color rgb="FFB0BEC5"/></top>'
        '<bottom style="thin"><color rgb="FFB0BEC5"/></bottom>'
        '</border>'
        '</borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="5">'
        # 0: normal
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0">'
        '<alignment wrapText="1" vertical="center"/></xf>'
        # 1: bold label
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0">'
        '<alignment vertical="center"/></xf>'
        # 2: title (large blue bold, centered)
        '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0">'
        '<alignment horizontal="center" vertical="center"/></xf>'
        # 3: header (blue fill, white bold, centered)
        '<xf numFmtId="0" fontId="3" fillId="2" borderId="1" xfId="0" applyFill="1">'
        '<alignment horizontal="center" vertical="center"/></xf>'
        # 4: alt row (light blue fill)
        '<xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1">'
        '<alignment wrapText="1" vertical="center"/></xf>'
        '</cellXfs>'
        '</styleSheet>'
    )
 
    # ── Pack into ZIP ─────────────────────────────────────────────────────────
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/_rels/workbook.xml.rels", xl_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/worksheets/sheet1.xml", ws_xml)
        zf.writestr("xl/sharedStrings.xml", ss_xml)
        zf.writestr("xl/styles.xml", styles_xml)
 
    with open(path, "wb") as f:
        f.write(buf.getvalue())
