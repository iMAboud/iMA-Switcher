import sys
import copy
import logging
import os
import threading
import time
import ctypes
import webbrowser
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QDialog,
    QScrollArea,
    QGridLayout,
    QGraphicsDropShadowEffect,
    QGraphicsBlurEffect,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QDesktopWidget,
    QStyleOption,
    QStyle,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QApplication, 
    QCheckBox,
    QSpinBox,
    QTabWidget,
    QComboBox,
    QSlider,
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
    QStackedWidget,
    QInputDialog,
    QProgressBar,
    QTextEdit,
    QMenu,
    QMessageBox,
)

def download_and_open_ima_menu():
    repo_url = "https://github.com/iMAboud/iMA-Menu"
    direct_download_url = "https://github.com/iMAboud/iMA-Menu/releases/latest/download/iMA.Menu.exe"
    try:
        webbrowser.open(repo_url)
        webbrowser.open(direct_download_url)
    except Exception as e:
        logging.error(f"Failed to open iMA Menu download link: {e}")
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QFont, QPainterPath, QLinearGradient, QPen
from PyQt5.QtCore import (
    Qt,
    QSize,
    QPoint,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QRectF,
    QTimer,
    QPointF,
    pyqtProperty,
    QThread,
    QEvent,
    QObject,
)


from theme_manager import get_available_themes, apply_theme_to_app, get_current_theme_key, get_theme


def get_asset_path(filename):
    """Utility to resolve absolute path of assets across source and frozen builds."""
    if hasattr(sys, '_MEIPASS'):
        p1 = os.path.join(sys._MEIPASS, filename)
        if os.path.exists(p1):
            return p1
        return os.path.join(sys._MEIPASS, 'Assets', filename)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    p2 = os.path.join(base_dir, filename)
    if os.path.exists(p2):
        return p2
    return os.path.join(base_dir, 'Assets', filename)

def get_agent_icon_html(agent_name, switcher_base_dir, width=14, height=14):
    if not agent_name or str(agent_name).lower() == "unknown":
        return "⚔️ "
    agents_dir = Path(switcher_base_dir) / "Agents"
    agent_path = agents_dir / f"{agent_name}.png"
    if not agent_path.exists():
        for f in agents_dir.glob("*.png"):
            if f.stem.lower() == str(agent_name).lower():
                agent_path = f
                break
    if agent_path.exists():
        clean_path = str(agent_path).replace("\\", "/")
        return f"<img src='{clean_path}' width='{width}' height='{height}'> "
    return "⚔️ "

def get_icon_path(filename):
    return str(Path(__file__).parent / "icons" / filename)

def get_icon_paths_from_folder(folder_path):
    """
    Retrieves all image file paths from the specified folder.
    """
    icon_paths = []
    if Path(folder_path).is_dir():
        for filename in os.listdir(folder_path):
            file_path = Path(folder_path) / filename
            if file_path.is_file() and file_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.ico'):
                icon_paths.append(str(file_path))
    return icon_paths


VALORANT_CROSSHAIR_PRESETS = {
    "TenZ (1-4-2-2 Cyan)": "0;s;1;P;c;5;h;0;m;0;0l;4;0v;4;0g;1;0o;2;0a;1;0f;0;1b;0",
    "Dot (Green ScreaM)": "0;P;c;1;d;1;a;1;z;3;h;0;0b;0;1b;0",
    "Chronicle (Red Box)": "0;P;c;7;o;1;d;1;z;1;0t;1;0l;3;0o;1;0a;1;0f;0;1b;0",
    "Boaster (Cyan 1-2-2-0)": "0;P;c;5;o;1;d;1;z;1;0b;0;0l;2;0o;2;0a;1;0f;0;1b;0",
    "Clean Plus (1-4-2-2)": "0;P;c;5;h;1;0t;1;0l;4;0o;2;0a;1;1b;0",
    "Competitive (1-4-2-0 Green)": "0;P;c;1;h;1;0t;1;0l;4;0o;2;0a;1;0f;0;1b;0",
    "Hollow Box (4-1-1-0 Cyan)": "0;P;c;5;h;1;0t;4;0l;1;0o;1;0a;1;1b;0"
}

class CrosshairCanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.bg_type = "Dark Grid"
        self.zoom = 2.0
        self.profile = {}

    def set_profile(self, profile):
        self.profile = profile or {}
        self.update()

    def set_bg(self, bg_name):
        self.bg_type = bg_name
        self.update()

    def set_zoom(self, zoom_val):
        self.zoom = float(zoom_val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        w = self.width()
        h = self.height()
        cx = int(w // 2)
        cy = int(h // 2)

        if self.bg_type == "Light Grid":
            painter.fillRect(0, 0, w, h, QColor("#e8e2de"))
            painter.setPen(QColor("#d4ceca"))
            for x in range(0, w, 20): painter.drawLine(x, 0, x, h)
            for y in range(0, h, 20): painter.drawLine(0, y, w, y)
        elif self.bg_type == "Pure Black":
            painter.fillRect(0, 0, w, h, QColor("#0d0e12"))
        else:
            painter.fillRect(0, 0, w, h, QColor("#181a1f"))
            painter.setPen(QColor("#262930"))
            for x in range(0, w, 20): painter.drawLine(x, 0, x, h)
            for y in range(0, h, 20): painter.drawLine(0, y, w, y)

        if not self.profile:
            return

        primary = self.profile.get("primary", {})
        preset_colors = [
            QColor(255, 255, 255),  # 0: White
            QColor(0, 255, 0),      # 1: Green
            QColor(127, 255, 0),    # 2: Yellow Green
            QColor(190, 255, 0),    # 3: Green Yellow
            QColor(255, 255, 0),    # 4: Yellow
            QColor(0, 255, 255),    # 5: Cyan
            QColor(255, 0, 255),    # 6: Pink
            QColor(255, 0, 0),      # 7: Red
        ]

        main_color = None
        col_val = primary.get("color")
        if col_val is None:
            col_val = primary.get("primaryColor")

        if isinstance(col_val, dict):
            r_val = col_val.get('r', col_val.get('R', None))
            g_val = col_val.get('g', col_val.get('G', None))
            b_val = col_val.get('b', col_val.get('B', None))
            a_val = col_val.get('a', col_val.get('A', 255))
            if r_val is not None and g_val is not None and b_val is not None:
                r_int = int(round(r_val * 255)) if isinstance(r_val, float) and r_val <= 1.0 else int(r_val)
                g_int = int(round(g_val * 255)) if isinstance(g_val, float) and g_val <= 1.0 else int(g_val)
                b_int = int(round(b_val * 255)) if isinstance(b_val, float) and b_val <= 1.0 else int(b_val)
                a_int = int(round(a_val * 255)) if isinstance(a_val, float) and a_val <= 1.0 else int(a_val)
                main_color = QColor(max(0, min(255, r_int)), max(0, min(255, g_int)), max(0, min(255, b_int)), max(0, min(255, a_int)))
        elif isinstance(col_val, int) and 0 <= col_val < len(preset_colors):
            main_color = preset_colors[col_val]
        elif primary.get("bUseCustomColor", False) or "colorCustom" in primary or "customColor" in primary:
            custom_dict = primary.get("colorCustom") or primary.get("customColor")
            if isinstance(custom_dict, dict):
                r = int(custom_dict.get('r', custom_dict.get('R', 255)))
                g = int(custom_dict.get('g', custom_dict.get('G', 255)))
                b = int(custom_dict.get('b', custom_dict.get('B', 255)))
                main_color = QColor(r, g, b)
            elif isinstance(custom_dict, str) and custom_dict.startswith("#"):
                main_color = QColor(custom_dict)
            else:
                main_color = QColor(0, 255, 136)

        if not main_color or not main_color.isValid():
            main_color = QColor(255, 255, 255)

        scale = max(1, int(round(self.zoom)))
        b_outline = primary.get("bHasOutline", primary.get("bOutlineEnabled", True))
        outline_op = float(primary.get("outlineOpacity", 1.0))
        outline_thick = max(1, int(primary.get("outlineThickness", 1))) * scale
        outline_color = QColor(0, 0, 0, int(outline_op * 255))

        outline_quads = []
        fill_quads = []

        outer = primary.get("outerLines", {})
        o_len = int(outer.get("lineLength", 0))
        o_vlen = int(outer.get("lineLengthVertical", o_len)) if not outer.get("bAllowVertScaling", False) else int(outer.get("lineLengthVertical", o_len))
        o_op = float(outer.get("opacity", outer.get("lineOpacity", 0.35)))
        is_outer_enabled = outer.get("bShowLines", outer.get("bDisplayOuterLines", outer.get("bbDisplayOuterLines", False)))
        if is_outer_enabled and (o_len > 0 or o_vlen > 0) and o_op > 0:
            o_thick = max(1, int(outer.get("lineThickness", 2)))
            o_off = int(outer.get("lineOffset", 10))
            show_top = outer.get("bShowTopLine", True)
            line_col = QColor(main_color.red(), main_color.green(), main_color.blue(), int(o_op * 255))

            t_px = o_thick * scale
            l_px = o_len * scale
            vl_px = o_vlen * scale
            off_px = o_off * scale
            t_half = (o_thick // 2) * scale

            if show_top and vl_px > 0:
                fill_quads.append((QRect(cx - t_half, cy - off_px - vl_px, t_px, vl_px), line_col))
                outline_quads.append(QRect(cx - t_half - outline_thick, cy - off_px - vl_px - outline_thick, t_px + 2*outline_thick, vl_px + 2*outline_thick))
            if vl_px > 0:
                fill_quads.append((QRect(cx - t_half, cy + off_px, t_px, vl_px), line_col))
                outline_quads.append(QRect(cx - t_half - outline_thick, cy + off_px - outline_thick, t_px + 2*outline_thick, vl_px + 2*outline_thick))
            if l_px > 0:
                fill_quads.append((QRect(cx - off_px - l_px, cy - t_half, l_px, t_px), line_col))
                outline_quads.append(QRect(cx - off_px - l_px - outline_thick, cy - t_half - outline_thick, l_px + 2*outline_thick, t_px + 2*outline_thick))
            if l_px > 0:
                fill_quads.append((QRect(cx + off_px, cy - t_half, l_px, t_px), line_col))
                outline_quads.append(QRect(cx + off_px - outline_thick, cy - t_half - outline_thick, l_px + 2*outline_thick, t_px + 2*outline_thick))

        inner = primary.get("innerLines", {})
        i_len = int(inner.get("lineLength", 0))
        i_vlen = int(inner.get("lineLengthVertical", i_len)) if not inner.get("bAllowVertScaling", False) else int(inner.get("lineLengthVertical", i_len))
        i_op = float(inner.get("opacity", inner.get("lineOpacity", 1.0)))
        is_inner_enabled = inner.get("bShowLines", inner.get("bDisplayInnerLines", inner.get("bbDisplayInnerLines", False)))
        if is_inner_enabled and (i_len > 0 or i_vlen > 0) and i_op > 0:
            i_thick = max(1, int(inner.get("lineThickness", 2)))
            i_off = int(inner.get("lineOffset", 3))
            show_top = inner.get("bShowTopLine", True)
            line_col = QColor(main_color.red(), main_color.green(), main_color.blue(), int(i_op * 255))

            t_px = i_thick * scale
            l_px = i_len * scale
            vl_px = i_vlen * scale
            off_px = i_off * scale
            t_half = (i_thick // 2) * scale

            if show_top and vl_px > 0:
                fill_quads.append((QRect(cx - t_half, cy - off_px - vl_px, t_px, vl_px), line_col))
                outline_quads.append(QRect(cx - t_half - outline_thick, cy - off_px - vl_px - outline_thick, t_px + 2*outline_thick, vl_px + 2*outline_thick))
            if vl_px > 0:
                fill_quads.append((QRect(cx - t_half, cy + off_px, t_px, vl_px), line_col))
                outline_quads.append(QRect(cx - t_half - outline_thick, cy + off_px - outline_thick, t_px + 2*outline_thick, vl_px + 2*outline_thick))
            if l_px > 0:
                fill_quads.append((QRect(cx - off_px - l_px, cy - t_half, l_px, t_px), line_col))
                outline_quads.append(QRect(cx - off_px - l_px - outline_thick, cy - t_half - outline_thick, l_px + 2*outline_thick, t_px + 2*outline_thick))
            if l_px > 0:
                fill_quads.append((QRect(cx + off_px, cy - t_half, l_px, t_px), line_col))
                outline_quads.append(QRect(cx + off_px - outline_thick, cy - t_half - outline_thick, l_px + 2*outline_thick, t_px + 2*outline_thick))

        if b_outline and outline_thick > 0 and outline_op > 0:
            for out_rect in outline_quads:
                painter.fillRect(out_rect, outline_color)

        for rect, col in fill_quads:
            painter.fillRect(rect, col)

        if primary.get("bDisplayCenterDot", False):
            dot_op = float(primary.get("centerDotOpacity", 1.0))
            dot_size = max(1, int(primary.get("centerDotSize", 2)))
            dot_col = QColor(main_color.red(), main_color.green(), main_color.blue(), int(dot_op * 255))
            dot_px = dot_size * scale
            dot_half = (dot_size // 2) * scale

            painter.setRenderHint(QPainter.Antialiasing, True)
            if b_outline and outline_thick > 0 and outline_op > 0:
                out_rect = QRect(cx - dot_half - outline_thick, cy - dot_half - outline_thick, dot_px + 2*outline_thick, dot_px + 2*outline_thick)
                painter.setPen(Qt.NoPen)
                painter.setBrush(outline_color)
                painter.drawEllipse(out_rect)

            dot_rect = QRect(cx - dot_half, cy - dot_half, dot_px, dot_px)
            painter.setPen(Qt.NoPen)
            painter.setBrush(dot_col)
            painter.drawEllipse(dot_rect)
            painter.setRenderHint(QPainter.Antialiasing, False)


class ValorantCrosshairCodeParser:
    @staticmethod
    def parse_code(code_str: str) -> dict:
        code_str = code_str.strip()
        if not code_str:
            return {}
        tokens = code_str.split(";")
        profile = {
            "profileName": "Imported Profile",
            "primary": {
                "color": 0,
                "bUseCustomColor": False,
                "customColor": "#00FF88FF",
                "bOutlineEnabled": True,
                "outlineOpacity": 1.0,
                "outlineThickness": 1,
                "bDisplayCenterDot": False,
                "centerDotOpacity": 1.0,
                "centerDotSize": 2,
                "innerLines": {
                    "bDisplayInnerLines": False,
                    "lineOpacity": 1.0,
                    "lineLength": 6,
                    "lineLengthVertical": 6,
                    "bIgnoreVerticalLength": True,
                    "lineThickness": 2,
                    "lineOffset": 3,
                    "bShowTopLine": True,
                    "bShowMovementError": False,
                    "bShowShootingError": False
                },
                "outerLines": {
                    "bDisplayOuterLines": False,
                    "lineOpacity": 0.35,
                    "lineLength": 2,
                    "lineLengthVertical": 2,
                    "bIgnoreVerticalLength": True,
                    "lineThickness": 2,
                    "lineOffset": 10,
                    "bShowTopLine": True,
                    "bShowMovementError": False,
                    "bShowShootingError": False
                }
            }
        }
        primary = profile["primary"]
        inner = primary["innerLines"]
        outer = primary["outerLines"]

        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t == "c" and i + 1 < len(tokens):
                try: primary["color"] = int(tokens[i+1])
                except: pass
                i += 1
            elif t == "u" and i + 1 < len(tokens):
                primary["bUseCustomColor"] = True
                c_val = tokens[i+1]
                if not c_val.startswith("#"): c_val = "#" + c_val
                if len(c_val) == 7: c_val += "FF"
                primary["customColor"] = c_val
                i += 1
            elif t == "b" and i + 1 < len(tokens):
                primary["bOutlineEnabled"] = (tokens[i+1] == "1")
                i += 1
            elif t == "o" and i + 1 < len(tokens):
                try: primary["outlineOpacity"] = float(tokens[i+1])
                except: pass
                i += 1
            elif t == "t" and i + 1 < len(tokens):
                try: primary["outlineThickness"] = int(tokens[i+1])
                except: pass
                i += 1
            elif t == "d" and i + 1 < len(tokens):
                primary["bDisplayCenterDot"] = (tokens[i+1] == "1")
                i += 1
            elif t == "a" and i + 1 < len(tokens):
                try: primary["centerDotOpacity"] = float(tokens[i+1])
                except: pass
                i += 1
            elif t == "z" and i + 1 < len(tokens):
                try: primary["centerDotSize"] = int(tokens[i+1])
                except: pass
                i += 1
            elif (t == "h" or t == "0h" or t == "0b") and i + 1 < len(tokens):
                inner["bDisplayInnerLines"] = (tokens[i+1] == "1")
                i += 1
            elif t == "0t" and i + 1 < len(tokens):
                try: inner["lineThickness"] = int(tokens[i+1])
                except: pass
                if tokens[i+1] != "0": inner["bDisplayInnerLines"] = True
                i += 1
            elif t == "0l" and i + 1 < len(tokens):
                try: inner["lineLength"] = int(tokens[i+1])
                except: pass
                if tokens[i+1] != "0": inner["bDisplayInnerLines"] = True
                i += 1
            elif t == "0v" and i + 1 < len(tokens):
                try: inner["lineLengthVertical"] = int(tokens[i+1])
                except: pass
                i += 1
            elif t == "0g" and i + 1 < len(tokens):
                inner["bIgnoreVerticalLength"] = (tokens[i+1] == "1")
                i += 1
            elif t == "0o" and i + 1 < len(tokens):
                try: inner["lineOffset"] = int(tokens[i+1])
                except: pass
                i += 1
            elif t == "0a" and i + 1 < len(tokens):
                try: inner["lineOpacity"] = float(tokens[i+1])
                except: pass
                i += 1
            elif t == "0s" and i + 1 < len(tokens):
                inner["bShowTopLine"] = (tokens[i+1] == "1")
                i += 1
            elif (t == "1h" or t == "1b") and i + 1 < len(tokens):
                outer["bDisplayOuterLines"] = (tokens[i+1] == "1")
                i += 1
            elif t == "1t" and i + 1 < len(tokens):
                try: outer["lineThickness"] = int(tokens[i+1])
                except: pass
                if tokens[i+1] != "0": outer["bDisplayOuterLines"] = True
                i += 1
            elif t == "1l" and i + 1 < len(tokens):
                try: outer["lineLength"] = int(tokens[i+1])
                except: pass
                if tokens[i+1] != "0": outer["bDisplayOuterLines"] = True
                i += 1
            elif t == "1v" and i + 1 < len(tokens):
                try: outer["lineLengthVertical"] = int(tokens[i+1])
                except: pass
                i += 1
            elif t == "1g" and i + 1 < len(tokens):
                outer["bIgnoreVerticalLength"] = (tokens[i+1] == "1")
                i += 1
            elif t == "1o" and i + 1 < len(tokens):
                try: outer["lineOffset"] = int(tokens[i+1])
                except: pass
                i += 1
            elif t == "1a" and i + 1 < len(tokens):
                try: outer["lineOpacity"] = float(tokens[i+1])
                except: pass
                i += 1
            elif t == "1s" and i + 1 < len(tokens):
                outer["bShowTopLine"] = (tokens[i+1] == "1")
                i += 1
            i += 1
        return profile

    @staticmethod
    def export_code(profile: dict) -> str:
        primary = profile.get("primary", {})
        inner = primary.get("innerLines", {})
        outer = primary.get("outerLines", {})
        parts = ["0", "P"]

        if primary.get("bUseCustomColor", False):
            custom_hex = primary.get("customColor", "#00FF88FF").replace("#", "")
            parts.extend(["c", "8", "u", custom_hex])
        else:
            c_idx = primary.get("color", 0)
            parts.extend(["c", str(c_idx)])

        if not primary.get("bOutlineEnabled", True):
            parts.extend(["b", "0"])
        else:
            op = primary.get("outlineOpacity", 1.0)
            if op != 1.0: parts.extend(["o", f"{op:.3f}".rstrip('0').rstrip('.')])
            th = primary.get("outlineThickness", 1)
            if th != 1: parts.extend(["t", str(th)])

        if primary.get("bDisplayCenterDot", False):
            parts.extend(["d", "1"])
            d_op = primary.get("centerDotOpacity", 1.0)
            if d_op != 1.0: parts.extend(["a", f"{d_op:.3f}".rstrip('0').rstrip('.')])
            d_sz = primary.get("centerDotSize", 2)
            if d_sz != 2: parts.extend(["z", str(d_sz)])

        if not inner.get("bDisplayInnerLines", True):
            parts.extend(["h", "0"])
        else:
            parts.extend(["0t", str(inner.get("lineThickness", 2))])
            parts.extend(["0l", str(inner.get("lineLength", 6))])
            parts.extend(["0o", str(inner.get("lineOffset", 3))])
            i_op = inner.get("lineOpacity", 1.0)
            if i_op != 1.0: parts.extend(["0a", f"{i_op:.3f}".rstrip('0').rstrip('.')])
            if not inner.get("bShowTopLine", True): parts.extend(["0s", "0"])

        if outer.get("bDisplayOuterLines", False):
            parts.extend(["1b", "1"])
            parts.extend(["1t", str(outer.get("lineThickness", 2))])
            parts.extend(["1l", str(outer.get("lineLength", 2))])
            parts.extend(["1o", str(outer.get("lineOffset", 10))])
            o_op = outer.get("lineOpacity", 0.35)
            if o_op != 1.0: parts.extend(["1a", f"{o_op:.3f}".rstrip('0').rstrip('.')])
            if not outer.get("bShowTopLine", True): parts.extend(["1s", "0"])
        else:
            parts.extend(["1b", "0"])

        return ";".join(parts)


class LaunchNotificationWidget(QWidget):
    def __init__(self, account_name, icon_pixmap, in_game_name=None, in_game_tag=None, rank=None, use_rank_icons=False, parent=None, standalone=False, switcher_instance=None):
        super().__init__(parent)
        self.switcher_instance = switcher_instance
        self.standalone = standalone
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.CustomizeWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_DeleteOnClose)
        self.setup_ui(account_name, icon_pixmap, in_game_name, in_game_tag, rank, use_rank_icons)
        self.center_on_screen()
        
        # Set initial opacity to 0
        self.setWindowOpacity(0.0)
        
        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(500)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_anim.start()

        # Trigger fade out 500ms before the 6000ms total duration
        QTimer.singleShot(5500, self.start_fade_out)

    def start_fade_out(self):
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(500)
        self.fade_out_anim.setStartValue(self.windowOpacity())
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InOutQuad)
        if self.standalone:
            self.fade_out_anim.finished.connect(self.close_and_exit)
        else:
            self.fade_out_anim.finished.connect(self.close)
        self.fade_out_anim.start()

    def close_and_exit(self):
        """Closes the widget and quits the QApplication."""
        self.close()
        app_instance = QApplication.instance()
        if app_instance:
            app_instance.quit()

    def _add_shadow_effect(self, widget):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 3)
        widget.setGraphicsEffect(shadow)

    def setup_ui(self, name, pixmap, in_game_name, in_game_tag, rank, use_rank_icons):
        self.setFixedSize(320, 380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        splash_pixmap = pixmap
        if self.switcher_instance:
            base_dir = Path(self.switcher_instance.base_dir)
            game_config = self.switcher_instance._load_game_config(name)
            orig_name = game_config.get("original_icon_name")
            
            candidate_names = []
            if orig_name:
                candidate_names.append(orig_name)
            
            account_data = self.switcher_instance.get_saved_accounts().get(name)
            if account_data and account_data[0]:
                candidate_names.append(Path(account_data[0]).name)

            for cand in candidate_names:
                full_body_candidate = base_dir / "icons" / cand
                if full_body_candidate.exists():
                    splash_pixmap = self.switcher_instance.get_qicon_from_path(str(full_body_candidate)).pixmap(180, 180)
                    break

        icon_label = QLabel(self)
        icon_label.setPixmap(splash_pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        self._add_shadow_effect(icon_label)
        layout.addWidget(icon_label); layout.addSpacing(15)
        
        name_layout = QHBoxLayout()
        name_layout.setAlignment(Qt.AlignCenter)

        # Rank icon next to name
        if rank and not use_rank_icons: # Only show if not already using rank icon as main icon
            rank_icon_path = Path(get_asset_path(f"{rank.lower().replace(' ', '_')}.png"))
            if rank_icon_path.exists():
                rank_pixmap = self.switcher_instance.get_qicon_from_path(rank_icon_path).pixmap(24, 24)
                rank_label = QLabel(self)
                rank_label.setPixmap(rank_pixmap)
                self._add_shadow_effect(rank_label)
                name_layout.addWidget(rank_label)

        name_label = QLabel(name, self)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; text-align: center;")
        self._add_shadow_effect(name_label)
        name_layout.addWidget(name_label)
        layout.addLayout(name_layout)

        if in_game_name and in_game_tag:
            in_game_label = QLabel(f"{in_game_name}#{in_game_tag}", self)
            in_game_label.setAlignment(Qt.AlignCenter)
            in_game_label.setStyleSheet("color: #b0a8a8; font-size: 16px; text-align: center;")
            self._add_shadow_effect(in_game_label)
            layout.addWidget(in_game_label)
        elif in_game_name:
            in_game_label = QLabel(in_game_name, self)
            in_game_label.setAlignment(Qt.AlignCenter)
            in_game_label.setStyleSheet("color: #b0a8a8; font-size: 16px; text-align: center;")
            self._add_shadow_effect(in_game_label)
            layout.addWidget(in_game_label)

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            self.move(screen.availableGeometry().center() - self.frameGeometry().center())

class ValueSlider(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, min_val, max_val, step=0.1, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.scale_factor = 100 # To handle floats with 2 decimal places
        self.min_val_scaled = int(min_val * self.scale_factor)
        self.max_val_scaled = int(max_val * self.scale_factor)
        self.step_scaled = int(step * self.scale_factor)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self.min_val_scaled, self.max_val_scaled)
        self.slider.setSingleStep(self.step_scaled)

        self.spin_box = QDoubleSpinBox() # Use QDoubleSpinBox for float values
        self.spin_box.setRange(min_val, max_val)
        self.spin_box.setSingleStep(step)
        self.spin_box.setDecimals(1) # Display one decimal place
        self.spin_box.setFixedWidth(70)
        self.spin_box.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.slider)
        layout.addWidget(self.spin_box)

        self.slider.valueChanged.connect(lambda val: self.spin_box.setValue(val / self.scale_factor))
        self.spin_box.valueChanged.connect(lambda val: self.slider.setValue(int(val * self.scale_factor)))
        self.slider.valueChanged.connect(lambda val: self.valueChanged.emit(val / self.scale_factor))

    def value(self):
        return self.slider.value() / self.scale_factor

    def setValue(self, value):
        self.slider.setValue(int(value * self.scale_factor))

class RadioButtonGroup(QWidget):
    stateChanged = pyqtSignal(bool)

    def __init__(self, text_true, text_false, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        main_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.btn_true = QPushButton(text_true)
        self.btn_false = QPushButton(text_false)
        
        self.btn_true.setCheckable(True)
        self.btn_false.setCheckable(True)

        toggle_style = """
            QPushButton {
                background-color: #242933;
                color: #8fa7bb;
                border: 1px solid #3b4252;
                border-radius: 12px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: bold;
                min-width: 85px;
            }
            QPushButton:hover {
                background-color: #2e3440;
                color: #ffffff;
                border-color: #4c566a;
            }
            QPushButton:checked {
                background-color: #20e693;
                color: #064e3b;
                border: 1px solid #20e693;
            }
        """
        self.btn_true.setStyleSheet(toggle_style)
        self.btn_false.setStyleSheet(toggle_style)

        self.btn_true.clicked.connect(lambda: self.set_state(True))
        self.btn_false.clicked.connect(lambda: self.set_state(False))

        main_layout.addWidget(self.btn_false)
        main_layout.addWidget(self.btn_true)
    
    def set_state(self, is_true):
        self.btn_true.setChecked(is_true)
        self.btn_false.setChecked(not is_true)
        self.stateChanged.emit(is_true)

    def get_state(self):
        return self.btn_true.isChecked()

class PopupDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        
        self.main_widget = QWidget(objectName="popup_widget")
        
        popup_layout = QVBoxLayout(self.main_widget)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(title, self, is_dialog=True)
        popup_layout.addWidget(self.title_bar)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(15, 10, 15, 15)
        popup_layout.addLayout(self.content_layout)

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0,0,0,0)
        main_v_layout.addWidget(self.main_widget)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.center() - self.rect().center())

class ValorantIconPickerDialog(PopupDialog):
    def __init__(self, parent=None, switcher_instance=None):
        super().__init__("Select Valorant Menu Icon", parent)
        self.switcher = switcher_instance
        self.selected_icon_path = None
        self.setFixedSize(380, 420)

        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignTop)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        grid_container = QWidget(objectName="grid_container")
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        scroll_area.setWidget(grid_container)
        
        self.content_layout.addWidget(scroll_area)

        base_dir = self.switcher.base_dir if self.switcher else Path(__file__).parent
        valorant_dir = Path(base_dir) / "Assets" / "valorant"
        icon_files = get_icon_paths_from_folder(str(valorant_dir))
        
        for i, icon_path in enumerate(icon_files):
            row, col = i // 3, i % 3
            btn = QPushButton()
            btn.setFixedSize(90, 90)
            if self.switcher:
                icon = self.switcher.get_qicon_from_path(icon_path)
            else:
                icon = QIcon(icon_path)
            btn.setIcon(icon)
            btn.setIconSize(QSize(70, 70))
            btn.clicked.connect(lambda _, path=icon_path: self._select(path))
            self.grid_layout.addWidget(btn, row, col, Qt.AlignCenter)

    def _select(self, path):
        self.selected_icon_path = path
        self.accept()

    def get_selected_icon_path(self):
        return self.selected_icon_path

class ExportIMAMenuDialog(QDialog):
    def __init__(self, accounts_data, parent=None, default_settings=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setMinimumWidth(780)
        default_settings = default_settings or {}
        self.switcher = parent.switcher if (parent and hasattr(parent, 'switcher')) else None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container_widget = QWidget(objectName="container")
        main_layout.addWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.title_bar = CustomTitleBar("iMA Menu Shortcut", self, is_dialog=True)
        container_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        container_layout.addWidget(content_area)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        content_layout.addLayout(top_layout)
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        top_layout.addLayout(left_layout, 5)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        top_layout.addLayout(right_layout, 4)

        self.accounts_data = accounts_data
        self.menu_icon_path = default_settings.get("menu_icon_path", "")
        if not self.menu_icon_path:
            base_dir = self.switcher.base_dir if self.switcher else Path(__file__).parent
            default_icon = Path(base_dir) / "Assets" / "valorant" / "5.png"
            if default_icon.exists():
                self.menu_icon_path = str(default_icon)
        
        group_style = """
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 6px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #FFFFFF; }
        """

        path_group = QGroupBox("iMA Menu Installation")
        path_group.setStyleSheet(group_style)
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(6)

        self.path_stack = QStackedWidget()

        detected_widget = QWidget()
        detected_layout = QVBoxLayout(detected_widget)
        detected_layout.setContentsMargins(0, 0, 0, 0)
        detected_layout.setSpacing(6)

        path_input_layout = QHBoxLayout()
        path_input_layout.setSpacing(8)

        current_path_str = default_settings.get("ima_menu_path", "")
        if not current_path_str and self.switcher:
            current_path_str = str(self.switcher.find_ima_menu_path() or "")

        self.path_edit = QLineEdit(current_path_str)
        self.path_edit.setPlaceholderText("Path to iMA Menu folder or its parent directory")
        self.path_edit.textChanged.connect(self.update_path_status)
        path_input_layout.addWidget(self.path_edit)

        browse_path_button = QPushButton("Browse...")
        browse_path_button.setObjectName("ApplyButton")
        browse_path_button.clicked.connect(self.browse_path)
        path_input_layout.addWidget(browse_path_button)

        detect_button = QPushButton("Detect Active")
        detect_button.setToolTip("Auto-detect the active registered iMA Menu from Windows Registry")
        detect_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; color: #e0d6d1; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: 1px solid #6b6365;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #c89f68; }
        """)
        detect_button.clicked.connect(self.detect_active_path)
        path_input_layout.addWidget(detect_button)
        detected_layout.addLayout(path_input_layout)

        self.path_status_label = QLabel()
        self.path_status_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        detected_layout.addWidget(self.path_status_label)

        self.path_stack.addWidget(detected_widget)

        missing_widget = QWidget()
        missing_layout = QVBoxLayout(missing_widget)
        missing_layout.setContentsMargins(4, 4, 4, 4)
        missing_layout.setSpacing(6)

        banner_title = QLabel("Install iMA Menu to use this feature")
        banner_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        missing_layout.addWidget(banner_title)

        banner_desc = QLabel("iMA Menu is a highly customizable Context menu enhancer tool with smart and beautiful features.")
        banner_desc.setWordWrap(True)
        banner_desc.setStyleSheet("color: #e0d6d1; font-size: 11px;")
        missing_layout.addWidget(banner_desc)

        banner_btn_layout = QHBoxLayout()
        banner_btn_layout.setSpacing(8)

        download_btn = QPushButton("Download")
        download_btn.setObjectName("ApplyButton")
        download_btn.clicked.connect(download_and_open_ima_menu)
        banner_btn_layout.addWidget(download_btn)

        detect_ima_btn = QPushButton("Detect iMA Menu")
        detect_ima_btn.clicked.connect(self.detect_active_path)
        banner_btn_layout.addWidget(detect_ima_btn)

        locate_btn = QPushButton("Browse...")
        locate_btn.clicked.connect(self.browse_path)
        banner_btn_layout.addWidget(locate_btn)
        banner_btn_layout.addStretch()

        missing_layout.addLayout(banner_btn_layout)

        self.path_stack.addWidget(missing_widget)

        path_layout.addWidget(self.path_stack)
        left_layout.addWidget(path_group)

        menu_details_group = QGroupBox("Menu Details")
        menu_details_group.setStyleSheet(group_style)
        menu_details_layout = QVBoxLayout(menu_details_group)
        menu_details_layout.setSpacing(8)

        menu_details_layout.addWidget(QLabel("Menu Title:"))
        self.title_edit = QLineEdit(default_settings.get("title", "Valorant"))
        menu_details_layout.addWidget(self.title_edit)
        
        menu_details_layout.addWidget(QLabel("Menu Icon:"))
        icon_layout = QHBoxLayout()
        icon_layout.setSpacing(8)
        self.icon_path_edit = QLineEdit(self.menu_icon_path)
        self.icon_path_edit.setPlaceholderText("Optional: Select an icon for the main menu")
        self.icon_path_edit.textChanged.connect(self.update_icon_preview)

        self.icon_preview_btn = QPushButton()
        self.icon_preview_btn.setFixedSize(36, 36)
        self.icon_preview_btn.setIconSize(QSize(26, 26))
        self.icon_preview_btn.setToolTip("Click to choose a Valorant menu icon style")
        self.icon_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #d9b68b; }
        """)
        self.icon_preview_btn.clicked.connect(self.open_valorant_icon_picker)

        browse_button = QPushButton("Browse...")
        browse_button.setObjectName("ApplyButton")
        browse_button.clicked.connect(self.select_icon)

        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(self.icon_preview_btn)
        icon_layout.addWidget(browse_button)
        menu_details_layout.addLayout(icon_layout)
        left_layout.addWidget(menu_details_group)

        self.update_icon_preview(self.menu_icon_path)
        
        settings_group = QGroupBox("iMA Menu Settings")
        settings_group.setStyleSheet(group_style)
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(10)
        
        ui_settings = default_settings.get("ui_settings", {})
        self.show_rank_tips_toggle = RadioButtonGroup("On", "Off")
        self.show_rank_tips_toggle.set_state(ui_settings.get("show_rank_tips", False))
        settings_layout.addWidget(QLabel("Show Rank Tips:"), 0, 0)
        settings_layout.addWidget(self.show_rank_tips_toggle, 0, 1)

        self.show_rr_in_tip_toggle = RadioButtonGroup("On", "Off")
        self.show_rr_in_tip_toggle.set_state(ui_settings.get("show_rr_in_tip", False))
        settings_layout.addWidget(QLabel("Show Current RR in Tip:"), 1, 0)
        settings_layout.addWidget(self.show_rr_in_tip_toggle, 1, 1)

        self.tip_delay_slider = ValueSlider(0.0, 2.0, 0.1)
        self.tip_delay_slider.setValue(ui_settings.get("tip_delay", 1.0))
        settings_layout.addWidget(QLabel("Tip Delay (seconds):"), 2, 0)
        settings_layout.addWidget(self.tip_delay_slider, 2, 1)

        self.include_app_shortcut_toggle = RadioButtonGroup("On", "Off")
        self.include_app_shortcut_toggle.set_state(ui_settings.get("include_app_shortcut", False))
        settings_layout.addWidget(QLabel("Add iMA Switcher to Menu:"), 3, 0)
        settings_layout.addWidget(self.include_app_shortcut_toggle, 3, 1)

        self.show_map_planner_toggle = RadioButtonGroup("On", "Off")
        self.show_map_planner_toggle.set_state(ui_settings.get("show_map_planner_in_menu", False))
        settings_layout.addWidget(QLabel("Show Map Planner in Menu:"), 4, 0)
        settings_layout.addWidget(self.show_map_planner_toggle, 4, 1)
        
        left_layout.addWidget(settings_group)
        left_layout.addStretch()
        
        right_layout.addWidget(QLabel("Arrange Accounts (Drag & Drop):"))
        self.accounts_list = QListWidget()
        self.accounts_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.accounts_list.setIconSize(QSize(32, 32))
        self.populate_accounts(default_settings.get("ordered_accounts"))
        right_layout.addWidget(self.accounts_list)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        export_button = QPushButton("Export")
        export_button.setObjectName("ApplyButton")
        export_button.clicked.connect(self.on_export_clicked)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        content_layout.addLayout(button_layout)

        self.update_path_status(self.path_edit.text())
    
    def on_export_clicked(self):
        if not self.accounts_data:
            CustomMessageDialog.warning(self, "No Accounts", "You must save at least one account before exporting.")
            return
        self.accept()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.center() - self.rect().center())

    def browse_path(self):
        initial = self.path_edit.text().strip()
        chosen = QFileDialog.getExistingDirectory(self, "Select iMA Menu Folder or Parent Folder", initial)
        if chosen:
            if self.switcher:
                resolved = self.switcher.resolve_ima_menu_folder(chosen)
                self.path_edit.setText(str(resolved))
            else:
                self.path_edit.setText(chosen)

    def detect_active_path(self):
        if self.switcher:
            detected = self.switcher.get_registered_ima_shell_path() or self.switcher.find_ima_menu_path()
            if detected:
                self.path_edit.setText(str(detected))
                self.update_path_status(str(detected))
            else:
                self.update_path_status("")

    def update_path_status(self, text=None):
        path_val = (text if text is not None else self.path_edit.text()).strip()
        if not path_val:
            self.path_stack.setCurrentIndex(1)
            return
        if self.switcher:
            resolved = self.switcher.resolve_ima_menu_folder(path_val)
            is_reg, active_reg, _ = self.switcher.get_ima_menu_registration_info(resolved)
            if not resolved or not Path(resolved).exists():
                self.path_stack.setCurrentIndex(1)
            else:
                self.path_stack.setCurrentIndex(0)
                if is_reg:
                    self.path_status_label.setText(f"<font color='#2ecc71'>● Active & Registered in Windows Shell: {resolved}</font>")
                elif active_reg:
                    self.path_status_label.setText(f"<font color='#f39c12'>● Custom Path (Live shell registered at: {active_reg})</font>")
                else:
                    self.path_status_label.setText(f"<font color='#f39c12'>● Custom Path (Shell not registered)</font>")
        else:
            if Path(path_val).exists():
                self.path_stack.setCurrentIndex(0)
                self.path_status_label.setText("<font color='#2ecc71'>● Folder exists</font>")
            else:
                self.path_stack.setCurrentIndex(1)

    def update_icon_preview(self, path_text):
        self.menu_icon_path = path_text.strip()
        switcher = self.parent().switcher if (self.parent() and hasattr(self.parent(), 'switcher')) else None
        if self.menu_icon_path and Path(self.menu_icon_path).exists():
            if switcher:
                icon = switcher.get_qicon_from_path(self.menu_icon_path)
            else:
                icon = QIcon(self.menu_icon_path)
            self.icon_preview_btn.setIcon(icon)
        else:
            self.icon_preview_btn.setIcon(QIcon())

    def open_valorant_icon_picker(self):
        switcher = self.parent().switcher if (self.parent() and hasattr(self.parent(), 'switcher')) else None
        picker = ValorantIconPickerDialog(self, switcher_instance=switcher)
        if picker.exec_() == QDialog.Accepted and picker.get_selected_icon_path():
            chosen = picker.get_selected_icon_path()
            self.icon_path_edit.setText(chosen)

    def populate_accounts(self, ordered_list=None):
        if ordered_list is None: ordered_list = sorted(self.accounts_data.keys())
        all_accounts = set(self.accounts_data.keys()); current_accounts = set(ordered_list)
        for name in ordered_list:
            if name in self.accounts_data: self._add_item(name, self.accounts_data[name][0])
        for name in sorted(list(all_accounts - current_accounts)): self._add_item(name, self.accounts_data[name][0])

    def _add_item(self, name, icon_path):
        item = QListWidgetItem(name)
        switcher = self.parent().switcher if (self.parent() and hasattr(self.parent(), 'switcher')) else None
        if switcher:
            account_data = self.accounts_data.get(name)
            rank = account_data[2] if account_data else None
            ui_settings = switcher.get_ima_config().get("ui_settings", {})
            use_rank_icons = ui_settings.get("use_rank_icons", False)
            resolved_icon_path = switcher.get_icon_path_for_account(name, rank, use_rank_icons, account_icon_path=icon_path)
            item.setIcon(switcher.get_qicon_from_path(resolved_icon_path))
        else:
            item.setIcon(QIcon(icon_path or ""))
        self.accounts_list.addItem(item)

    def select_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon Files (*.ico *.png)")
        if path: self.menu_icon_path = path; self.icon_path_edit.setText(path)

    def get_settings(self):
        return {
            "title": self.title_edit.text(), 
            "menu_icon_path": self.menu_icon_path, 
            "ima_menu_path": self.path_edit.text().strip(),
            "ordered_accounts": [self.accounts_list.item(i).text() for i in range(self.accounts_list.count())],
            "show_rank_tips": self.show_rank_tips_toggle.get_state(),
            "show_rr_in_tip": self.show_rr_in_tip_toggle.get_state(),
            "tip_delay": self.tip_delay_slider.value(),
            "include_app_shortcut": self.include_app_shortcut_toggle.get_state(),
            "show_map_planner_in_menu": self.show_map_planner_toggle.get_state()
        }

class PopupDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_widget = QWidget(objectName="popup_widget")
        
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = CustomTitleBar(title, self, is_dialog=True)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 10, 15, 15)

        widget_layout = QVBoxLayout(self.main_widget)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(0)
        widget_layout.addWidget(self.title_bar)
        widget_layout.addWidget(self.content_widget)

        main_v_layout.addWidget(self.main_widget)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.center() - self.rect().center())

class CustomMessageDialog(PopupDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, parent)
        self.resize(380, 190)
        self.setMinimumSize(340, 160)
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 13px; font-weight: 500; padding: 10px 5px;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)
        
        ok_button = QPushButton("OK")
        ok_button.setObjectName("ApplyButton")
        ok_button.setProperty("accent", True)
        ok_button.setMinimumWidth(100)
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

    @classmethod
    def information(cls, parent, title, message):
        dlg = cls(title, message, parent)
        return dlg.exec_()

    @classmethod
    def warning(cls, parent, title, message):
        dlg = cls(title, message, parent)
        return dlg.exec_()

    @classmethod
    def critical(cls, parent, title, message):
        dlg = cls(title, message, parent)
        return dlg.exec_()

class InputDialog(PopupDialog):
    def __init__(self, title, prompt, default_text="", in_game_name_default="", in_game_tag_default="", parent=None):
        super().__init__(title, parent)
        
        self.in_game_name_edit = None
        self.in_game_tag_edit = None

        prompt_label = QLabel(prompt)
        self.content_layout.addWidget(prompt_label)
        
        self.input_field = QLineEdit(default_text)
        self.content_layout.addWidget(self.input_field)

        if in_game_name_default is not None or in_game_tag_default is not None:
            self.content_layout.addWidget(QLabel("In-game Name and Tag (optional):"))
            in_game_name_tag_layout = QHBoxLayout()
            in_game_name_tag_layout.setContentsMargins(0,0,0,0)
            in_game_name_tag_layout.setSpacing(5)

            self.in_game_name_edit = QLineEdit(in_game_name_default)
            self.in_game_name_edit.setPlaceholderText("In-game Name")
            in_game_name_tag_layout.addWidget(self.in_game_name_edit)
            
            in_game_name_tag_layout.addWidget(QLabel("#"))

            self.in_game_tag_edit = QLineEdit(in_game_tag_default)
            self.in_game_tag_edit.setPlaceholderText("Tag")
            in_game_name_tag_layout.addWidget(self.in_game_tag_edit)
            self.content_layout.addLayout(in_game_name_tag_layout)
            self.setFixedSize(350, 250)
        else:
            self.setFixedSize(350, 180)
        
        save_button = QPushButton("Save")
        save_button.setObjectName("ApplyButton")
        save_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

    def get_text(self):
        if self.in_game_name_edit and self.in_game_tag_edit:
            return self.input_field.text().strip(), self.in_game_name_edit.text().strip(), self.in_game_tag_edit.text().strip()
        return self.input_field.text().strip()

class SaveAccountDialog(PopupDialog):
    def __init__(self, parent=None, switcher_instance=None):
        super().__init__("Save Account", parent)
        self.setFixedSize(440, 350)
        self.switcher_instance = switcher_instance

        name_label = QLabel("Enter a name for the current account:")
        name_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.content_layout.addWidget(self.name_edit)

        self.content_layout.addWidget(QLabel("Enter in-game name and tag (optional):"))
        in_game_name_tag_layout = QHBoxLayout()
        in_game_name_tag_layout.setContentsMargins(0,0,0,0)
        in_game_name_tag_layout.setSpacing(5)

        self.in_game_name_edit = QLineEdit()
        self.in_game_name_edit.setPlaceholderText("In-game Name")
        in_game_name_tag_layout.addWidget(self.in_game_name_edit)
        
        in_game_name_tag_layout.addWidget(QLabel("#"))

        self.in_game_tag_edit = QLineEdit()
        self.in_game_tag_edit.setPlaceholderText("Tag")
        in_game_name_tag_layout.addWidget(self.in_game_tag_edit)
        self.content_layout.addLayout(in_game_name_tag_layout)

        self.puuid_edit = QLineEdit()
        self.puuid_edit.setPlaceholderText("PUUID (optional)")
        self.content_layout.addWidget(self.puuid_edit)

        self.content_layout.addWidget(QLabel("Select Game:"))
        self.game_combo = QComboBox()
        
        valorant_icon_path = Path(get_asset_path("valorant.png"))
        lol_icon_path = Path(get_asset_path("lol.png"))

        if valorant_icon_path.exists():
            self.game_combo.addItem(self.switcher_instance.get_qicon_from_path(str(valorant_icon_path)), "Valorant", "valorant")
        else:
            self.game_combo.addItem("Valorant", "valorant")

        if lol_icon_path.exists():
            self.game_combo.addItem(self.switcher_instance.get_qicon_from_path(str(lol_icon_path)), "League of Legends", "lol")
        else:
            self.game_combo.addItem("League of Legends", "lol")

        riot_icon_path = Path(get_asset_path("Riot.png"))
        if riot_icon_path.exists():
            self.game_combo.addItem(self.switcher_instance.get_qicon_from_path(str(riot_icon_path)), "Both", "both")
        else:
            self.game_combo.addItem("Both", "both")
            
        self.content_layout.addWidget(self.game_combo)

        self.content_layout.addSpacing(20)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setObjectName("ApplyButton")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

    def get_details(self):
        return self.name_edit.text().strip(), self.game_combo.currentData(), self.in_game_name_edit.text().strip(), self.in_game_tag_edit.text().strip(), self.puuid_edit.text().strip()

class BackupRestoreSelectionDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Backup and Restore", parent)
        self.setFixedSize(350, 200)
        self.selection = None

        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignCenter)

        backup_button = QPushButton("Backup")
        backup_button.setObjectName("ApplyButton")
        backup_button.setIcon(QIcon(get_asset_path("Backup.png")))
        backup_button.setIconSize(QSize(24, 24))
        backup_button.clicked.connect(lambda: self._set_selection_and_accept("backup"))
        self.content_layout.addWidget(backup_button)

        restore_button = QPushButton("Restore")
        restore_button.setObjectName("ApplyButton")
        restore_button.setIcon(QIcon(get_asset_path("Restore.png")))
        restore_button.setIconSize(QSize(24, 24))
        restore_button.clicked.connect(lambda: self._set_selection_and_accept("restore"))
        self.content_layout.addWidget(restore_button)

    def _set_selection_and_accept(self, selection):
        self.selection = selection
        self.accept()

    def get_selection(self):
        return self.selection

class BackupRestoreDialog(PopupDialog):
    def __init__(self, parent=None, mode='backup'):
        super().__init__(f"{mode.capitalize()} Profiles", parent)
        self.setFixedSize(350, 200)
        self.mode = mode
        self.selection = None

        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignCenter)

        local_button = QPushButton("Local")
        local_button.setObjectName("ApplyButton")
        local_button.setIcon(QIcon(get_asset_path("Local.png")))
        local_button.setIconSize(QSize(24, 24))
        local_button.clicked.connect(lambda: self.set_selection("local"))
        self.content_layout.addWidget(local_button)

        google_drive_button = QPushButton("Google Drive")
        google_drive_button.setObjectName("ApplyButton")
        google_drive_button.setIcon(QIcon(get_asset_path("Google.png")))
        google_drive_button.setIconSize(QSize(24, 24))
        google_drive_button.clicked.connect(lambda: self.set_selection("google_drive"))
        self.content_layout.addWidget(google_drive_button)

    def set_selection(self, selection):
        self.selection = selection
        self.accept()

    def get_selection(self):
        return self.selection

class SettingsDropdownMenu(QWidget):
    def __init__(self, settings_button, actions_handler, parent=None):
        super().__init__(parent)
        self.settings_button = settings_button
        self.actions_handler = actions_handler
        self.is_closing = False

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_widget = QWidget(self)
        self.main_widget.setObjectName("settings_dropdown_widget")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.main_widget.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        add_btn = QPushButton(" Add")
        add_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 18px;")
        add_icon = Path(get_asset_path("Add.png"))
        if add_icon.exists():
            add_btn.setIcon(QIcon(str(add_icon)))
            add_btn.setIconSize(QSize(18, 18))
        add_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.add_account))
        row1.addWidget(add_btn)

        save_btn = QPushButton(" Save")
        save_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 18px;")
        save_icon = Path(get_asset_path("Save.png"))
        if save_icon.exists():
            save_btn.setIcon(QIcon(str(save_icon)))
            save_btn.setIconSize(QSize(18, 18))
        save_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.save_current_account))
        row1.addWidget(save_btn)

        main_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        backup_btn = QPushButton(" Backup")
        backup_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 18px;")
        backup_icon = Path(get_asset_path("Backup.png"))
        if backup_icon.exists():
            backup_btn.setIcon(QIcon(str(backup_icon)))
            backup_btn.setIconSize(QSize(18, 18))
        backup_btn.clicked.connect(lambda: self.execute_action(self.actions_handler._handle_backup_selection))
        row2.addWidget(backup_btn)

        restore_btn = QPushButton(" Restore")
        restore_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 18px;")
        restore_icon = Path(get_asset_path("Restore.png"))
        if restore_icon.exists():
            restore_btn.setIcon(QIcon(str(restore_icon)))
            restore_btn.setIconSize(QSize(18, 18))
        restore_btn.clicked.connect(lambda: self.execute_action(self.actions_handler._handle_restore_selection))
        row2.addWidget(restore_btn)

        main_layout.addLayout(row2)

        ima_btn = QPushButton(" iMA Menu")
        ima_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 18px;")
        ima_icon = Path(get_asset_path("ima.png"))
        if ima_icon.exists():
            ima_btn.setIcon(QIcon(str(ima_icon)))
            ima_btn.setIconSize(QSize(20, 20))
        ima_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.export_ima_menu))
        main_layout.addWidget(ima_btn)

        options_btn = QPushButton(" Options")
        options_btn.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px 18px;")
        options_icon = Path(get_asset_path("Options.png"))
        if options_icon.exists():
            options_btn.setIcon(QIcon(str(options_icon)))
            options_btn.setIconSize(QSize(20, 20))
        options_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.open_options_dialog))
        main_layout.addWidget(options_btn)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_widget)

        self.target_width = 220
        self.target_height = 175
        self.resize(self.target_width, self.target_height)

    def show_animated(self):
        if self.settings_button:
            btn_global = self.settings_button.mapToGlobal(QPoint(0, self.settings_button.height() + 4))
            x_pos = btn_global.x()
            y_pos = btn_global.y()
        else:
            x_pos, y_pos = 100, 100

        self.setGeometry(x_pos, y_pos, self.target_width, 0)
        self.show()
        self.raise_()
        self.activateWindow()

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(180)
        self.anim.setStartValue(QRect(x_pos, y_pos, self.target_width, 0))
        self.anim.setEndValue(QRect(x_pos, y_pos, self.target_width, self.target_height))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

    def execute_action(self, action_func):
        self.close_animated(callback=action_func)

    def close_animated(self, callback=None):
        if self.is_closing:
            return
        self.is_closing = True

        if self.settings_button:
            btn_global = self.settings_button.mapToGlobal(QPoint(0, self.settings_button.height() + 4))
            x_pos = btn_global.x()
            y_pos = btn_global.y()
        else:
            x_pos, y_pos = self.x(), self.y()

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(QRect(x_pos, y_pos, self.target_width, 0))
        self.anim.setEasingCurve(QEasingCurve.InCubic)

        def on_finished():
            self.close()
            if callback:
                callback()

        self.anim.finished.connect(on_finished)
        self.anim.start()

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange and not self.isActiveWindow():
            if not self.is_closing:
                self.close_animated()
        super().changeEvent(event)

class SettingsDialog:
    def __init__(self, actions, parent):
        self.parent = parent
    def exec_(self):
        if hasattr(self.parent, 'settings_handler'):
            menu = SettingsDropdownMenu(
                settings_button=getattr(self.parent.title_bar, 'settings_button', None),
                actions_handler=self.parent.settings_handler,
                parent=self.parent
            )
            menu.show_animated()

class OptionsDialog(PopupDialog):
    settings_applied = pyqtSignal()

    def __init__(self, switcher_instance, parent=None):
        super().__init__("Options", parent)
        self.switcher = switcher_instance
        self.resize(780, 680)
        self.setMinimumSize(720, 580)

        open_folder_btn = HoverButton()
        open_folder_btn.setFixedSize(30, 30)
        open_folder_btn.setIconSize(QSize(18, 18))
        open_folder_path = get_asset_path("Open.png")
        if os.path.exists(open_folder_path):
            open_folder_btn.setIcon(QIcon(open_folder_path))
        open_folder_btn.setToolTip("Open Profiles Folder")
        open_folder_btn.setStyleSheet("QPushButton { background-color: #4f4a4b; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 2)
        open_folder_btn.setGraphicsEffect(shadow)
        open_folder_btn.clicked.connect(self.open_profiles_folder)
        self.title_bar.add_header_button(open_folder_btn)

        self.quality_settings_map = {
            "sg.ViewDistanceQuality": "View Distance", "sg.AntiAliasingQuality": "Anti-Aliasing",
            "sg.ShadowQuality": "Shadows", "sg.PostProcessQuality": "Post-Processing",
            "sg.TextureQuality": "Textures", "sg.EffectsQuality": "Effects",
            "sg.FoliageQuality": "Foliage", "sg.ShadingQuality": "Shading",
        }
        self.riot_quality_settings_map = {
            "EAresIntSettingName::MaterialQuality": "Material Quality",
            "EAresIntSettingName::TextureQuality": "Texture Quality",
            "EAresIntSettingName::DetailQuality": "Detail Quality",
            "EAresIntSettingName::UIQuality": "UI Quality",
            "EAresIntSettingName::NvidiaReflexLowLatencySetting": "Nvidia Reflex",
        }
        self.audio_settings_map = {
            "EAresFloatSettingName::OverallVolume": "Main Volume",
            "EAresFloatSettingName::SoundEffectsVolume": "Sound Effects",
            "EAresFloatSettingName::VoiceOverVolume": "Voice-Over",
            "EAresFloatSettingName::VideoVolume": "Store Video",
            "EAresFloatSettingName::AllMusicOverallVolume": "All Music",
            "EAresFloatSettingName::MenuAndLobbyMusicVolume": "Menu & Lobby Music",
            "EAresFloatSettingName::CharacterSelectMusicVolume": "Agent Select Music",
            "EAresIntSettingName::MicVolume": "Mic Volume",
            "EAresIntSettingName::VoiceVolume": "Incoming Volume",
            "EAresBoolSettingName::PushToTalkEnabled": "Party Voice Activation",
            "EAresBoolSettingName::EnableHRTF": "HRTF"
        }
        self.riot_combo_boxes = {}
        self.audio_controls = {}
        self.spin_boxes = {}

        self.content_layout.setSpacing(10)
        
        # Horizontal Body Layout: Sidebar + Stack
        body_layout = QHBoxLayout()
        body_layout.setSpacing(15)

        # Left Sidebar Navigation List
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(170)
        body_layout.addWidget(self.nav_list)

        # Right Pages Stack
        self.pages_widget = QStackedWidget()
        body_layout.addWidget(self.pages_widget)

        self.content_layout.addLayout(body_layout)

        # Setup pages
        self.setup_ui_tab()          # Page 0: Display
        self.setup_account_tab()     # Page 1: Rank & Account
        self.setup_graphics_tab()    # Page 2: Graphics
        self.setup_audio_tab()       # Page 3: Audio
        self.setup_advanced_tab()    # Page 4: Quality Presets & Riot Client
        self.setup_crosshairs_tab()  # Page 5: Crosshair Manager
        self.setup_ima_menu_tab()    # Page 6: iMA Menu
        self.setup_map_planner_tab() # Page 7: Map Planner
        self.setup_updates_tab()     # Page 8: Software Updates

        self.nav_list.currentRowChanged.connect(self.pages_widget.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e0d6d1; font-size: 12px; padding-top: 5px;")
        self.content_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        apply_button = QPushButton("Apply")
        apply_button.setProperty("accent", True)
        apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

        self.populate_account_combos()
        self.load_current_settings()

    def add_page(self, title, icon_file, widget):
        item = QListWidgetItem(title)
        icon_p = get_asset_path(icon_file)
        if Path(icon_p).exists():
            item.setIcon(QIcon(icon_p))
        self.nav_list.addItem(item)
        self.pages_widget.addWidget(widget)

    def populate_account_combos(self):
        accounts = list(self.switcher.get_saved_accounts().keys())
        if hasattr(self, 'crosshair_account_combo'):
            self.crosshair_account_combo.blockSignals(True)
            self.crosshair_account_combo.clear()
            self.crosshair_account_combo.addItems(accounts)
            self.crosshair_account_combo.blockSignals(False)

    def setup_account_tab(self):
        account_tab = QWidget()
        main_layout = QVBoxLayout(account_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        group_style = """
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #FFFFFF; }
        """
        combo_style = """
            QComboBox { 
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1; font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; border: 1px solid #c89f68; selection-background-color: #c89f68; color: #e0d6d1; selection-color: #2c2a2b; padding: 5px;
            }
        """

        rank_update_group = QGroupBox("Rank Update Settings")
        rank_update_group.setStyleSheet(group_style)
        rank_update_layout = QGridLayout(rank_update_group)
        rank_update_layout.setSpacing(10)

        self.auto_rank_update_toggle = RadioButtonGroup("On", "Off")
        rank_update_layout.addWidget(QLabel("Auto Rank Update:"), 0, 0)
        rank_update_layout.addWidget(self.auto_rank_update_toggle, 0, 1)

        rank_update_layout.addWidget(QLabel("Rank Check Region:"), 1, 0)
        self.rank_check_region_combo = QComboBox()
        self.rank_check_region_combo.addItem("Europe (eu)", "eu")
        self.rank_check_region_combo.addItem("North America (na)", "na")
        self.rank_check_region_combo.addItem("Asia Pacific (ap)", "ap")
        self.rank_check_region_combo.addItem("Brazil (br)", "br")
        self.rank_check_region_combo.addItem("Korea (kr)", "kr")
        self.rank_check_region_combo.addItem("Latin America (latam)", "latam")
        self.rank_check_region_combo.setStyleSheet(combo_style)
        rank_update_layout.addWidget(self.rank_check_region_combo, 1, 1)
        main_layout.addWidget(rank_update_group)

        rank_features_group = QGroupBox("Rank Features")
        rank_features_group.setStyleSheet(group_style)
        rank_features_layout = QGridLayout(rank_features_group)
        rank_features_layout.setSpacing(10)

        self.use_rank_icons_toggle = RadioButtonGroup("On", "Off")
        rank_features_layout.addWidget(QLabel("Use Rank for Account Icon:"), 0, 0)
        rank_features_layout.addWidget(self.use_rank_icons_toggle, 0, 1)

        main_layout.addWidget(rank_features_group)

        notif_group = QGroupBox("Notifications")
        notif_group.setStyleSheet(group_style)
        notif_layout = QGridLayout(notif_group)
        notif_layout.setSpacing(10)

        self.show_splash_notification_toggle = RadioButtonGroup("On", "Off")
        notif_layout.addWidget(QLabel("Show Splash Notification:"), 0, 0)
        notif_layout.addWidget(self.show_splash_notification_toggle, 0, 1)

        preview_splash_btn = QPushButton("Preview Splash Screen")
        preview_splash_btn.setObjectName("ApplyButton")
        preview_splash_btn.clicked.connect(self.preview_splash_screen)
        notif_layout.addWidget(preview_splash_btn, 1, 0, 1, 2)
        main_layout.addWidget(notif_group)

        main_layout.addStretch()
        self.add_page("Rank & Account", "Settings.png", account_tab)

    def setup_graphics_tab(self):
        graphics_tab = QWidget()
        layout = QVBoxLayout(graphics_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["Default", "Fullscreen", "Windowed Fullscreen", "Windowed"])
        form_layout.addRow(QLabel("Display Mode:"), self.display_mode_combo)
        
        quality_keys = [
            "EAresIntSettingName::MaterialQuality", "EAresIntSettingName::TextureQuality",
            "EAresIntSettingName::DetailQuality", "EAresIntSettingName::UIQuality",
            "EAresIntSettingName::NvidiaReflexLowLatencySetting"
        ]
        for key in quality_keys:
            combo_box = QComboBox()
            if key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                combo_box.addItems(["Off", "On", "On + Boost"])
            else:
                combo_box.addItems(["Low", "Med", "High"])
            
            self.riot_combo_boxes[key] = combo_box
            form_layout.addRow(QLabel(self.riot_quality_settings_map[key] + ":"), combo_box)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        self.add_page("Graphics", "Graphics.png", graphics_tab)

    def setup_audio_tab(self):
        audio_tab = QWidget()
        main_layout = QVBoxLayout(audio_tab)
        main_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignTop)

        general_group = QGroupBox("General Volume")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(10)
        general_layout.setLabelAlignment(Qt.AlignLeft)
        general_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        general_keys = ["EAresFloatSettingName::OverallVolume", "EAresFloatSettingName::SoundEffectsVolume", "EAresFloatSettingName::VoiceOverVolume", "EAresFloatSettingName::VideoVolume"]
        for key in general_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            lbl = QLabel(self.audio_settings_map[key] + ":")
            lbl.setMinimumWidth(110)
            general_layout.addRow(lbl, slider)
        main_layout.addWidget(general_group)

        music_group = QGroupBox("Music")
        music_layout = QFormLayout(music_group)
        music_layout.setSpacing(10)
        music_layout.setLabelAlignment(Qt.AlignLeft)
        music_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        music_keys = ["EAresFloatSettingName::AllMusicOverallVolume", "EAresFloatSettingName::MenuAndLobbyMusicVolume", "EAresFloatSettingName::CharacterSelectMusicVolume"]
        for key in music_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            lbl = QLabel(self.audio_settings_map[key] + ":")
            lbl.setMinimumWidth(110)
            music_layout.addRow(lbl, slider)
        main_layout.addWidget(music_group)
        
        voice_group = QGroupBox("Voice Communication")
        voice_layout = QFormLayout(voice_group)
        voice_layout.setSpacing(10)
        voice_layout.setLabelAlignment(Qt.AlignLeft)
        voice_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        voice_keys = ["EAresIntSettingName::MicVolume", "EAresIntSettingName::VoiceVolume"]
        for key in voice_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            lbl = QLabel(self.audio_settings_map[key] + ":")
            lbl.setMinimumWidth(110)
            voice_layout.addRow(lbl, slider)
        
        self.audio_controls["EAresBoolSettingName::PushToTalkEnabled"] = RadioButtonGroup("Push to Talk", "Automatic")
        lbl_ptt = QLabel(self.audio_settings_map["EAresBoolSettingName::PushToTalkEnabled"] + ":")
        lbl_ptt.setMinimumWidth(110)
        voice_layout.addRow(lbl_ptt, self.audio_controls["EAresBoolSettingName::PushToTalkEnabled"])
        
        self.audio_controls["EAresBoolSettingName::EnableHRTF"] = RadioButtonGroup("On", "Off")
        lbl_hrtf = QLabel(self.audio_settings_map["EAresBoolSettingName::EnableHRTF"] + ":")
        lbl_hrtf.setMinimumWidth(110)
        voice_layout.addRow(lbl_hrtf, self.audio_controls["EAresBoolSettingName::EnableHRTF"])
        main_layout.addWidget(voice_group)

        main_layout.addStretch()
        self.add_page("Audio", "Audio.png", audio_tab)

    def setup_advanced_tab(self):
        advanced_tab = QWidget()
        layout = QVBoxLayout(advanced_tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        preset_buttons_layout = QHBoxLayout()
        recommended_button = QPushButton("Recommended (Low)")
        recommended_button.setObjectName("ApplyButton")
        default_button = QPushButton("Default (High)")
        default_button.setObjectName("ApplyButton")
        
        recommended_button.clicked.connect(lambda: self.set_all_qualities(0))
        default_button.clicked.connect(lambda: self.set_all_qualities(3))

        preset_buttons_layout.addWidget(recommended_button)
        preset_buttons_layout.addWidget(default_button)
        layout.addLayout(preset_buttons_layout)
        layout.addSpacing(15)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        items = list(self.quality_settings_map.items())
        num_rows = (len(items) + 1) // 2 

        for i, (key, display_name) in enumerate(items):
            row, col = i % num_rows, (i // num_rows) * 2
            
            label = QLabel(display_name + ":")
            grid_layout.addWidget(label, row, col)
            
            spin_box = QSpinBox()
            spin_box.setRange(0, 3)
            spin_box.setFixedWidth(60)
            self.spin_boxes[key] = spin_box
            grid_layout.addWidget(spin_box, row, col + 1, Qt.AlignLeft)

        layout.addLayout(grid_layout)

        riot_client_group = QGroupBox("Riot Client Behavior")
        riot_client_layout = QGridLayout(riot_client_group)
        riot_client_layout.setSpacing(10)

        self.show_riot_client_toggle = RadioButtonGroup("Show", "Hide")
        riot_client_layout.addWidget(QLabel("Riot Client Window:"), 0, 0)
        riot_client_layout.addWidget(self.show_riot_client_toggle, 0, 1)
        layout.addWidget(riot_client_group)

        layout.addStretch()
        self.add_page("Quality Presets", "Advanced.png", advanced_tab)

    def setup_ui_tab(self):
        ui_tab = QWidget()
        main_layout = QVBoxLayout(ui_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        group_style = """
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #FFFFFF; }
        """

        top_group = QGroupBox("Show in UI")
        top_layout = QGridLayout(top_group)
        top_layout.setSpacing(10)

        self.show_game_icons_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Game Icon:"), 0, 0)
        top_layout.addWidget(self.show_game_icons_toggle, 0, 1)

        self.show_rank_icon_left_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Rank Icon:"), 1, 0)
        top_layout.addWidget(self.show_rank_icon_left_toggle, 1, 1)

        self.show_name_tag_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Name#Tag:"), 2, 0)
        top_layout.addWidget(self.show_name_tag_toggle, 2, 1)

        self.show_current_rr_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Current RR:"), 3, 0)
        top_layout.addWidget(self.show_current_rr_toggle, 3, 1)

        self.show_last_game_rr_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Last Game's RR:"), 4, 0)
        top_layout.addWidget(self.show_last_game_rr_toggle, 4, 1)

        self.show_last_match_info_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Last Game's Agent & Map:"), 5, 0)
        top_layout.addWidget(self.show_last_match_info_toggle, 5, 1)

        self.show_map_background_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Account Map Background:"), 6, 0)
        top_layout.addWidget(self.show_map_background_toggle, 6, 1)

        bottom_group = QGroupBox("Layout Settings")
        bottom_layout = QGridLayout(bottom_group)
        bottom_layout.setSpacing(10)

        bottom_layout.addWidget(QLabel("Grid Size (Columns):"), 0, 0)
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        bottom_layout.addWidget(self.grid_size_combo, 0, 1)

        bottom_layout.addWidget(QLabel("UI Theme:"), 1, 0)
        self.theme_combo = QComboBox()
        themes_map = get_available_themes()
        for key, name in themes_map.items():
            self.theme_combo.addItem(name, key)
        bottom_layout.addWidget(self.theme_combo, 1, 1)

        main_layout.addWidget(top_group)
        main_layout.addWidget(bottom_group)
        main_layout.addStretch()

        self.add_page("Display", "app_icon.png", ui_tab)

    def setup_crosshairs_tab(self):
        crosshair_page = QWidget()
        layout = QVBoxLayout(crosshair_page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        combo_style = """
            QComboBox { 
                background-color: #353233; border: 1px solid #4a4647; border-radius: 8px; padding: 6px 10px; color: #e0d6d1; font-weight: bold;
            }
            QComboBox:hover { border-color: #c89f68; }
            QComboBox QAbstractItemView { 
                background-color: #2c2a2b; border: 1px solid #4a4647; selection-background-color: #c89f68; color: #e0d6d1; selection-color: #2c2a2b; padding: 4px;
            }
        """

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        top_bar.addWidget(QLabel("Account:"))
        self.crosshair_account_combo = QComboBox()
        self.crosshair_account_combo.setStyleSheet(combo_style)
        top_bar.addWidget(self.crosshair_account_combo, 1)

        top_bar.addWidget(QLabel("Profile:"))
        self.crosshair_profile_combo = QComboBox()
        self.crosshair_profile_combo.setStyleSheet(combo_style)
        top_bar.addWidget(self.crosshair_profile_combo, 1)

        self.crosshair_preset_combo = QComboBox()
        self.crosshair_preset_combo.setStyleSheet(combo_style)
        self.crosshair_preset_combo.addItem("Presets...")
        for p_name in VALORANT_CROSSHAIR_PRESETS.keys():
            self.crosshair_preset_combo.addItem(p_name)
        self.crosshair_preset_combo.currentIndexChanged.connect(self.on_crosshair_preset_selected)
        top_bar.addWidget(self.crosshair_preset_combo, 1)

        layout.addLayout(top_bar)

        main_split = QHBoxLayout()
        main_split.setSpacing(14)

        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        canvas_frame = QWidget()
        canvas_frame.setStyleSheet("background-color: transparent; border: 1px solid #4a4647; border-radius: 12px;")
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.ch_canvas = CrosshairCanvasWidget()
        canvas_layout.addWidget(self.ch_canvas)
        left_col.addWidget(canvas_frame)

        bg_bar = QHBoxLayout()
        bg_bar.setSpacing(4)
        bg_bar.addWidget(QLabel("BG:"))
        self.ch_bg_combo = QComboBox()
        self.ch_bg_combo.setStyleSheet(combo_style)
        self.ch_bg_combo.addItems(["Dark Grid", "Light Grid", "Pure Black"])
        bg_bar.addWidget(self.ch_bg_combo, 1)

        bg_bar.addWidget(QLabel("Zoom:"))
        self.ch_zoom_combo = QComboBox()
        self.ch_zoom_combo.setStyleSheet(combo_style)
        self.ch_zoom_combo.addItems(["1x", "2x", "4x", "8x"])
        self.ch_zoom_combo.setCurrentIndex(1)
        bg_bar.addWidget(self.ch_zoom_combo, 1)
        left_col.addLayout(bg_bar)
        left_col.addStretch()

        main_split.addLayout(left_col, 0)

        self.ch_controls_tab = QTabWidget()
        self.ch_controls_tab.setUsesScrollButtons(False)

        # Tab 1: Primary & Color
        tab_color = QWidget()
        layout_color = QFormLayout(tab_color)
        layout_color.setSpacing(6)
        
        self.ch_color_combo = QComboBox()
        self.ch_color_combo.setStyleSheet(combo_style)
        self.ch_color_combo.addItems(["White", "Green", "Yellow Green", "Green Yellow", "Yellow", "Cyan", "Pink", "Red", "Custom Hex"])
        layout_color.addRow(QLabel("Color Preset:"), self.ch_color_combo)

        self.ch_custom_hex_edit = QLineEdit("#00FF88FF")
        self.ch_custom_hex_edit.setStyleSheet("background-color: #353233; border: 1px solid #4a4647; border-radius: 6px; padding: 4px 8px; color: #e0d6d1;")
        layout_color.addRow(QLabel("Custom Hex:"), self.ch_custom_hex_edit)

        self.ch_dot_enable_cb = QCheckBox("Enable Center Dot")
        layout_color.addRow(self.ch_dot_enable_cb)

        self.ch_dot_opacity_slider = ValueSlider(0, 100)
        layout_color.addRow(QLabel("Dot Opacity:"), self.ch_dot_opacity_slider)

        self.ch_dot_size_slider = ValueSlider(1, 6)
        layout_color.addRow(QLabel("Dot Size (px):"), self.ch_dot_size_slider)

        self.ch_controls_tab.addTab(tab_color, "Color & Dot")

        # Tab 2: Outlines
        tab_outlines = QWidget()
        layout_outlines = QFormLayout(tab_outlines)
        layout_outlines.setSpacing(6)

        self.ch_outline_enable_cb = QCheckBox("Enable Outlines")
        layout_outlines.addRow(self.ch_outline_enable_cb)

        self.ch_outline_opacity_slider = ValueSlider(0, 100)
        layout_outlines.addRow(QLabel("Outline Opacity:"), self.ch_outline_opacity_slider)

        self.ch_outline_thick_slider = ValueSlider(1, 6)
        layout_outlines.addRow(QLabel("Outline Thickness:"), self.ch_outline_thick_slider)

        self.ch_controls_tab.addTab(tab_outlines, "Outlines")

        # Tab 3: Inner Lines
        tab_inner = QWidget()
        layout_inner = QFormLayout(tab_inner)
        layout_inner.setSpacing(5)

        self.ch_inner_enable_cb = QCheckBox("Show Inner Lines")
        layout_inner.addRow(self.ch_inner_enable_cb)

        self.ch_inner_opacity_slider = ValueSlider(0, 100)
        layout_inner.addRow(QLabel("Opacity:"), self.ch_inner_opacity_slider)

        self.ch_inner_len_slider = ValueSlider(0, 20)
        layout_inner.addRow(QLabel("Length:"), self.ch_inner_len_slider)

        self.ch_inner_thick_slider = ValueSlider(1, 10)
        layout_inner.addRow(QLabel("Thickness:"), self.ch_inner_thick_slider)

        self.ch_inner_off_slider = ValueSlider(0, 20)
        layout_inner.addRow(QLabel("Offset:"), self.ch_inner_off_slider)

        self.ch_inner_top_cb = QCheckBox("Show Top Line")
        layout_inner.addRow(self.ch_inner_top_cb)

        self.ch_controls_tab.addTab(tab_inner, "Inner")

        # Tab 4: Outer Lines
        tab_outer = QWidget()
        layout_outer = QFormLayout(tab_outer)
        layout_outer.setSpacing(5)

        self.ch_outer_enable_cb = QCheckBox("Show Outer Lines")
        layout_outer.addRow(self.ch_outer_enable_cb)

        self.ch_outer_opacity_slider = ValueSlider(0, 100)
        layout_outer.addRow(QLabel("Opacity:"), self.ch_outer_opacity_slider)

        self.ch_outer_len_slider = ValueSlider(0, 20)
        layout_outer.addRow(QLabel("Length:"), self.ch_outer_len_slider)

        self.ch_outer_thick_slider = ValueSlider(1, 10)
        layout_outer.addRow(QLabel("Thickness:"), self.ch_outer_thick_slider)

        self.ch_outer_off_slider = ValueSlider(0, 20)
        layout_outer.addRow(QLabel("Offset:"), self.ch_outer_off_slider)

        self.ch_outer_top_cb = QCheckBox("Show Top Line")
        layout_outer.addRow(self.ch_outer_top_cb)

        self.ch_controls_tab.addTab(tab_outer, "Outer")

        main_split.addWidget(self.ch_controls_tab, 1)
        layout.addLayout(main_split)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        btn_import = QPushButton("Import Code")
        btn_import.clicked.connect(self.on_import_crosshair_code)
        action_bar.addWidget(btn_import)

        btn_export = QPushButton("Copy In-Game Code")
        btn_export.clicked.connect(self.on_export_crosshair_code)
        action_bar.addWidget(btn_export)

        action_bar.addStretch()

        btn_save = QPushButton("Save to Account")
        btn_save.setObjectName("ApplyButton")
        btn_save.clicked.connect(self.on_save_crosshairs_to_account)
        action_bar.addWidget(btn_save)

        layout.addLayout(action_bar)

        self.ch_bg_combo.currentIndexChanged.connect(lambda: self.ch_canvas.set_bg(self.ch_bg_combo.currentText()))
        self.ch_zoom_combo.currentIndexChanged.connect(lambda: self.ch_canvas.set_zoom(
            8.0 if "8" in self.ch_zoom_combo.currentText() else
            4.0 if "4" in self.ch_zoom_combo.currentText() else
            2.0 if "2" in self.ch_zoom_combo.currentText() else 1.0
        ))

        self.ch_updating_controls = False
        for widget in [self.ch_color_combo, self.ch_custom_hex_edit, self.ch_dot_enable_cb,
                       self.ch_dot_opacity_slider, self.ch_dot_size_slider, self.ch_outline_enable_cb,
                       self.ch_outline_opacity_slider, self.ch_outline_thick_slider, self.ch_inner_enable_cb,
                       self.ch_inner_opacity_slider, self.ch_inner_len_slider, self.ch_inner_thick_slider,
                       self.ch_inner_off_slider, self.ch_inner_top_cb, self.ch_outer_enable_cb,
                       self.ch_outer_opacity_slider, self.ch_outer_len_slider, self.ch_outer_thick_slider,
                       self.ch_outer_off_slider, self.ch_outer_top_cb]:
            if isinstance(widget, ValueSlider):
                widget.valueChanged.connect(self.update_active_profile_from_controls)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self.update_active_profile_from_controls)
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self.update_active_profile_from_controls)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.update_active_profile_from_controls)

        self.crosshair_account_combo.currentIndexChanged.connect(self.load_account_crosshair_info)
        self.crosshair_profile_combo.currentIndexChanged.connect(self.on_crosshair_profile_selected)

        self.add_page("Crosshair", "crosshair.png", crosshair_page)

    def setup_ima_menu_tab(self):
        ima_tab = QWidget()
        main_layout = QVBoxLayout(ima_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        group_style = """
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #FFFFFF; }
        """

        path_group = QGroupBox("iMA Menu Installation")
        path_group.setStyleSheet(group_style)
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(6)

        self.options_ima_path_stack = QStackedWidget()

        detected_widget = QWidget()
        detected_layout = QVBoxLayout(detected_widget)
        detected_layout.setContentsMargins(0, 0, 0, 0)
        detected_layout.setSpacing(6)

        path_input_layout = QHBoxLayout()
        path_input_layout.setSpacing(8)

        self.options_ima_path_edit = QLineEdit()
        self.options_ima_path_edit.setPlaceholderText("Select iMA Menu folder or its parent directory")
        self.options_ima_path_edit.textChanged.connect(self.update_options_ima_path_status)
        path_input_layout.addWidget(self.options_ima_path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("ApplyButton")
        browse_btn.clicked.connect(self.browse_options_ima_path)
        path_input_layout.addWidget(browse_btn)

        detect_btn = QPushButton("Detect Active")
        detect_btn.setToolTip("Detect active registered iMA Menu from Windows Registry")
        detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; color: #e0d6d1; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: 1px solid #6b6365;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #c89f68; }
        """)
        detect_btn.clicked.connect(self.detect_options_ima_registered_path)
        path_input_layout.addWidget(detect_btn)
        detected_layout.addLayout(path_input_layout)

        self.options_ima_status_label = QLabel()
        self.options_ima_status_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        detected_layout.addWidget(self.options_ima_status_label)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setSpacing(8)

        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; color: #e0d6d1; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: 1px solid #6b6365;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #c89f68; }
        """)
        open_folder_btn.clicked.connect(self.open_options_ima_folder)
        action_buttons_layout.addWidget(open_folder_btn)

        open_valo_btn = QPushButton("Open valo.nss")
        open_valo_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; color: #e0d6d1; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: 1px solid #6b6365;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #c89f68; }
        """)
        open_valo_btn.clicked.connect(self.open_options_valo_nss)
        action_buttons_layout.addWidget(open_valo_btn)
        action_buttons_layout.addStretch()
        detected_layout.addLayout(action_buttons_layout)

        self.options_ima_path_stack.addWidget(detected_widget)

        missing_widget = QWidget()
        missing_layout = QVBoxLayout(missing_widget)
        missing_layout.setContentsMargins(4, 4, 4, 4)
        missing_layout.setSpacing(6)

        banner_title = QLabel("Install iMA Menu to use this feature")
        banner_title.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        missing_layout.addWidget(banner_title)

        banner_desc = QLabel("iMA Menu is a highly customizable Context menu enhancer tool with smart and beautiful features.")
        banner_desc.setWordWrap(True)
        banner_desc.setStyleSheet("color: #e0d6d1; font-size: 11px;")
        missing_layout.addWidget(banner_desc)

        banner_btn_layout = QHBoxLayout()
        banner_btn_layout.setSpacing(8)

        download_btn = QPushButton("Download")
        download_btn.setObjectName("ApplyButton")
        download_btn.clicked.connect(download_and_open_ima_menu)
        banner_btn_layout.addWidget(download_btn)

        detect_ima_btn = QPushButton("Detect iMA Menu")
        detect_ima_btn.clicked.connect(self.detect_options_ima_registered_path)
        banner_btn_layout.addWidget(detect_ima_btn)

        locate_btn = QPushButton("Browse...")
        locate_btn.clicked.connect(self.browse_options_ima_path)
        banner_btn_layout.addWidget(locate_btn)
        banner_btn_layout.addStretch()

        missing_layout.addLayout(banner_btn_layout)

        self.options_ima_path_stack.addWidget(missing_widget)

        path_layout.addWidget(self.options_ima_path_stack)
        main_layout.addWidget(path_group)

        menu_settings_group = QGroupBox("iMA Menu Configuration")
        menu_settings_group.setStyleSheet(group_style)
        menu_settings_layout = QGridLayout(menu_settings_group)
        menu_settings_layout.setSpacing(10)

        menu_settings_layout.addWidget(QLabel("Menu Title:"), 0, 0)
        self.options_ima_title_edit = QLineEdit("Valorant")
        menu_settings_layout.addWidget(self.options_ima_title_edit, 0, 1)

        menu_settings_layout.addWidget(QLabel("Menu Icon:"), 1, 0)
        icon_input_layout = QHBoxLayout()
        icon_input_layout.setSpacing(8)
        self.options_ima_icon_edit = QLineEdit()
        self.options_ima_icon_edit.setPlaceholderText("Optional menu icon path")
        self.options_ima_icon_edit.textChanged.connect(self.update_options_ima_icon_preview)
        
        self.options_ima_icon_preview = QPushButton()
        self.options_ima_icon_preview.setFixedSize(36, 36)
        self.options_ima_icon_preview.setIconSize(QSize(24, 24))
        self.options_ima_icon_preview.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #d9b68b; }
        """)
        self.options_ima_icon_preview.clicked.connect(self.open_options_ima_icon_picker)

        browse_icon_btn = QPushButton("Browse...")
        browse_icon_btn.setObjectName("ApplyButton")
        browse_icon_btn.clicked.connect(self.browse_options_ima_icon)

        icon_input_layout.addWidget(self.options_ima_icon_edit)
        icon_input_layout.addWidget(self.options_ima_icon_preview)
        icon_input_layout.addWidget(browse_icon_btn)
        menu_settings_layout.addLayout(icon_input_layout, 1, 1)

        self.options_show_rank_tips_toggle = RadioButtonGroup("On", "Off")
        menu_settings_layout.addWidget(QLabel("Show Rank Tips:"), 2, 0)
        menu_settings_layout.addWidget(self.options_show_rank_tips_toggle, 2, 1)

        self.options_show_rr_in_tip_toggle = RadioButtonGroup("On", "Off")
        menu_settings_layout.addWidget(QLabel("Show Current RR in Tip:"), 3, 0)
        menu_settings_layout.addWidget(self.options_show_rr_in_tip_toggle, 3, 1)

        self.options_tip_delay_slider = ValueSlider(0.0, 2.0, 0.1)
        menu_settings_layout.addWidget(QLabel("Tip Delay (seconds):"), 4, 0)
        menu_settings_layout.addWidget(self.options_tip_delay_slider, 4, 1)

        self.options_include_app_shortcut_toggle = RadioButtonGroup("On", "Off")
        menu_settings_layout.addWidget(QLabel("Add iMA Switcher to Menu:"), 5, 0)
        menu_settings_layout.addWidget(self.options_include_app_shortcut_toggle, 5, 1)

        self.options_show_map_planner_toggle = RadioButtonGroup("On", "Off")
        menu_settings_layout.addWidget(QLabel("Show Map Planner in Menu:"), 6, 0)
        menu_settings_layout.addWidget(self.options_show_map_planner_toggle, 6, 1)

        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_ima_btn = QPushButton("Export to iMA Menu")
        export_ima_btn.setObjectName("ApplyButton")
        export_ima_btn.clicked.connect(self.export_ima_menu_from_tab)
        export_layout.addWidget(export_ima_btn)
        menu_settings_layout.addLayout(export_layout, 7, 0, 1, 2)

        main_layout.addWidget(menu_settings_group)
        main_layout.addStretch()

        self.add_page("iMA Menu", "ima.png", ima_tab)

    def browse_options_ima_path(self):
        initial = self.options_ima_path_edit.text().strip()
        chosen = QFileDialog.getExistingDirectory(self, "Select iMA Menu Folder or Parent Folder", initial)
        if chosen:
            resolved = self.switcher.resolve_ima_menu_folder(chosen)
            self.options_ima_path_edit.setText(str(resolved))

    def detect_options_ima_registered_path(self):
        detected = self.switcher.get_registered_ima_shell_path() or self.switcher.find_ima_menu_path()
        if detected:
            self.options_ima_path_edit.setText(str(detected))
            self.update_options_ima_path_status(str(detected))
            self.status_label.setText(f"iMA Menu detected at: {detected}")
        else:
            self.update_options_ima_path_status("")
            self.status_label.setText("iMA Menu installation could not be detected. Please install or click 'Browse...'.")

    def update_options_ima_path_status(self, text=None):
        path_val = (text if text is not None else self.options_ima_path_edit.text()).strip()
        if not path_val:
            self.options_ima_path_stack.setCurrentIndex(1)
            return
        resolved = self.switcher.resolve_ima_menu_folder(path_val)
        is_reg, active_reg, _ = self.switcher.get_ima_menu_registration_info(resolved)
        if not resolved or not Path(resolved).exists():
            self.options_ima_path_stack.setCurrentIndex(1)
        else:
            self.options_ima_path_stack.setCurrentIndex(0)
            if is_reg:
                self.options_ima_status_label.setText(f"<font color='#2ecc71'>● Active & Registered in Windows Shell: {resolved}</font>")
            elif active_reg:
                self.options_ima_status_label.setText(f"<font color='#f39c12'>● Custom Path (Live shell registered at: {active_reg})</font>")
            else:
                self.options_ima_status_label.setText(f"<font color='#f39c12'>● Custom Path (Shell not registered)</font>")

    def open_options_ima_folder(self):
        path_val = self.options_ima_path_edit.text().strip()
        resolved = self.switcher.resolve_ima_menu_folder(path_val) if path_val else self.switcher.find_ima_menu_path()
        if resolved and Path(resolved).exists():
            try:
                os.startfile(str(resolved))
            except Exception as e:
                CustomMessageDialog.warning(self, "Error Opening Folder", f"Could not open folder:\n{e}")
        else:
            CustomMessageDialog.warning(self, "Folder Not Found", "The iMA Menu folder does not exist.")

    def open_options_valo_nss(self):
        path_val = self.options_ima_path_edit.text().strip()
        resolved = self.switcher.resolve_ima_menu_folder(path_val) if path_val else self.switcher.find_ima_menu_path()
        if resolved and Path(resolved).exists():
            valo_path = Path(resolved) / "imports" / "valo.nss"
            if valo_path.exists():
                try:
                    os.startfile(str(valo_path))
                except Exception as e:
                    CustomMessageDialog.warning(self, "Error Opening File", f"Could not open valo.nss:\n{e}")
            else:
                CustomMessageDialog.warning(self, "File Not Found", f"valo.nss was not found at:\n{valo_path}\n\nPlease click 'Export to iMA Menu' first to generate the configuration.")
        else:
            CustomMessageDialog.warning(self, "Folder Not Found", "Please specify or detect a valid iMA Menu folder first.")

    def update_options_ima_icon_preview(self, path_text):
        clean_path = path_text.strip()
        if clean_path and Path(clean_path).exists():
            self.options_ima_icon_preview.setIcon(self.switcher.get_qicon_from_path(clean_path))
        else:
            self.options_ima_icon_preview.setIcon(QIcon())

    def browse_options_ima_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon Files (*.ico *.png)")
        if path:
            self.options_ima_icon_edit.setText(path)

    def open_options_ima_icon_picker(self):
        picker = ValorantIconPickerDialog(self, switcher_instance=self.switcher)
        if picker.exec_() == QDialog.Accepted and picker.get_selected_icon_path():
            self.options_ima_icon_edit.setText(picker.get_selected_icon_path())

    def export_ima_menu_from_tab(self):
        accounts_data = self.switcher.get_saved_accounts()
        if not accounts_data:
            CustomMessageDialog.warning(self, "No Accounts", "You must save at least one account before exporting.")
            return

        raw_path = self.options_ima_path_edit.text().strip()
        resolved_ima_path = self.switcher.resolve_ima_menu_folder(raw_path) if raw_path else self.switcher.find_ima_menu_path()
        if not resolved_ima_path or not Path(resolved_ima_path).exists():
            CustomMessageDialog.warning(self, "Path Error", "Please specify or detect a valid iMA Menu folder first.")
            return

        ima_config = self.switcher.get_ima_config()
        output_dir = resolved_ima_path / "imports"
        output_dir.mkdir(parents=True, exist_ok=True)

        ui_settings = ima_config.get("ui_settings", {})
        ui_settings["show_rank_tips"] = self.options_show_rank_tips_toggle.get_state()
        ui_settings["show_rr_in_tip"] = self.options_show_rr_in_tip_toggle.get_state()
        ui_settings["tip_delay"] = self.options_tip_delay_slider.value()
        ui_settings["include_app_shortcut"] = self.options_include_app_shortcut_toggle.get_state()
        ui_settings["show_map_planner_in_menu"] = self.options_show_map_planner_toggle.get_state()

        ima_config["ima_menu_path"] = str(resolved_ima_path)
        ima_config["output_dir"] = str(output_dir)
        ima_config["title"] = self.options_ima_title_edit.text().strip() or "Valorant"
        ima_config["menu_icon_path"] = self.options_ima_icon_edit.text().strip()
        ima_config["ui_settings"] = ui_settings
        self.switcher.set_ima_config(ima_config)

        try:
            self.switcher.generate_ima_menu_script(
                output_dir=str(output_dir),
                title=ima_config["title"],
                ordered_accounts=ima_config.get("ordered_accounts", []),
                menu_icon_path=ima_config["menu_icon_path"],
                save_config=False
            )
            success, message = self.switcher.update_ima_shell_script(resolved_ima_path)
            if success:
                CustomMessageDialog.information(self, "Export Successful", f"Successfully exported iMA Menu configuration to:\n{output_dir / 'valo.nss'}")
            else:
                CustomMessageDialog.warning(self, "Shell Script Warning", message)
        except Exception as e:
            CustomMessageDialog.critical(self, "Export Failed", f"An error occurred: {e}")

    def setup_map_planner_tab(self):
        planner_tab = QWidget()
        main_layout = QVBoxLayout(planner_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        group_style = """
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #FFFFFF; }
        """

        launcher_group = QGroupBox("Valorant Tactical Map Planner", planner_tab)
        launcher_group.setStyleSheet(group_style)
        launcher_layout = QVBoxLayout(launcher_group)
        launcher_layout.setSpacing(12)
        launcher_layout.setContentsMargins(15, 20, 15, 15)

        desc_label = QLabel("Interactive tactical planning board with agent positioning, vision cones, execute paths, smokes, pings, and strategy export.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #e0d6d1; font-size: 12px;")
        launcher_layout.addWidget(desc_label)

        open_planner_btn = QPushButton("Open Map Planner")
        open_planner_btn.setObjectName("ApplyButton")
        open_planner_btn.clicked.connect(self.open_map_planner_dialog)
        launcher_layout.addWidget(open_planner_btn)

        main_layout.addWidget(launcher_group)
        main_layout.addStretch()

        self.add_page("Map Planner", "maps/maps planner/Bind.png", planner_tab)

    def open_map_planner_dialog(self):
        from map_planner import MapPlannerDialog
        dialog = MapPlannerDialog(self)
        dialog.exec_()

    def setup_updates_tab(self):
        updates_tab = QWidget()
        main_layout = QVBoxLayout(updates_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        group_style = """
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #FFFFFF; }
        """

        group_box = QGroupBox("App Version & Updates", updates_tab)
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(15, 20, 15, 15)

        from game_switcher import APP_VERSION
        version_label = QLabel(f"<b>Current Version:</b> v{APP_VERSION}")
        group_layout.addWidget(version_label)

        check_btn = QPushButton("Check for Updates")
        check_btn.setObjectName("ApplyButton")
        self.update_check_btn = check_btn
        check_btn.clicked.connect(lambda: self.open_update_dialog(source_button=self.update_check_btn))
        group_layout.addWidget(check_btn)

        main_layout.addWidget(group_box)

        changelog_box = QGroupBox("Changelog", updates_tab)
        changelog_layout = QVBoxLayout(changelog_box)
        changelog_layout.setSpacing(10)
        changelog_layout.setContentsMargins(15, 20, 15, 15)

        changelog_edit = QTextEdit()
        changelog_edit.setReadOnly(True)
        
        cl_path = get_asset_path("CHANGELOG.md")
        if os.path.exists(cl_path):
            try:
                with open(cl_path, "r", encoding="utf-8") as f:
                    changelog_edit.setMarkdown(f.read())
            except Exception:
                changelog_edit.setPlainText("Changelog information unavailable.")
        else:
            changelog_edit.setPlainText("Changelog information unavailable.")

        changelog_layout.addWidget(changelog_edit)
        main_layout.addWidget(changelog_box)

        self.add_page("Updates", "Update.png", updates_tab)

    def open_update_dialog(self, source_button=None):
        update_dialog = UpdateDialog(self.switcher, self, source_button=source_button)
        update_dialog.exec_()

    def load_account_crosshair_info(self):
        acc = self.crosshair_account_combo.currentText()
        if not acc:
            return

        self._last_selected_crosshair_acc = acc

        data = self.switcher.get_account_crosshairs(acc)
        if not data or 'profiles' not in data or not data['profiles']:
            default_p = ValorantCrosshairCodeParser.parse_code("0;P;c;1;h;1;0t;2;0l;6;0o;3;0a;1")
            default_p["profileName"] = "Primary Crosshair"
            data = {"currentProfile": 0, "profiles": [default_p]}
            

        self._current_crosshair_data = copy.deepcopy(data)
        self.crosshair_profile_combo.blockSignals(True)
        self.crosshair_profile_combo.clear()

        profiles = data.get('profiles', [])
        for i, p in enumerate(profiles):
            name = p.get('profileName', f"Profile {i+1}")
            self.crosshair_profile_combo.addItem(name, i)

        curr_idx = data.get('currentProfile', 0)
        if 0 <= curr_idx < len(profiles):
            self.crosshair_profile_combo.setCurrentIndex(curr_idx)
        elif len(profiles) > 0:
            self.crosshair_profile_combo.setCurrentIndex(0)

        self.crosshair_profile_combo.blockSignals(False)
        self.on_crosshair_profile_selected()

    def on_crosshair_profile_selected(self):
        if getattr(self, 'ch_updating_controls', False):
            return
        idx = self.crosshair_profile_combo.currentIndex()
        if not hasattr(self, '_current_crosshair_data') or not self._current_crosshair_data:
            self.ch_canvas.set_profile({})
            return
        profiles = self._current_crosshair_data.get('profiles', [])
        if not (0 <= idx < len(profiles)):
            self.ch_canvas.set_profile({})
            return

        p = profiles[idx]
        self.ch_canvas.set_profile(p)

        primary = p.get('primary', {})
        inner = primary.get('innerLines', {})
        outer = primary.get('outerLines', {})

        self.ch_updating_controls = True

        col_val = primary.get("color")
        if col_val is None:
            col_val = primary.get("primaryColor")

        if isinstance(col_val, dict):
            r_val = col_val.get('r', col_val.get('R', None))
            g_val = col_val.get('g', col_val.get('G', None))
            b_val = col_val.get('b', col_val.get('B', None))
            if r_val is not None and g_val is not None and b_val is not None:
                r = int(round(r_val * 255)) if isinstance(r_val, float) and r_val <= 1.0 else int(r_val)
                g = int(round(g_val * 255)) if isinstance(g_val, float) and g_val <= 1.0 else int(g_val)
                b = int(round(b_val * 255)) if isinstance(b_val, float) and b_val <= 1.0 else int(b_val)
                if r >= 230 and g >= 230 and b >= 230: self.ch_color_combo.setCurrentIndex(0)
                elif r <= 40 and g >= 230 and b <= 40: self.ch_color_combo.setCurrentIndex(1)
                elif r >= 110 and r <= 150 and g >= 230 and b <= 40: self.ch_color_combo.setCurrentIndex(2)
                elif r >= 170 and r <= 215 and g >= 230 and b <= 40: self.ch_color_combo.setCurrentIndex(3)
                elif r >= 230 and g >= 230 and b <= 40: self.ch_color_combo.setCurrentIndex(4)
                elif r <= 40 and g >= 230 and b >= 230: self.ch_color_combo.setCurrentIndex(5)
                elif r >= 230 and g <= 40 and b >= 230: self.ch_color_combo.setCurrentIndex(6)
                elif r >= 230 and g <= 40 and b <= 40: self.ch_color_combo.setCurrentIndex(7)
                else:
                    self.ch_color_combo.setCurrentIndex(8)
                    self.ch_custom_hex_edit.setText(f"#{r:02X}{g:02X}{b:02X}FF")
            else:
                self.ch_color_combo.setCurrentIndex(0)
        elif isinstance(col_val, int) and 0 <= col_val <= 7:
            self.ch_color_combo.setCurrentIndex(col_val)
        elif primary.get('bUseCustomColor', False) or 'colorCustom' in primary or 'customColor' in primary:
            self.ch_color_combo.setCurrentIndex(8)
            custom_dict = primary.get('colorCustom') or primary.get('customColor')
            if isinstance(custom_dict, dict):
                r = int(custom_dict.get('r', 255))
                g = int(custom_dict.get('g', 255))
                b = int(custom_dict.get('b', 255))
                self.ch_custom_hex_edit.setText(f"#{r:02X}{g:02X}{b:02X}FF")
            elif isinstance(custom_dict, str):
                self.ch_custom_hex_edit.setText(custom_dict)
        else:
            self.ch_color_combo.setCurrentIndex(0)

        self.ch_dot_enable_cb.setChecked(primary.get('bDisplayCenterDot', False))
        self.ch_dot_opacity_slider.setValue(int(float(primary.get('centerDotOpacity', 1.0)) * 100))
        self.ch_dot_size_slider.setValue(int(primary.get('centerDotSize', 2)))

        self.ch_outline_enable_cb.setChecked(primary.get('bHasOutline', primary.get('bOutlineEnabled', True)))
        self.ch_outline_opacity_slider.setValue(int(float(primary.get('outlineOpacity', 1.0)) * 100))
        self.ch_outline_thick_slider.setValue(int(primary.get('outlineThickness', 1)))

        self.ch_inner_enable_cb.setChecked(inner.get('bShowLines', inner.get('bbDisplayInnerLines', inner.get('bDisplayInnerLines', False))))
        self.ch_inner_opacity_slider.setValue(int(float(inner.get('opacity', inner.get('lineOpacity', 1.0))) * 100))
        self.ch_inner_len_slider.setValue(int(inner.get('lineLength', 6)))
        self.ch_inner_thick_slider.setValue(int(inner.get('lineThickness', 2)))
        self.ch_inner_off_slider.setValue(int(inner.get('lineOffset', 3)))
        self.ch_inner_top_cb.setChecked(inner.get('bShowTopLine', True))

        self.ch_outer_enable_cb.setChecked(outer.get('bShowLines', outer.get('bbDisplayOuterLines', outer.get('bDisplayOuterLines', False))))
        self.ch_outer_opacity_slider.setValue(int(float(outer.get('opacity', outer.get('lineOpacity', 0.35))) * 100))
        self.ch_outer_len_slider.setValue(int(outer.get('lineLength', 2)))
        self.ch_outer_thick_slider.setValue(int(outer.get('lineThickness', 2)))
        self.ch_outer_off_slider.setValue(int(outer.get('lineOffset', 10)))
        self.ch_outer_top_cb.setChecked(outer.get('bShowTopLine', True))

        self.ch_updating_controls = False

    def update_active_profile_from_controls(self):
        if getattr(self, 'ch_updating_controls', False):
            return
        idx = self.crosshair_profile_combo.currentIndex()
        if not hasattr(self, '_current_crosshair_data') or not self._current_crosshair_data:
            return
        profiles = self._current_crosshair_data.get('profiles', [])
        if not (0 <= idx < len(profiles)):
            return

        p = profiles[idx]
        if 'primary' not in p or not isinstance(p['primary'], dict):
            p['primary'] = {}
        primary = p['primary']

        if 'innerLines' not in primary or not isinstance(primary['innerLines'], dict):
            primary['innerLines'] = {}
        inner = primary['innerLines']

        if 'outerLines' not in primary or not isinstance(primary['outerLines'], dict):
            primary['outerLines'] = {}
        outer = primary['outerLines']

        color_idx = self.ch_color_combo.currentIndex()
        preset_colors = [
            {"r": 255, "g": 255, "b": 255, "a": 255},
            {"r": 0, "g": 255, "b": 0, "a": 255},
            {"r": 127, "g": 255, "b": 0, "a": 255},
            {"r": 190, "g": 255, "b": 0, "a": 255},
            {"r": 255, "g": 255, "b": 0, "a": 255},
            {"r": 0, "g": 255, "b": 255, "a": 255},
            {"r": 255, "g": 0, "b": 255, "a": 255},
            {"r": 255, "g": 0, "b": 0, "a": 255},
        ]
        if color_idx == 8:
            primary['bUseCustomColor'] = True
            primary['color'] = 8
            hex_val = self.ch_custom_hex_edit.text().strip() or "#00FF88FF"
            primary['customColor'] = hex_val
            try:
                qc = QColor(hex_val)
                primary['primaryColor'] = {"r": qc.red(), "g": qc.green(), "b": qc.blue(), "a": 255}
            except: pass
        else:
            primary['bUseCustomColor'] = False
            primary['color'] = color_idx
            if 0 <= color_idx < len(preset_colors):
                primary['primaryColor'] = preset_colors[color_idx]

        primary['bDisplayCenterDot'] = self.ch_dot_enable_cb.isChecked()
        primary['centerDotOpacity'] = float(self.ch_dot_opacity_slider.value()) / 100.0
        primary['centerDotSize'] = self.ch_dot_size_slider.value()

        primary['bOutlineEnabled'] = self.ch_outline_enable_cb.isChecked()
        primary['outlineOpacity'] = float(self.ch_outline_opacity_slider.value()) / 100.0
        primary['outlineThickness'] = self.ch_outline_thick_slider.value()

        inner['bDisplayInnerLines'] = self.ch_inner_enable_cb.isChecked()
        inner['lineOpacity'] = float(self.ch_inner_opacity_slider.value()) / 100.0
        inner['lineLength'] = self.ch_inner_len_slider.value()
        inner['lineThickness'] = self.ch_inner_thick_slider.value()
        inner['lineOffset'] = self.ch_inner_off_slider.value()
        inner['bShowTopLine'] = self.ch_inner_top_cb.isChecked()

        outer['bDisplayOuterLines'] = self.ch_outer_enable_cb.isChecked()
        outer['lineOpacity'] = float(self.ch_outer_opacity_slider.value()) / 100.0
        outer['lineLength'] = self.ch_outer_len_slider.value()
        outer['lineThickness'] = self.ch_outer_thick_slider.value()
        outer['lineOffset'] = self.ch_outer_off_slider.value()
        outer['bShowTopLine'] = self.ch_outer_top_cb.isChecked()

        self.ch_canvas.set_profile(p)

    def on_crosshair_preset_selected(self, index):
        if index <= 0:
            return
        preset_name = self.crosshair_preset_combo.currentText()
        code = VALORANT_CROSSHAIR_PRESETS.get(preset_name)
        if not code:
            return
        imported_profile = ValorantCrosshairCodeParser.parse_code(code)
        if not imported_profile:
            return

        idx = self.crosshair_profile_combo.currentIndex()
        if not hasattr(self, '_current_crosshair_data') or not self._current_crosshair_data:
            self._current_crosshair_data = {"currentProfile": 0, "profiles": []}
        profiles = self._current_crosshair_data.get('profiles', [])
        if 0 <= idx < len(profiles):
            imported_profile["profileName"] = profiles[idx].get("profileName", preset_name)
            profiles[idx] = imported_profile
        else:
            imported_profile["profileName"] = preset_name
            profiles.append(imported_profile)
            self._current_crosshair_data['currentProfile'] = len(profiles) - 1

        self.on_crosshair_profile_selected()
        self.status_label.setText(f"Loaded preset: '{preset_name}'. Click 'Save to Account' to apply.")
        self.crosshair_preset_combo.blockSignals(True)
        self.crosshair_preset_combo.setCurrentIndex(0)
        self.crosshair_preset_combo.blockSignals(False)

    def on_save_crosshairs_to_account(self):
        acc = self.crosshair_account_combo.currentText()
        if not acc or not hasattr(self, '_current_crosshair_data') or not self._current_crosshair_data:
            self.status_label.setText("No active crosshair profile to save.")
            return
        success = self.switcher.set_account_crosshairs(acc, self._current_crosshair_data)
        if success:
            self.status_label.setText(f"Successfully saved crosshairs to account '{acc}'.")
        else:
            self.status_label.setText(f"Failed to save crosshairs to account '{acc}'.")

    def on_import_crosshair_code(self):
        code, ok = QInputDialog.getText(self, "Import Valorant Crosshair Code", "Paste Crosshair Profile Code (e.g., 0;P;c;5;o;1;...):")
        if not ok or not code.strip():
            return

        imported_profile = ValorantCrosshairCodeParser.parse_code(code)
        if not imported_profile:
            self.status_label.setText("Failed to parse crosshair code.")
            return

        idx = self.crosshair_profile_combo.currentIndex()
        if not hasattr(self, '_current_crosshair_data') or not self._current_crosshair_data:
            self._current_crosshair_data = {"currentProfile": 0, "profiles": []}

        profiles = self._current_crosshair_data.get('profiles', [])
        if 0 <= idx < len(profiles):
            imported_profile["profileName"] = profiles[idx].get("profileName", "Imported Profile")
            profiles[idx] = imported_profile
        else:
            imported_profile["profileName"] = f"Profile {len(profiles)+1}"
            profiles.append(imported_profile)
            self._current_crosshair_data['currentProfile'] = len(profiles) - 1

        self.on_crosshair_profile_selected()
        self.status_label.setText("Crosshair code imported! Click 'Save to Account' to persist.")

    def on_export_crosshair_code(self):
        idx = self.crosshair_profile_combo.currentIndex()
        if not hasattr(self, '_current_crosshair_data') or not self._current_crosshair_data:
            return
        profiles = self._current_crosshair_data.get('profiles', [])
        if not (0 <= idx < len(profiles)):
            return

        code = ValorantCrosshairCodeParser.export_code(profiles[idx])
        QApplication.clipboard().setText(code)
        self.status_label.setText(f"Copied code to clipboard: {code}")

    def set_all_qualities(self, value):
        for spin_box in self.spin_boxes.values():
            spin_box.setValue(value)

    def apply_settings(self):
        quality_settings = {key: spin_box.value() for key, spin_box in self.spin_boxes.items()}
        
        riot_settings_to_save = {}
        for key, combo_box in self.riot_combo_boxes.items():
            selected_text = combo_box.currentText()
            if key == "EAresIntSettingName::MaterialQuality":
                if selected_text == "Low": riot_settings_to_save[key] = "0"
                elif selected_text == "Med": riot_settings_to_save[key] = "2"
                else: riot_settings_to_save[key] = "High"
            elif key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                if selected_text == "Off": riot_settings_to_save[key] = "0"
                elif selected_text == "On + Boost": riot_settings_to_save[key] = "2"
                else: riot_settings_to_save[key] = "On"
            else:
                if selected_text == "Low": riot_settings_to_save[key] = "0"
                elif selected_text == "Med": riot_settings_to_save[key] = "1"
                else: riot_settings_to_save[key] = "High"

        audio_settings_to_save = {}
        for key, control in self.audio_controls.items():
            special_float_keys = ["EAresFloatSettingName::CharacterSelectMusicVolume", "EAresFloatSettingName::MenuAndLobbyMusicVolume"]
            if isinstance(control, ValueSlider):
                val = control.value()
                if key.startswith("EAresFloatSettingName::"):
                    if val == 100:
                        audio_settings_to_save[key] = "1.000000" if key in special_float_keys else "MAX"
                    else:
                        audio_settings_to_save[key] = f"{val/100:.6f}"
                elif key.startswith("EAresIntSettingName::"):
                    audio_settings_to_save[key] = str(val)
            elif isinstance(control, RadioButtonGroup):
                audio_settings_to_save[key] = "True" if control.get_state() else "False"

        ui_settings_to_save = {
            "show_game_icons": self.show_game_icons_toggle.get_state() if hasattr(self, 'show_game_icons_toggle') else True,
            "use_rank_icons": self.use_rank_icons_toggle.get_state() if hasattr(self, 'use_rank_icons_toggle') else False,
            "show_rank_icon_left": self.show_rank_icon_left_toggle.get_state() if hasattr(self, 'show_rank_icon_left_toggle') else False,
            "show_name_tag": self.show_name_tag_toggle.get_state() if hasattr(self, 'show_name_tag_toggle') else True,
            "show_current_rr": self.show_current_rr_toggle.get_state() if hasattr(self, 'show_current_rr_toggle') else True,
            "show_last_game_rr": self.show_last_game_rr_toggle.get_state() if hasattr(self, 'show_last_game_rr_toggle') else True,
            "show_last_match_info": self.show_last_match_info_toggle.get_state() if hasattr(self, 'show_last_match_info_toggle') else True,
            "show_map_background": self.show_map_background_toggle.get_state() if hasattr(self, 'show_map_background_toggle') else False,
            "rank_check_region": self.rank_check_region_combo.currentData() if hasattr(self, 'rank_check_region_combo') else "eu",
            "auto_rank_update": self.auto_rank_update_toggle.get_state() if hasattr(self, 'auto_rank_update_toggle') else True,
            "grid_size": int(self.grid_size_combo.currentText()) if hasattr(self, 'grid_size_combo') else 4,
            "show_splash_notification": self.show_splash_notification_toggle.get_state() if hasattr(self, 'show_splash_notification_toggle') else True,
            "show_riot_client": self.show_riot_client_toggle.get_state() if hasattr(self, 'show_riot_client_toggle') else False,
            "theme": self.theme_combo.currentData() if hasattr(self, 'theme_combo') else "dark_gold",
            "unified_settings_enabled": self.unified_enabled_toggle.get_state() if hasattr(self, 'unified_enabled_toggle') else False,
            "master_account": self.master_account_combo.currentText() if hasattr(self, 'master_account_combo') else "",
            "sync_keybinds": self.sync_keybinds_toggle.get_state() if hasattr(self, 'sync_keybinds_toggle') else False,
        }

        if hasattr(self, 'options_show_rank_tips_toggle'):
            ui_settings_to_save["show_rank_tips"] = self.options_show_rank_tips_toggle.get_state()
            ui_settings_to_save["show_rr_in_tip"] = self.options_show_rr_in_tip_toggle.get_state()
            ui_settings_to_save["tip_delay"] = self.options_tip_delay_slider.value()
            ui_settings_to_save["include_app_shortcut"] = self.options_include_app_shortcut_toggle.get_state()
            ui_settings_to_save["show_map_planner_in_menu"] = self.options_show_map_planner_toggle.get_state()

        settings_to_save = {
            "display_mode": self.display_mode_combo.currentText(),
            "quality": quality_settings,
            "riot_settings": riot_settings_to_save,
            "audio_settings": audio_settings_to_save,
            "ui_settings": ui_settings_to_save
        }
        self.switcher.save_graphics_settings(settings_to_save)
        success, message = self.switcher.update_all_game_user_settings(settings_to_save)

        if hasattr(self, 'options_ima_path_edit'):
            raw_path = self.options_ima_path_edit.text().strip()
            resolved_ima_path = self.switcher.resolve_ima_menu_folder(raw_path) if raw_path else self.switcher.find_ima_menu_path()
            if resolved_ima_path:
                ima_config = self.switcher.get_ima_config()
                ima_config["ima_menu_path"] = str(resolved_ima_path)
                ima_config["output_dir"] = str(resolved_ima_path / "imports")
                ima_config["title"] = self.options_ima_title_edit.text().strip() or "Valorant"
                ima_config["menu_icon_path"] = self.options_ima_icon_edit.text().strip()
                ima_config["ui_settings"] = ui_settings_to_save
                self.switcher.set_ima_config(ima_config)
                try:
                    output_dir = resolved_ima_path / "imports"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    self.switcher.generate_ima_menu_script(
                        output_dir=str(output_dir),
                        title=ima_config["title"],
                        ordered_accounts=ima_config.get("ordered_accounts", []),
                        menu_icon_path=ima_config["menu_icon_path"],
                        save_config=False
                    )
                    self.switcher.update_ima_shell_script(resolved_ima_path)
                except Exception as e:
                    logging.error(f"Error applying iMA Menu settings: {e}")
        else:
            self.switcher.update_ima_menu_if_enabled('update', None)

        if hasattr(self, 'theme_combo'):
            selected_theme = self.theme_combo.currentData()
            apply_theme_to_app(QApplication.instance(), selected_theme)
            if self.parent():
                apply_theme_to_app(self.parent(), selected_theme)

        if hasattr(self, 'on_save_crosshairs_clicked'):
            self.on_save_crosshairs_clicked()
        if hasattr(self, 'save_account_controls'):
            self.save_account_controls()
        
        if success:
            self.status_label.setText("Settings applied successfully.")
            self.settings_applied.emit()
        else:
            self.status_label.setText(f"Failed to apply settings: {message}")

    def load_current_settings(self):
        settings = self.switcher.get_graphics_settings()
        self.display_mode_combo.setCurrentText(settings.get("display_mode", "Default"))
        
        riot_settings = settings.get("riot_settings", {})
        for key, combo_box in self.riot_combo_boxes.items():
            if key == "EAresIntSettingName::MaterialQuality":
                value = riot_settings.get(key, "High")
                if value == "0": combo_box.setCurrentText("Low")
                elif value == "2": combo_box.setCurrentText("Med")
                else: combo_box.setCurrentText("High")
            elif key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                value = riot_settings.get(key, "On")
                if value == "0": combo_box.setCurrentText("Off")
                elif value == "2": combo_box.setCurrentText("On + Boost")
                else: combo_box.setCurrentText("On")
            else:
                value = riot_settings.get(key, "High")
                if value == "0": combo_box.setCurrentText("Low")
                elif value == "1": combo_box.setCurrentText("Med")
                else: combo_box.setCurrentText("High")

        audio_settings = settings.get("audio_settings", {})
        for key, control in self.audio_controls.items():
            value_str = audio_settings.get(key)
            if value_str is None: 
                if isinstance(control, ValueSlider):
                    control.setValue(100)
                elif isinstance(control, RadioButtonGroup):
                    is_true_default = (key == "EAresBoolSettingName::PushToTalkEnabled")
                    control.set_state(is_true_default)
            else:
                if key.startswith("EAresFloatSettingName::"):
                    if value_str.upper() == 'MAX':
                        control.setValue(100)
                    else:
                        control.setValue(float(value_str) * 100)
                elif key.startswith("EAresIntSettingName::"):
                    control.setValue(int(float(value_str)))
                elif key.startswith("EAresBoolSettingName::"):
                    control.set_state(value_str.lower() == 'true')
        
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        if hasattr(self, 'show_game_icons_toggle'): self.show_game_icons_toggle.set_state(ui_settings.get("show_game_icons", True))
        if hasattr(self, 'use_rank_icons_toggle'): self.use_rank_icons_toggle.set_state(ui_settings.get("use_rank_icons", False))
        if hasattr(self, 'show_rank_icon_left_toggle'): self.show_rank_icon_left_toggle.set_state(ui_settings.get("show_rank_icon_left", False))
        if hasattr(self, 'show_name_tag_toggle'): self.show_name_tag_toggle.set_state(ui_settings.get("show_name_tag", True))
        if hasattr(self, 'show_current_rr_toggle'): self.show_current_rr_toggle.set_state(ui_settings.get("show_current_rr", True))
        if hasattr(self, 'show_last_game_rr_toggle'): self.show_last_game_rr_toggle.set_state(ui_settings.get("show_last_game_rr", True))
        if hasattr(self, 'show_last_match_info_toggle'): self.show_last_match_info_toggle.set_state(ui_settings.get("show_last_match_info", True))
        if hasattr(self, 'show_map_background_toggle'): self.show_map_background_toggle.set_state(ui_settings.get("show_map_background", False))
        if hasattr(self, 'grid_size_combo'): self.grid_size_combo.setCurrentText(str(ui_settings.get("grid_size", 4)))
        if hasattr(self, 'theme_combo'):
            saved_theme = ui_settings.get("theme", "dark_gold")
            idx = self.theme_combo.findData(saved_theme)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
        if hasattr(self, 'show_splash_notification_toggle'): self.show_splash_notification_toggle.set_state(ui_settings.get("show_splash_notification", True))
        if hasattr(self, 'show_riot_client_toggle'): self.show_riot_client_toggle.set_state(ui_settings.get("show_riot_client", False))
        
        ima_config = self.switcher.get_ima_config()
        if hasattr(self, 'options_ima_path_edit'):
            saved_ima_path = ima_config.get("ima_menu_path")
            if not saved_ima_path:
                detected_path = self.switcher.find_ima_menu_path()
                saved_ima_path = str(detected_path) if detected_path else ""
            self.options_ima_path_edit.setText(saved_ima_path or "")
            self.update_options_ima_path_status(saved_ima_path)
            self.options_ima_title_edit.setText(ima_config.get("title", "Valorant"))
            self.options_ima_icon_edit.setText(ima_config.get("menu_icon_path", ""))
            self.update_options_ima_icon_preview(ima_config.get("menu_icon_path", ""))
            self.options_show_rank_tips_toggle.set_state(ui_settings.get("show_rank_tips", False))
            self.options_show_rr_in_tip_toggle.set_state(ui_settings.get("show_rr_in_tip", False))
            self.options_tip_delay_slider.setValue(ui_settings.get("tip_delay", 1.0))
            if hasattr(self, 'options_include_app_shortcut_toggle'):
                self.options_include_app_shortcut_toggle.set_state(ui_settings.get("include_app_shortcut", False))
            if hasattr(self, 'options_show_map_planner_toggle'):
                self.options_show_map_planner_toggle.set_state(ui_settings.get("show_map_planner_in_menu", False))
        
        # Account tab settings
        self.auto_rank_update_toggle.set_state(ui_settings.get("auto_rank_update", True))
        saved_region = ui_settings.get("rank_check_region", "eu")
        index = self.rank_check_region_combo.findData(saved_region)
        if index == -1:
            index = self.rank_check_region_combo.findText(saved_region)
        if index != -1:
            self.rank_check_region_combo.setCurrentIndex(index)

        self.load_account_crosshair_info()
        self.status_label.setText("Loaded saved settings.")

    def open_profiles_folder(self):
        if hasattr(self.switcher, 'profiles_dir') and self.switcher.profiles_dir:
            os.startfile(str(self.switcher.profiles_dir))

    def preview_splash_screen(self):
        accounts = self.switcher.get_saved_accounts()
        if not accounts:
            self.status_label.setText("No accounts available to preview.")
            return

        account_names = list(accounts.keys())
        if not hasattr(self, "_preview_account_index"):
            self._preview_account_index = 0
        else:
            self._preview_account_index = (self._preview_account_index + 1) % len(account_names)

        account_name = account_names[self._preview_account_index]
        account_data = accounts[account_name]
        icon_source_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = account_data

        use_rank_icons = self.use_rank_icons_toggle.get_state()
        icon_path_str = self.switcher.get_icon_path_for_account(account_name, rank, use_rank_icons, icon_source_path)
        account_icon = self.switcher.get_qicon_from_path(icon_path_str)
        pixmap = account_icon.pixmap(180, 180)

        if hasattr(self, "_preview_notification") and self._preview_notification:
            try:
                self._preview_notification.close()
            except RuntimeError:
                pass

        self._preview_notification = LaunchNotificationWidget(
            account_name,
            pixmap,
            in_game_name=in_game_name if self.show_name_tag_toggle.get_state() else None,
            in_game_tag=in_game_tag if self.show_name_tag_toggle.get_state() else None,
            rank=rank,
            use_rank_icons=use_rank_icons,
            standalone=False,
            switcher_instance=self.switcher
        )
        self._preview_notification.show()
        self.status_label.setText(f"Previewing splash for '{account_name}' ({self._preview_account_index + 1}/{len(account_names)})")

class CustomTitleBar(QWidget):
    def __init__(self, title_or_parent, parent_or_is_dialog=None, is_dialog=False):
        if isinstance(title_or_parent, QWidget):
            parent = title_or_parent
            is_dialog = parent_or_is_dialog if isinstance(parent_or_is_dialog, bool) else False
            title = ""
        else:
            title = str(title_or_parent)
            parent = parent_or_is_dialog
            is_dialog = is_dialog

        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(44)

        self.setObjectName("CustomTitleBar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        if not is_dialog:
            logo_path = get_asset_path("app_icon.png")
            if not os.path.exists(logo_path) and hasattr(parent, 'switcher'):
                logo_path = str(parent.switcher.base_dir / "Assets" / "app_icon.png")
            
            self.logo_label = QLabel()
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(pixmap)
            layout.addWidget(self.logo_label)

            self.settings_button = HoverButton()
            self.settings_button.setObjectName("HeaderButton")
            self.settings_button.setFixedSize(30, 30)
            self.settings_button.setIconSize(QSize(18, 18))
            if hasattr(parent, 'create_gear_icon'):
                self.settings_button.setIcon(parent.create_gear_icon())
            layout.addWidget(self.settings_button)

            layout.addStretch()

            self.status_label = QLabel("Ready")
            self.status_label.setObjectName("StatusLabel")
            self.status_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.status_label)

            layout.addStretch()

            self.add_account_button = HoverButton()
            self.add_account_button.setObjectName("HeaderButton")
            self.add_account_button.setFixedSize(30, 30)
            self.add_account_button.setIconSize(QSize(18, 18))
            if hasattr(parent, 'create_add_icon'):
                self.add_account_button.setIcon(parent.create_add_icon())
            add_shadow = QGraphicsDropShadowEffect(self)
            add_shadow.setBlurRadius(15)
            add_shadow.setColor(QColor(0, 0, 0, 160))
            add_shadow.setOffset(0, 2)
            self.add_account_button.setGraphicsEffect(add_shadow)
            layout.addWidget(self.add_account_button)

            refresh_icon_path = get_asset_path("Refresh.png")
            self.refresh_button = QPushButton(QIcon(refresh_icon_path), "")
            self.refresh_button.setObjectName("HeaderButton")
            self.refresh_button.setFixedSize(30, 30)
            self.refresh_button.setIconSize(QSize(18, 18))
            refresh_shadow = QGraphicsDropShadowEffect(self)
            refresh_shadow.setBlurRadius(15)
            refresh_shadow.setColor(QColor(0, 0, 0, 160))
            refresh_shadow.setOffset(0, 2)
            self.refresh_button.setGraphicsEffect(refresh_shadow)
            layout.addWidget(self.refresh_button)

            minimize_icon_path = get_asset_path("minimize.png")
            self.minimize_button = QPushButton()
            self.minimize_button.setObjectName("HeaderButton")
            if os.path.exists(minimize_icon_path):
                self.minimize_button.setIcon(QIcon(minimize_icon_path))
                self.minimize_button.setIconSize(QSize(16, 16))
            else:
                self.minimize_button.setText("—")
                self.minimize_button.setStyleSheet("font-size: 18px; font-weight: 900; padding: 0px; margin: 0px;")
            self.minimize_button.setFixedSize(30, 30)
            self.minimize_button.clicked.connect(self.parent_window.showMinimized)
            minimize_shadow = QGraphicsDropShadowEffect(self)
            minimize_shadow.setBlurRadius(15)
            minimize_shadow.setColor(QColor(0, 0, 0, 160))
            minimize_shadow.setOffset(0, 2)
            self.minimize_button.setGraphicsEffect(minimize_shadow)
            layout.addWidget(self.minimize_button)

            x_icon_path = get_asset_path("x.png")
            close_button = QPushButton()
            close_button.setObjectName("CloseButton")
            if os.path.exists(x_icon_path):
                close_button.setIcon(QIcon(x_icon_path))
                close_button.setIconSize(QSize(14, 14))
            else:
                close_button.setText("✕")
            close_button.setFixedSize(30, 30)
            close_button.clicked.connect(self.parent_window.close)
            close_shadow = QGraphicsDropShadowEffect(self)
            close_shadow.setBlurRadius(15)
            close_shadow.setColor(QColor(0, 0, 0, 160))
            close_shadow.setOffset(0, 2)
            close_button.setGraphicsEffect(close_shadow)
            layout.addWidget(close_button)

        else:
            title_label = QLabel(title)
            title_label.setObjectName("TitleLabel")
            layout.addWidget(title_label)

            layout.addStretch()

            x_icon_path = get_asset_path("x.png")
            close_button = QPushButton()
            close_button.setObjectName("CloseButton")
            if os.path.exists(x_icon_path):
                close_button.setIcon(QIcon(x_icon_path))
                close_button.setIconSize(QSize(14, 14))
            else:
                close_button.setText("✕")
            close_button.setFixedSize(30, 30)
            close_button.clicked.connect(self.parent_window.close)
            close_button.setStyleSheet("QPushButton { background-color: #f38ba8; border: none; border-radius: 15px; } QPushButton:hover { background-color: #e67e80; }")
            close_shadow = QGraphicsDropShadowEffect(self)
            close_shadow.setBlurRadius(15)
            close_shadow.setColor(QColor(0, 0, 0, 160))
            close_shadow.setOffset(0, 2)
            close_button.setGraphicsEffect(close_shadow)
            layout.addWidget(close_button)

    def add_header_button(self, button):
        lay = self.layout()
        count = lay.count()
        if count > 0:
            lay.insertWidget(count - 1, button)
        else:
            lay.addWidget(button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_window.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self.parent_window, "old_pos") and self.parent_window.old_pos is not None:
            delta = QPoint(event.globalPos() - self.parent_window.old_pos)
            self.parent_window.move(self.parent_window.x() + delta.x(), self.parent_window.y() + delta.y())
            self.parent_window.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.parent_window.old_pos = None

class GameSelectionDialog(PopupDialog):
    game_selected = pyqtSignal(str)

    def __init__(self, account_name, account_icon_pixmap, parent=None, switcher_instance=None):
        super().__init__("Select Game", parent)
        self.setFixedSize(400, 450)
        self.account_name = account_name
        self.account_icon_pixmap = account_icon_pixmap
        self.switcher_instance = switcher_instance
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(Qt.AlignCenter)

        # Game selection buttons
        game_buttons_layout = QHBoxLayout()
        game_buttons_layout.setSpacing(20)
        game_buttons_layout.setAlignment(Qt.AlignCenter)

        self.valorant_button = self._create_game_button("Valorant", "valorant.png", "valorant")
        self.lol_button = self._create_game_button("League of Legends", "lol.png", "lol")

        game_buttons_layout.addWidget(self.valorant_button)
        game_buttons_layout.addWidget(self.lol_button)
        self.content_layout.addLayout(game_buttons_layout)

        # Account info below game selection
        account_info_layout = QVBoxLayout()
        account_info_layout.setAlignment(Qt.AlignCenter)

        account_icon_label = QLabel(self)
        account_icon_label.setPixmap(self.account_icon_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        account_icon_label.setAlignment(Qt.AlignCenter)
        account_info_layout.addWidget(account_icon_label)

        account_name_label = QLabel(self.account_name, self)
        account_name_label.setAlignment(Qt.AlignCenter)
        account_name_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        account_info_layout.addWidget(account_name_label)

        self.content_layout.addLayout(account_info_layout)

    def _create_game_button(self, name, icon_filename, game_id):
        button = QPushButton()
        button.setFixedSize(150, 150)
        button.setStyleSheet("""
            QPushButton { background-color: #3a3637; border-radius: 15px; border: 2px solid #4f4a4b; }
            QPushButton:hover { background-color: #4f4a4b; border-color: #c89f68; }
            QPushButton:pressed { background-color: #2c2a2b; }
        """
)
        button.clicked.connect(lambda: self._set_selected_game_and_accept(game_id))

        layout = QVBoxLayout(button)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        icon_path = get_asset_path(icon_filename)
        logging.debug(f"_create_game_button - icon_path: {icon_path}, exists: {os.path.exists(icon_path)}")
        if self.switcher_instance and Path(icon_path).exists():
            icon_label = QLabel()
            pixmap = self.switcher_instance.get_qicon_from_path(icon_path).pixmap(80, 80).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)

        return button

    def _set_selected_game_and_accept(self, game_id):
        self.game_selected_value = game_id
        self.game_selected.emit(game_id)
        self.accept()

class IconPickerDialog(PopupDialog):
    def __init__(self, switcher_instance, current_icon_path, parent=None):
        super().__init__("Change Icon", parent)
        self.switcher = switcher_instance
        self.selected_icon_path = current_icon_path
        self.setFixedSize(420, 550)

        # --- Main Layout and Styling ---
        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignTop)

        # --- Icon Preview Section ---
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setAlignment(Qt.AlignCenter)
        preview_layout.setContentsMargins(0, 10, 0, 10)

        self.icon_display_widget = QWidget()
        self.icon_display_widget.setFixedSize(130, 130)

        # The preview button is a child of the display widget, positioned manually
        self.icon_preview_button = QPushButton(self.icon_display_widget)
        self.icon_preview_button.setFixedSize(120, 120)
        self.icon_preview_button.move(5, 5)  # Centered (130-120)/2
        self.icon_preview_button.clicked.connect(self.select_icon_from_device)

        # The remove button is also a child, moved to the corner and raised
        self.remove_button = QPushButton("✕", self.icon_display_widget)
        self.remove_button.setFixedSize(24, 24)
        self.remove_button.setObjectName("CloseButton")
        self.remove_button.clicked.connect(self.remove_icon)
        self.remove_button.move(5, 5)  # Top-left corner
        self.remove_button.raise_()

        preview_layout.addWidget(self.icon_display_widget)
        self.content_layout.addWidget(preview_container)

        # --- Icons Grid Section ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        grid_container = QWidget(objectName="grid_container")
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        scroll_area.setWidget(grid_container)
        
        self.content_layout.addWidget(scroll_area)

        # --- Buttons Section ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setObjectName("ApplyButton")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

        self.update_preview()
        
        QTimer.singleShot(50, self.populate_icon_grid)

    def populate_icon_grid(self):
        agents_path = Path(self.switcher.base_dir) / "Agents"
        if not agents_path.exists():
            agents_path = Path(self.switcher.base_dir) / "icons"
        valorant_icons_path = Path(self.switcher.base_dir) / "Assets" / "valorant"
        icon_files = get_icon_paths_from_folder(str(agents_path))
        icon_files.extend(get_icon_paths_from_folder(str(valorant_icons_path)))
        
        for i, icon_path in enumerate(icon_files):
            row, col = i // 4, i % 4
            icon_widget = self.create_grid_icon(icon_path)
            self.grid_layout.addWidget(icon_widget, row, col, Qt.AlignCenter)

    def create_grid_icon(self, icon_path):
        icon_button = QPushButton()
        icon_button.setFixedSize(70, 70)
        
        icon = self.switcher.get_qicon_from_path(icon_path)
        pixmap = icon.pixmap(icon.actualSize(QSize(256, 256)))
        
        scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        circular_pixmap = QPixmap(60, 60)
        circular_pixmap.fill(Qt.transparent)
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, 60, 60)
        painter.setClipPath(path)
        
        x = (60 - scaled_pixmap.width()) / 2
        y = (60 - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        painter.end()

        icon_button.setIcon(QIcon(circular_pixmap))
        icon_button.setIconSize(QSize(60, 60))
        icon_button.clicked.connect(lambda: self.set_selected_icon(icon_path))
        return icon_button

    def update_preview(self):
        size = 120
        if self.selected_icon_path and Path(self.selected_icon_path).exists():
            icon = self.switcher.get_qicon_from_path(self.selected_icon_path)
            pixmap = icon.pixmap(icon.actualSize(QSize(256, 256)))
            scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            circular_pixmap = QPixmap(size, size)
            circular_pixmap.fill(Qt.transparent)
            painter = QPainter(circular_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            x = (size - scaled_pixmap.width()) / 2
            y = (size - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)
            painter.end()

            self.icon_preview_button.setIcon(QIcon(circular_pixmap))
            self.icon_preview_button.setText("")
            self.icon_preview_button.setIconSize(QSize(size, size))
            self.remove_button.setVisible(True)
        else:
            self.icon_preview_button.setIcon(QIcon())
            self.icon_preview_button.setText("+")
            self.icon_preview_button.setStyleSheet("""QPushButton {
                    border: 2px dashed #c89f68;
                    border-radius: 60px;
                    color: #e0d6d1;
                    font-size: 48px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    border-color: #d9b68b;
                    color: #d9b68b;
                }""")
            self.remove_button.setVisible(False)

    def set_selected_icon(self, path):
        self.selected_icon_path = path
        self.update_preview()

    def select_icon_from_device(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Images (*.png *.jpg *.jpeg *.ico)")
        if path:
            self.set_selected_icon(Path(path))

    def remove_icon(self):
        self.selected_icon_path = None
        self.update_preview()

    def get_selected_icon_path(self):
        return self.selected_icon_path


class RiotClientNotFoundDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Riot Client Not Found", parent)
        self.setFixedSize(400, 250)
        
        message_label = QLabel("Could not find RiotClientServices.exe.\nPlease locate it manually.")
        message_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to RiotClientServices.exe")
        self.path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        self.content_layout.addWidget(self.path_edit)

        button_layout = QHBoxLayout()
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        browse_button.clicked.connect(self.browse)
        button_layout.addWidget(browse_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        self.content_layout.addLayout(button_layout)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select RiotClientServices.exe", "", "Executable Files (*.exe)")
        if path:
            self.path_edit.setText(str(Path(path)))

    def get_path(self):
        return self.path_edit.text()

class IMAMenuPathDialog(PopupDialog):
    def __init__(self, parent=None, default_path=""):
        super().__init__("iMA Menu Path", parent)
        self.setFixedSize(520, 290)
        self.switcher = parent.switcher if (parent and hasattr(parent, 'switcher')) else None
        
        message_text = "Select your <b>iMA Menu</b> installation folder or its parent directory.<br><span style='font-size:11px; color:#c89f68;'>Structure: <b>iMA Menu\\imports\\valo.nss</b></span>"
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 13px; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)

        self.path_edit = QLineEdit(default_path)
        self.path_edit.setPlaceholderText("Path to iMA Menu folder or parent directory")
        self.path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        self.path_edit.textChanged.connect(self.update_status)
        self.content_layout.addWidget(self.path_edit)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.content_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        download_button = QPushButton("Download iMA Menu")
        download_button.setStyleSheet('''
            QPushButton {
                background-color: #4a4647; color: #c89f68; font-weight: bold; 
                border-radius: 8px; padding: 8px 12px; border: 1px solid #c89f68;
            }
            QPushButton:hover { background-color: #5a5556; color: #d9b68b; }
        ''')
        download_button.clicked.connect(download_and_open_ima_menu)
        button_layout.addWidget(download_button)
        
        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet('''
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 8px 14px; border: 1px solid transparent;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
        ''')
        browse_button.clicked.connect(self.browse)
        button_layout.addWidget(browse_button)

        detect_button = QPushButton("Detect Active")
        detect_button.setStyleSheet('''
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 8px 14px; border: 1px solid transparent;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
        ''')
        detect_button.clicked.connect(self.detect_active)
        button_layout.addWidget(detect_button)
        
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet('''
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 8px 22px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        ''')
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        self.content_layout.addLayout(button_layout)
        self.update_status(self.path_edit.text())

    def browse(self):
        initial = self.path_edit.text()
        chosen = QFileDialog.getExistingDirectory(self, "Select iMA Menu Folder or Parent Folder", initial)
        if chosen:
            resolved = self.switcher.resolve_ima_menu_folder(chosen) if self.switcher else Path(chosen)
            self.path_edit.setText(str(resolved))

    def detect_active(self):
        if self.switcher:
            detected = self.switcher.get_registered_ima_shell_path() or self.switcher.find_ima_menu_path()
            if detected:
                self.path_edit.setText(str(detected))

    def update_status(self, text=None):
        path_val = (text if text is not None else self.path_edit.text()).strip()
        if not path_val:
            self.status_label.setText("<font color='#e74c3c'>● No path specified</font>")
            return
        if self.switcher:
            resolved = self.switcher.resolve_ima_menu_folder(path_val)
            is_reg, active_reg, _ = self.switcher.get_ima_menu_registration_info(resolved)
            if not resolved or not Path(resolved).exists():
                self.status_label.setText(f"<font color='#e74c3c'>● Folder does not exist: {path_val}</font>")
            elif is_reg:
                self.status_label.setText(f"<font color='#2ecc71'>● Active & Registered: {resolved}</font>")
            elif active_reg:
                self.status_label.setText(f"<font color='#f39c12'>● Custom (Live shell: {active_reg})</font>")
            else:
                self.status_label.setText(f"<font color='#f39c12'>● Custom Folder</font>")
        else:
            if Path(path_val).exists():
                self.status_label.setText("<font color='#2ecc71'>● Folder exists</font>")
            else:
                self.status_label.setText("<font color='#e74c3c'>● Folder does not exist</font>")

    def get_path(self):
        raw = self.path_edit.text().strip()
        if self.switcher and raw:
            return str(self.switcher.resolve_ima_menu_folder(raw))
        return raw

class ConfirmDeleteDialog(PopupDialog):
    def __init__(self, account_name, parent=None, title="Confirm Delete", message=None):
        super().__init__(title, parent)
        self.setFixedSize(350, 180)
        
        if message is None:
            message = f"Delete '{account_name}'?"

        message_label = QLabel(message)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15) # Increased spacing between buttons
        button_layout.addStretch()

        no_button = QPushButton("No")
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b; /* Increased padding */
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """
)
        no_button.clicked.connect(self.reject)
        button_layout.addWidget(no_button)

        yes_button = QPushButton("Yes")
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """
)
        yes_button.clicked.connect(self.accept)
        button_layout.addWidget(yes_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

class AccountWidget(QWidget):
    selected = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    context_menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, parent=None, is_add_button=False, switcher_instance=None):
        super().__init__(parent)
        self.account_name = account_name
        self.game = game
        self.rank = rank
        self.in_game_name = in_game_name
        self.in_game_tag = in_game_tag
        self.current_rr = current_rr
        self.last_game_rr = last_game_rr
        self.switcher = switcher_instance
        self.setObjectName("AccountWidget")
        self.setFixedSize(160, 195)
        self.is_selected, self.is_hovered = False, False
        self.is_add_button = is_add_button
        self.icon = icon  # Store the icon
        self.init_ui(icon)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        self.icon_anim = QPropertyAnimation(self, b"iconSize")
        self.icon_anim.setDuration(150)
        self.icon_anim.setEasingCurve(QEasingCurve.OutQuad)

    def _get_icon_size(self):
        return self.icon_label.size()

    def _set_icon_size(self, size):
        self.set_icon(self.icon, size.width())

    iconSize = pyqtProperty(QSize, _get_icon_size, _set_icon_size)

    def _add_shadow_effect(self, widget):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 2)
        widget.setGraphicsEffect(shadow)

    def init_ui(self, icon):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(2)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.current_rr_label = QLabel(self)
        self.current_rr_label.setAlignment(Qt.AlignCenter)
        self.current_rr_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self._add_shadow_effect(self.current_rr_label)
        self.main_layout.addWidget(self.current_rr_label, 0, Qt.AlignCenter)

        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.set_icon(icon, 70)
        self._add_shadow_effect(self.icon_label)
        self.main_layout.addWidget(self.icon_label, 0, Qt.AlignCenter)

        self.name_label = QLabel(self.account_name, self, objectName="NameLabel")
        self.name_label.setAlignment(Qt.AlignCenter)
        self._add_shadow_effect(self.name_label)
        self.main_layout.addWidget(self.name_label, 0, Qt.AlignCenter)

        self.in_game_name_tag_label = QLabel(self)
        self.in_game_name_tag_label.setAlignment(Qt.AlignCenter)
        self.in_game_name_tag_label.setStyleSheet("color: #b0a8a8; font-size: 11px;")
        self._add_shadow_effect(self.in_game_name_tag_label)
        self.main_layout.addWidget(self.in_game_name_tag_label, 0, Qt.AlignCenter)

        self.last_game_rr_label = QLabel(self)
        self.last_game_rr_label.setAlignment(Qt.AlignCenter)
        self._add_shadow_effect(self.last_game_rr_label)
        self.main_layout.addWidget(self.last_game_rr_label, 0, Qt.AlignCenter)

        self.last_match_label = QLabel(self, objectName="LastMatchLabel")
        self.last_match_label.setAlignment(Qt.AlignCenter)
        self.last_match_label.setVisible(False)
        self._add_shadow_effect(self.last_match_label)
        self.main_layout.addWidget(self.last_match_label, 0, Qt.AlignCenter)
        
        if self.is_add_button:
            self.setProperty("is_add_button", "true")
            self.name_label.setStyleSheet("color: #c89f68; font-size: 16px; font-weight: bold;")
            self.icon_label.setStyleSheet("color: #c89f68;")
            self.in_game_name_tag_label.setVisible(False)
            self.current_rr_label.setVisible(False)
            self.last_game_rr_label.setVisible(False)
            self.last_match_label.setVisible(False)
        else:
            self.game_icon_label = QLabel(self)
            game_icon_size = 24
            self.game_icon_label.setFixedSize(game_icon_size, game_icon_size)
            self.game_icon_label.setAlignment(Qt.AlignCenter)
            self.game_icon_label.move(self.width() - game_icon_size - 10, 10)
            self._add_shadow_effect(self.game_icon_label)
            
            valorant_icon_path = get_asset_path("valorant.png")
            lol_icon_path = get_asset_path("lol.png")
            riot_icon_path = get_asset_path("Riot.png")

            self.game_icon_label.setVisible(False)
            if self.game == 'valorant' and Path(valorant_icon_path).exists():
                pixmap = QPixmap(str(valorant_icon_path)).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.game_icon_label.setPixmap(pixmap)
            elif self.game == 'lol' and Path(lol_icon_path).exists():
                pixmap = QPixmap(str(lol_icon_path)).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.game_icon_label.setPixmap(pixmap)
            elif self.game == 'both' and Path(riot_icon_path).exists():
                pixmap = QPixmap(str(riot_icon_path)).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.game_icon_label.setPixmap(pixmap)

            self.rank_icon_label = QLabel(self)
            self.rank_icon_label.setFixedSize(game_icon_size, game_icon_size)
            self.rank_icon_label.setAlignment(Qt.AlignCenter)
            self.rank_icon_label.move(10, 10)
            self.rank_icon_label.setVisible(False)
            self._add_shadow_effect(self.rank_icon_label)

            if self.rank:
                rank_icon_path = get_asset_path(f"{self.rank.lower().replace(' ', '_')}.png")
                if os.path.exists(rank_icon_path):
                    pixmap = QPixmap(rank_icon_path).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.rank_icon_label.setPixmap(pixmap)

        self.update_content()

    def update_content(self):
        if self.current_rr is not None:
            self.current_rr_label.setText(str(self.current_rr))
        else:
            self.current_rr_label.setText("")

        if self.last_game_rr is not None:
            rr_text = f"+{self.last_game_rr}" if self.last_game_rr > 0 else str(self.last_game_rr)
            rr_color = "#a6e3a1" if self.last_game_rr > 0 else ("#f38ba8" if self.last_game_rr < 0 else "#e0d6d1")
            self.last_game_rr_label.setText(f"({rr_text})")
            self.last_game_rr_label.setStyleSheet(f"color: {rr_color}; font-size: 11px;")
        else:
            self.last_game_rr_label.setText("")

        in_game_text = ""
        if self.in_game_name and self.in_game_tag:
            in_game_text = f"{self.in_game_name}#{self.in_game_tag}"
        elif self.in_game_name:
            in_game_text = self.in_game_name
        self.in_game_name_tag_label.setText(in_game_text)

        if hasattr(self, 'switcher') and self.switcher:
            ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
            show_last_match = ui_settings.get("show_last_match_info", True)
            if show_last_match:
                last_map, last_agent = self.switcher.get_account_last_match_info(self.account_name)
                if last_map or last_agent:
                    match_parts = []
                    if last_map: match_parts.append(last_map)
                    if last_agent:
                        agent_icon = get_agent_icon_html(last_agent, self.switcher.base_dir, width=16, height=16)
                        match_parts.append(f"{agent_icon}{last_agent}")
                    self.last_match_label.setText(" • ".join(match_parts))
                else:
                    self.last_match_label.setText("")
            else:
                self.last_match_label.setText("")

        self.main_layout.invalidate()
        self.update()

    def set_icon(self, icon, size):
        self.icon = icon
        self.icon_label.setFixedSize(QSize(size, size))
        
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.transparent)

        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        if icon and not icon.isNull():
            source_pixmap = icon.pixmap(icon.actualSize(QSize(256, 256)))
            scaled_pixmap = source_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (size - scaled_pixmap.width()) / 2
            y = (size - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)
        else:
            default_icon_path = get_asset_path("valorant.png")
            if os.path.exists(default_icon_path):
                def_pix = QPixmap(default_icon_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(0, 0, def_pix)
            else:
                painter.fillRect(0, 0, size, size, QColor("#242933"))
        painter.end()
        
        self.icon_label.setPixmap(circular_pixmap)

    def _get_rank_border_color(self):
        if not self.rank:
            return None
        base_rank = self.rank.split()[0] if self.rank else "Unranked"
        rank_hex_colors = {
            "Iron": "#5a5959",
            "Bronze": "#a5855c",
            "Silver": "#bcc5cb",
            "Gold": "#ecce6e",
            "Platinum": "#3ab5c2",
            "Diamond": "#b584e0",
            "Ascendant": "#2e9e6b",
            "Immortal": "#c44b5c",
            "Radiant": "#fffaa8",
            "Unranked": "#4f555a"
        }
        return rank_hex_colors.get(base_rank)

    def _fast_blur_image(self, src_image, radius):
        if radius <= 0.1:
            return src_image
        r = int(round(radius))
        steps = 3
        current = src_image
        for _ in range(steps):
            down_w = max(4, current.width() // 2)
            down_h = max(4, current.height() // 2)
            down = current.scaled(down_w, down_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            current = down.scaled(src_image.width(), src_image.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        return current

    def _get_map_background_pixmap(self, map_name, target_size):
        if not map_name:
            return None
        cache_key = (map_name.lower(), target_size.width(), target_size.height())
        if hasattr(AccountWidget, '_map_pixmap_cache') and cache_key in AccountWidget._map_pixmap_cache:
            return AccountWidget._map_pixmap_cache[cache_key]

        map_filename = map_name.lower().replace(" ", "").replace("'", "") + ".png"
        map_path = None
        if hasattr(self, 'switcher') and self.switcher:
            possible_path = Path(self.switcher.base_dir) / "maps" / map_filename
            if possible_path.exists():
                map_path = possible_path

        if not map_path:
            local_maps_dir = Path(__file__).parent / "maps"
            possible_path = local_maps_dir / map_filename
            if possible_path.exists():
                map_path = possible_path

        if not map_path or not map_path.exists():
            return None

        src = QImage(str(map_path))
        if src.isNull():
            return None

        scaled = src.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        rect = QRect((scaled.width() - target_size.width()) // 2, (scaled.height() - target_size.height()) // 2, target_size.width(), target_size.height())
        cropped = scaled.copy(rect)

        sharp_pixmap = QPixmap.fromImage(cropped)

        blurred_image = self._fast_blur_image(cropped.convertToFormat(QImage.Format_ARGB32_Premultiplied), 4.0)
        darkener = QPainter(blurred_image)
        darkener.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        darkener.fillRect(blurred_image.rect(), QColor(0, 0, 0, 110))
        darkener.end()

        blurred_pixmap = QPixmap.fromImage(blurred_image)

        if not hasattr(AccountWidget, '_map_pixmap_cache'):
            AccountWidget._map_pixmap_cache = {}
        AccountWidget._map_pixmap_cache[cache_key] = (sharp_pixmap, blurred_pixmap)
        return sharp_pixmap, blurred_pixmap

    def _get_banner_background_pixmap(self, banner_url, target_size, zoom=1.0, offset_x=0.0, offset_y=0.0, blur_radius=4.0):
        cache_key = f"banner_{banner_url}_{target_size.width()}x{target_size.height()}_z{zoom:.2f}_ox{offset_x:.1f}_oy{offset_y:.1f}_b{blur_radius:.1f}"
        if hasattr(AccountWidget, '_map_pixmap_cache') and cache_key in AccountWidget._map_pixmap_cache:
            return AccountWidget._map_pixmap_cache[cache_key]

        pixmap = QPixmap()
        if os.path.exists(str(banner_url)):
            pixmap.load(str(banner_url))
        elif str(banner_url).startswith("http"):
            cache_dir = Path(self.switcher.base_dir) / "Assets" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            import hashlib
            url_hash = hashlib.md5(str(banner_url).encode('utf-8')).hexdigest()
            cached_file = cache_dir / f"banner_{url_hash}.png"
            if cached_file.exists() and cached_file.stat().st_size > 0:
                pixmap.load(str(cached_file))
            else:
                if not getattr(self, '_banner_download_in_progress', False):
                    self._banner_download_in_progress = True
                    def _download_banner_async(url, dest_path):
                        tmp_path = dest_path.with_suffix(".tmp")
                        try:
                            import urllib.request
                            urllib.request.urlretrieve(url, str(tmp_path))
                            if tmp_path.exists() and tmp_path.stat().st_size > 0:
                                if dest_path.exists():
                                    try:
                                        dest_path.unlink()
                                    except OSError:
                                        pass
                                tmp_path.rename(dest_path)
                                QTimer.singleShot(0, self.update)
                        except Exception:
                            if tmp_path.exists():
                                try:
                                    tmp_path.unlink()
                                except OSError:
                                    pass
                        finally:
                            self._banner_download_in_progress = False
                    threading.Thread(target=_download_banner_async, args=(banner_url, cached_file), daemon=True).start()

        if pixmap.isNull():
            return None

        scaled_w = max(10, int(target_size.width() * zoom))
        scaled_h = max(10, int(target_size.height() * zoom))
        scaled_pixmap = pixmap.scaled(scaled_w, scaled_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        base_x = (scaled_pixmap.width() - target_size.width()) // 2
        base_y = (scaled_pixmap.height() - target_size.height()) // 2
        crop_x = max(0, min(scaled_pixmap.width() - target_size.width(), int(base_x - offset_x)))
        crop_y = max(0, min(scaled_pixmap.height() - target_size.height(), int(base_y - offset_y)))

        sharp_pixmap = scaled_pixmap.copy(crop_x, crop_y, target_size.width(), target_size.height())

        sharp_image = sharp_pixmap.toImage().convertToFormat(QImage.Format_ARGB32_Premultiplied)
        blurred_image = self._fast_blur_image(sharp_image, blur_radius)

        darkener = QPainter(blurred_image)
        darkener.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        darkener.fillRect(blurred_image.rect(), QColor(0, 0, 0, 110))
        darkener.end()

        blurred_pixmap = QPixmap.fromImage(blurred_image)
        if not hasattr(AccountWidget, '_map_pixmap_cache'):
            AccountWidget._map_pixmap_cache = {}
        AccountWidget._map_pixmap_cache[cache_key] = (sharp_pixmap, blurred_pixmap)
        return sharp_pixmap, blurred_pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        border_radius = 20

        if self.is_add_button:
            opt = QStyleOption()
            opt.initFrom(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
            return

        ui_settings = self.switcher.get_ima_config().get("ui_settings", {}) if (hasattr(self, 'switcher') and self.switcher) else {}
        show_map_bg = ui_settings.get("show_map_background", False)
        
        cfg = self.switcher._load_game_config(self.account_name) if (hasattr(self, 'switcher') and self.switcher) else {}
        use_banner_bg = ui_settings.get("use_banner_background", cfg.get("use_banner_background", False))
        global_blur = float(ui_settings.get("banner_blur", cfg.get("banner_blur", 4.0)))

        map_data = None
        if use_banner_bg and hasattr(self, 'switcher') and self.switcher:
            banner_url = cfg.get("banner_card_url") or cfg.get("card_icon")
            if not banner_url:
                history = cfg.get("match_history", [])
                if history and isinstance(history, list) and len(history) > 0:
                    for p in history[0].get("players", []):
                        if p.get("name", "").lower() == self.account_name.lower() or (self.in_game_name and p.get("name", "").lower() == self.in_game_name.lower()):
                            banner_url = p.get("card_icon")
                            break
            if not banner_url and (self.in_game_name and self.in_game_tag):
                if not getattr(self, '_banner_fetch_in_progress', False):
                    self._banner_fetch_in_progress = True
                    threading.Thread(target=self._auto_fetch_account_banner, daemon=True).start()

            if banner_url:
                b_zoom = float(cfg.get("banner_zoom", 1.0))
                b_ox = float(cfg.get("banner_offset_x", 0.0))
                b_oy = float(cfg.get("banner_offset_y", 0.0))
                b_blur = global_blur
                map_data = self._get_banner_background_pixmap(
                    banner_url, rect.size(), zoom=b_zoom, offset_x=b_ox, offset_y=b_oy, blur_radius=b_blur
                )

        if not map_data and show_map_bg and hasattr(self, 'switcher') and self.switcher:
            last_map, _ = self.switcher.get_account_last_match_info(self.account_name)
            if last_map:
                map_data = self._get_map_background_pixmap(last_map, rect.size())

        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(rect), border_radius, border_radius)

        painter.save()
        painter.setClipPath(clip_path)

        if map_data:
            sharp_pixmap, blurred_pixmap = map_data
            if use_banner_bg:
                b_blur = global_blur
                if b_blur > 0.1:
                    painter.drawPixmap(rect, blurred_pixmap)
                else:
                    painter.drawPixmap(rect, sharp_pixmap)
            else:
                painter.drawPixmap(rect, sharp_pixmap)
        else:
            opt = QStyleOption()
            opt.initFrom(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

        painter.restore()

        rank_color_hex = self._get_rank_border_color()
        if not rank_color_hex:
            theme_dict = get_theme()
            rank_color_hex = theme_dict.get("accent", "#c89f68")

        glow_color = QColor(rank_color_hex)
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        for idx, (alpha, width_add) in enumerate([(40, 4.0), (25, 6.0), (12, 8.5)]):
            glow_pen = QPen(QColor(glow_color.red(), glow_color.green(), glow_color.blue(), alpha), width_add)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            inset = width_add / 2.0
            glow_rect = QRectF(rect).adjusted(inset, inset, -inset, -inset)
            painter.drawRoundedRect(glow_rect, border_radius - inset, border_radius - inset)
        painter.restore()

        pen_width = 3.5 if self.is_selected else 2.0
        border_pen = QPen(glow_color, pen_width)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        inset = pen_width / 2.0
        border_rect = QRectF(rect).adjusted(inset, inset, -inset, -inset)
        painter.drawRoundedRect(border_rect, border_radius - inset, border_radius - inset)

    def set_selected(self, selected):
        self.is_selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def set_show_game_icon(self, show):
        if hasattr(self, 'game_icon_label'):
            self.game_icon_label.setVisible(show)

    def set_show_rank_icon(self, show):
        if hasattr(self, 'rank_icon_label'):
            self.rank_icon_label.setVisible(show and self.rank is not None)

    def set_show_name_tag(self, show):
        if hasattr(self, 'in_game_name_tag_label'):
            self.in_game_name_tag_label.setVisible(show and bool(self.in_game_name or self.in_game_tag))
            if self.parentWidget() and hasattr(self.parentWidget(), 'update_window_size'):
                self.parentWidget().update_window_size()

    def set_show_current_rr(self, show):
        if hasattr(self, 'current_rr_label'):
            self.current_rr_label.setVisible(show and self.current_rr is not None)

    def set_show_last_game_rr(self, show):
        if hasattr(self, 'last_game_rr_label'):
            self.last_game_rr_label.setVisible(show and self.last_game_rr is not None)

    def set_show_last_match_info(self, show):
        if hasattr(self, 'last_match_label'):
            has_info = bool(self.last_match_label.text().strip())
            self.last_match_label.setVisible(show and has_info)
            target_height = 195 if (show and has_info) else 170
            self.setFixedSize(160, target_height)
            if self.parentWidget() and hasattr(self.parentWidget(), 'update_window_size'):
                self.parentWidget().update_window_size()

    def set_show_map_background(self, show):
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.account_name)

    def mouseDoubleClickEvent(self, event):
        if self.is_add_button: return
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.account_name)

    def enterEvent(self, event):
        if not self.is_add_button:
            self.icon_anim.setStartValue(self.icon_label.size())
            self.icon_anim.setEndValue(QSize(74, 74))
            self.icon_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_add_button:
            self.icon_anim.setStartValue(self.icon_label.size())
            self.icon_anim.setEndValue(QSize(70, 70))
            self.icon_anim.start()
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        if self.is_add_button: return
        self.context_menu_requested.emit(self.account_name, self.mapToGlobal(event.pos()))

    def update_data(self, account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, ui_settings):
        self.account_name = account_name
        self.game = game
        self.rank = rank
        self.in_game_name = in_game_name
        self.in_game_tag = in_game_tag
        self.current_rr = current_rr
        self.last_game_rr = last_game_rr

        self.set_icon(icon, 70)
        self.name_label.setText(self.account_name)

        if ui_settings:
            self.set_show_game_icon(ui_settings.get("show_game_icons", True))
            self.set_show_rank_icon(ui_settings.get("show_rank_icon_left", False))
            self.set_show_name_tag(ui_settings.get("show_name_tag", True))
            self.set_show_current_rr(ui_settings.get("show_current_rr", True))
            self.set_show_last_game_rr(ui_settings.get("show_last_game_rr", True))
            self.set_show_map_background(ui_settings.get("show_map_background", False))

        if self.current_rr is not None:
            self.current_rr_label.setText(str(self.current_rr))
        if self.last_game_rr is not None:
            rr_text = f"+{self.last_game_rr}" if self.last_game_rr > 0 else str(self.last_game_rr)
            rr_color = "#a6e3a1" if self.last_game_rr > 0 else ("#f38ba8" if self.last_game_rr < 0 else "#e0d6d1")
            self.last_game_rr_label.setText(f"({rr_text})")
            self.last_game_rr_label.setStyleSheet(f"color: {rr_color}; font-size: 11px;")
        
        game_icon_size = 24
        if self.rank:
            rank_icon_path = Path(get_asset_path(f"{self.rank.lower().replace(' ', '_')}.png"))
            if rank_icon_path.exists():
                pixmap = QPixmap(str(rank_icon_path)).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.rank_icon_label.setPixmap(pixmap)
            else:
                self.rank_icon_label.clear()
        else:
            self.rank_icon_label.clear()

        self.update()

    def _auto_fetch_account_banner(self):
        try:
            if hasattr(self, 'switcher') and self.switcher:
                self.switcher._get_or_fetch_account_puuid(self.account_name, self.in_game_name, self.in_game_tag)
                if hasattr(AccountWidget, '_map_pixmap_cache'):
                    AccountWidget._map_pixmap_cache.clear()
                QTimer.singleShot(0, self.update)
        except Exception:
            pass
        finally:
            self._banner_fetch_in_progress = False


class ProfileIconHoverWidget(QWidget):
    iconRemoved = pyqtSignal()
    iconClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 70)
        self.icon_pixmap = None
        self.setCursor(Qt.PointingHandCursor)

        self.trash_btn = QPushButton("✕", self)
        self.trash_btn.setFixedSize(22, 22)
        self.trash_btn.move(44, 4)
        self.trash_btn.setCursor(Qt.PointingHandCursor)
        self.trash_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border-radius: 11px;
                font-size: 11px;
                font-weight: bold;
                border: 1.5px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.trash_btn.clicked.connect(self.iconRemoved.emit)
        self.trash_btn.hide()

    def set_pixmap(self, pixmap):
        self.icon_pixmap = pixmap
        self.update()

    def enterEvent(self, event):
        if self.icon_pixmap and not self.icon_pixmap.isNull():
            self.trash_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.trash_btn.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.trash_btn.geometry().contains(event.pos()):
            self.iconClicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addEllipse(2, 2, 66, 66)
        painter.setClipPath(path)

        painter.fillRect(2, 2, 66, 66, QColor("#1a1e24"))
        if self.icon_pixmap and not self.icon_pixmap.isNull():
            painter.drawPixmap(2, 2, 66, 66, self.icon_pixmap)
        else:
            painter.setPen(QColor("#8fa7bb"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Icon")

        painter.setClipping(False)
        painter.setPen(QPen(QColor("#3b4252"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(2, 2, 66, 66)


class BannerCustomizerDialog(PopupDialog):
    def __init__(self, account_name, switcher_instance, config_data, parent=None):
        super().__init__(f"Banner Customizer - {account_name}", parent)
        self.account_name = account_name
        self.switcher = switcher_instance
        self.config_data = config_data
        self.setFixedSize(480, 440)

        ui_settings = self.switcher.get_ima_config().get("ui_settings", {}) if self.switcher else {}
        self.zoom = float(self.config_data.get("banner_zoom", 1.0))
        self.offset_x = float(self.config_data.get("banner_offset_x", 0.0))
        self.offset_y = float(self.config_data.get("banner_offset_y", 0.0))
        self.blur = float(ui_settings.get("banner_blur", self.config_data.get("banner_blur", 4.0)))

        self.last_mouse_pos = None
        self.is_dragging = False

        self.init_customizer_ui()

    def init_customizer_ui(self):
        self.content_layout.setSpacing(8)
        self.content_layout.setContentsMargins(16, 4, 16, 12)

        hint_lbl = QLabel("Drag on preview card to pan banner • Scroll mouse wheel to zoom in/out")
        hint_lbl.setStyleSheet("color: #8fa7bb; font-size: 11px;")
        hint_lbl.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(hint_lbl)

        self.preview_box = QWidget()
        self.preview_box.setFixedHeight(190)
        self.preview_box.setCursor(Qt.SizeAllCursor)
        box_layout = QHBoxLayout(self.preview_box)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setAlignment(Qt.AlignCenter)

        icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = self.switcher.get_saved_accounts().get(
            self.account_name, (None, None, None, None, None, None, None)
        )
        icon = self.switcher.get_qicon_from_path(icon_path) if icon_path else None

        self.card_preview = AccountWidget(
            self.account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr,
            parent=self.preview_box, switcher_instance=self.switcher
        )
        self.card_preview.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        box_layout.addWidget(self.card_preview)
        self.content_layout.addWidget(self.preview_box)

        self.preview_box.mousePressEvent = self.on_mouse_press
        self.preview_box.mouseMoveEvent = self.on_mouse_move
        self.preview_box.mouseReleaseEvent = self.on_mouse_release
        self.preview_box.wheelEvent = self.on_wheel

        self.card_preview.mousePressEvent = self.on_mouse_press
        self.card_preview.mouseMoveEvent = self.on_mouse_move
        self.card_preview.mouseReleaseEvent = self.on_mouse_release
        self.card_preview.wheelEvent = self.on_wheel

        ctrl_box = QGroupBox("Banner Adjustments (Blur applies to all accounts)")
        ctrl_layout = QFormLayout(ctrl_box)
        ctrl_layout.setSpacing(8)
        ctrl_layout.setContentsMargins(12, 10, 12, 10)

        self.blur_slider = ValueSlider(0, 20, step=0.5)
        self.blur_slider.setValue(self.blur)
        self.blur_slider.valueChanged.connect(self.on_blur_changed)
        ctrl_layout.addRow(QLabel("Backdrop Blur:"), self.blur_slider)

        self.zoom_lbl = QLabel(f"{self.zoom:.2f}x")
        self.zoom_lbl.setStyleSheet("color: #20e693; font-weight: bold;")
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(self.zoom_lbl)
        zoom_row.addStretch()

        reset_btn = QPushButton("Reset Position & Zoom")
        reset_btn.clicked.connect(self.reset_adjustments)
        zoom_row.addWidget(reset_btn)
        ctrl_layout.addRow(QLabel("Zoom Scale:"), zoom_row)

        self.content_layout.addWidget(ctrl_box)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        actions_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        actions_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save & Apply")
        save_btn.setObjectName("ApplyButton")
        save_btn.clicked.connect(self.on_save)
        actions_layout.addWidget(save_btn)

        self.content_layout.addLayout(actions_layout)

    def on_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.pos()

    def on_mouse_move(self, event):
        if self.is_dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.refresh_preview()

    def on_mouse_release(self, event):
        self.is_dragging = False

    def on_wheel(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 1.08 if delta > 0 else 0.92
        self.zoom = max(0.5, min(3.5, self.zoom * zoom_factor))
        self.zoom_lbl.setText(f"{self.zoom:.2f}x")
        self.refresh_preview()

    def on_blur_changed(self, val):
        self.blur = float(val)
        self.refresh_preview()

    def reset_adjustments(self):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.blur = 4.0
        self.blur_slider.setValue(4.0)
        self.zoom_lbl.setText("1.00x")
        self.refresh_preview()

    def refresh_preview(self):
        self.config_data["banner_zoom"] = self.zoom
        self.config_data["banner_offset_x"] = self.offset_x
        self.config_data["banner_offset_y"] = self.offset_y
        self.config_data["banner_blur"] = self.blur
        if self.switcher:
            cfg = self.switcher.get_ima_config()
            cfg_ui = cfg.setdefault("ui_settings", {})
            cfg_ui["banner_blur"] = self.blur
        if hasattr(AccountWidget, '_map_pixmap_cache'):
            AccountWidget._map_pixmap_cache.clear()
        self.card_preview.update()

    def on_save(self):
        self.refresh_preview()
        if self.switcher:
            cfg = self.switcher.get_ima_config()
            cfg_ui = cfg.setdefault("ui_settings", {})
            cfg_ui["banner_blur"] = self.blur
            self.switcher.set_ima_config({"ui_settings": cfg_ui})
            for acc in self.switcher.get_saved_accounts():
                acc_cfg = self.switcher._load_game_config(acc)
                acc_cfg["banner_blur"] = self.blur
                self.switcher._save_game_config(acc, acc_cfg)
        self.accept()


class CustomizeAccountDialog(PopupDialog):
    def __init__(self, account_name, switcher_instance, parent=None):
        super().__init__(f"Customize Account - {account_name}", parent)
        self.account_name = account_name
        self.switcher = switcher_instance
        self.setFixedSize(740, 560)

        current_icon_path, game, rank, ign, tag, current_rr, last_game_rr = self.switcher.get_saved_accounts().get(
            account_name, (None, None, None, None, None, None, None)
        )
        self.selected_icon_path = current_icon_path
        self.config_data = self.switcher._load_game_config(account_name)

        self.content_layout.setSpacing(10)
        self.content_layout.setContentsMargins(16, 8, 16, 14)

        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(14)

        left_widget = QWidget()
        left_widget.setFixedWidth(320)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        identity_box = QGroupBox("Account Details & Riot ID")
        identity_layout = QFormLayout(identity_box)
        identity_layout.setSpacing(8)
        identity_layout.setLabelAlignment(Qt.AlignLeft)

        self.name_edit = QLineEdit(account_name)
        self.name_edit.setPlaceholderText("Profile Name")
        identity_layout.addRow(QLabel("Profile Name:"), self.name_edit)

        ign_row = QHBoxLayout()
        ign_row.setSpacing(6)
        self.ign_edit = QLineEdit(ign or "")
        self.ign_edit.setPlaceholderText("In-Game Name")
        self.tag_edit = QLineEdit(tag or "")
        self.tag_edit.setPlaceholderText("Tag")
        self.tag_edit.setFixedWidth(80)
        ign_row.addWidget(self.ign_edit, 1)
        ign_row.addWidget(QLabel("#"))
        ign_row.addWidget(self.tag_edit)
        identity_layout.addRow(QLabel("In-Game Name:"), ign_row)

        self.puuid_edit = QLineEdit(str(self.config_data.get("puuid") or ""))
        self.puuid_edit.setPlaceholderText("Auto-detected via API or enter PUUID")
        identity_layout.addRow(QLabel("Riot PUUID:"), self.puuid_edit)

        left_layout.addWidget(identity_box)

        appearance_box = QGroupBox("Card Background (Applies to all accounts)")
        appearance_layout = QVBoxLayout(appearance_box)
        appearance_layout.setSpacing(8)

        toggle_row = QHBoxLayout()
        toggle_row.addWidget(QLabel("Use Banner:"))
        toggle_row.addStretch()

        self.banner_toggle = RadioButtonGroup("On", "Off")
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {}) if self.switcher else {}
        is_banner_on = ui_settings.get("use_banner_background", self.config_data.get("use_banner_background", False))
        self.banner_toggle.set_state(is_banner_on)
        self.banner_toggle.stateChanged.connect(self.on_banner_toggle_changed)
        toggle_row.addWidget(self.banner_toggle)
        appearance_layout.addLayout(toggle_row)

        card_preview_container = QWidget()
        card_preview_layout = QHBoxLayout(card_preview_container)
        card_preview_layout.setContentsMargins(0, 2, 0, 2)
        card_preview_layout.setAlignment(Qt.AlignCenter)

        icon = self.switcher.get_qicon_from_path(current_icon_path) if current_icon_path else None
        self.card_preview = AccountWidget(
            account_name, icon, game, rank, ign, tag, current_rr, last_game_rr,
            parent=card_preview_container, switcher_instance=self.switcher
        )
        self.card_preview.setCursor(Qt.PointingHandCursor)
        self.card_preview.setToolTip("Click card to customize banner zoom, pan & blur")
        self.card_preview.mousePressEvent = lambda e: self.open_banner_customizer() if e.button() == Qt.LeftButton else None
        card_preview_layout.addWidget(self.card_preview)
        appearance_layout.addWidget(card_preview_container)

        left_layout.addWidget(appearance_box)
        columns_layout.addWidget(left_widget)

        icon_box = QGroupBox("Profile Icon")
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setSpacing(8)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(12)

        self.icon_hover_widget = ProfileIconHoverWidget()
        self.icon_hover_widget.iconRemoved.connect(self.remove_icon)
        self.icon_hover_widget.iconClicked.connect(self.select_custom_icon)
        preview_row.addWidget(self.icon_hover_widget)

        icon_desc_box = QVBoxLayout()
        icon_desc_box.setSpacing(4)
        lbl_info = QLabel("<b>Profile Icon</b>")
        lbl_sub = QLabel("Upload custom file or pick an icon below. Hover to remove.")
        lbl_sub.setStyleSheet("color: #8fa7bb; font-size: 11px;")
        lbl_sub.setWordWrap(True)
        upload_btn = QPushButton("Upload Custom Image...")
        upload_btn.clicked.connect(self.select_custom_icon)
        icon_desc_box.addWidget(lbl_info)
        icon_desc_box.addWidget(lbl_sub)
        icon_desc_box.addWidget(upload_btn)
        preview_row.addLayout(icon_desc_box)
        preview_row.addStretch()

        icon_layout.addLayout(preview_row)

        self.icon_search = QLineEdit()
        self.icon_search.setPlaceholderText("Search agent or icon...")
        self.icon_search.textChanged.connect(self.filter_icons)
        icon_layout.addWidget(self.icon_search)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(self.grid_widget)
        icon_layout.addWidget(scroll, 1)

        columns_layout.addWidget(icon_box, 1)
        self.content_layout.addLayout(columns_layout)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("ApplyButton")
        save_btn.clicked.connect(self.on_save)
        action_layout.addWidget(save_btn)

        self.content_layout.addLayout(action_layout)

        self.all_icon_buttons = []
        self.update_preview()
        QTimer.singleShot(20, self.populate_icons)

    def on_banner_toggle_changed(self, is_on):
        self.config_data["use_banner_background"] = is_on
        if self.switcher:
            cfg = self.switcher.get_ima_config()
            cfg_ui = cfg.setdefault("ui_settings", {})
            cfg_ui["use_banner_background"] = is_on
        if hasattr(AccountWidget, '_map_pixmap_cache'):
            AccountWidget._map_pixmap_cache.clear()
        self.card_preview.update()

    def open_banner_customizer(self):
        dlg = BannerCustomizerDialog(self.account_name, self.switcher, self.config_data, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            if hasattr(AccountWidget, '_map_pixmap_cache'):
                AccountWidget._map_pixmap_cache.clear()
            self.card_preview.update()

    def select_custom_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon Image", "", "Images (*.png *.jpg *.jpeg *.ico *.webp *.bmp)"
        )
        if file_path:
            self.selected_icon_path = file_path
            self.update_preview()

    def remove_icon(self):
        self.selected_icon_path = None
        self.update_preview()

    def set_selected_icon(self, icon_path):
        self.selected_icon_path = icon_path
        self.update_preview()

    def update_preview(self):
        if self.selected_icon_path and os.path.exists(str(self.selected_icon_path)):
            icon = self.switcher.get_qicon_from_path(self.selected_icon_path)
            pixmap = icon.pixmap(64, 64)
            self.icon_hover_widget.set_pixmap(pixmap)
            self.card_preview.set_icon(icon, 70)
        else:
            self.icon_hover_widget.set_pixmap(None)
            self.card_preview.set_icon(None, 70)

    def populate_icons(self):
        agents_path = Path(self.switcher.base_dir) / "Agents"
        if not agents_path.exists():
            agents_path = Path(self.switcher.base_dir) / "icons"
        valorant_icons_path = Path(self.switcher.base_dir) / "Assets" / "valorant"

        icon_files = []
        if agents_path.exists():
            icon_files.extend(get_icon_paths_from_folder(str(agents_path)))
        if valorant_icons_path.exists():
            icon_files.extend(get_icon_paths_from_folder(str(valorant_icons_path)))

        self.all_icon_buttons = []
        for i, icon_path in enumerate(icon_files):
            name = Path(icon_path).stem
            btn = QPushButton()
            btn.setFixedSize(52, 52)
            btn.setToolTip(name)
            icon = self.switcher.get_qicon_from_path(icon_path)
            pix = icon.pixmap(44, 44)
            circ = QPixmap(44, 44)
            circ.fill(Qt.transparent)
            p = QPainter(circ)
            p.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, 44, 44)
            p.setClipPath(path)
            p.drawPixmap(0, 0, pix)
            p.end()
            btn.setIcon(QIcon(circ))
            btn.setIconSize(QSize(44, 44))
            btn.clicked.connect(lambda _, ip=icon_path: self.set_selected_icon(ip))
            self.all_icon_buttons.append((name.lower(), btn, icon_path))
            self.grid_layout.addWidget(btn, i // 5, i % 5)

    def filter_icons(self, text):
        query = text.strip().lower()
        visible_idx = 0
        for name, btn, ip in self.all_icon_buttons:
            match = not query or query in name
            btn.setVisible(match)
            if match:
                self.grid_layout.removeWidget(btn)
                self.grid_layout.addWidget(btn, visible_idx // 5, visible_idx % 5)
                visible_idx += 1

    def on_save(self):
        new_name = self.name_edit.text().strip()
        new_ign = self.ign_edit.text().strip() or None
        new_tag = self.tag_edit.text().strip() or None
        new_puuid = self.puuid_edit.text().strip()
        use_banner = self.banner_toggle.get_state()

        if not new_name:
            CustomMessageDialog.warning(self, "Invalid Name", "Account name cannot be empty.")
            return

        if new_name != self.account_name and new_name in self.switcher.get_saved_accounts():
            CustomMessageDialog.warning(self, "Account Exists", f'An account named "{new_name}" already exists.')
            return

        final_name = self.account_name
        if new_name != self.account_name:
            if self.switcher.rename_account(self.account_name, new_name):
                final_name = new_name
            else:
                CustomMessageDialog.critical(self, "Rename Error", "Failed to rename account directory.")
                return

        self.switcher.set_account_in_game_name_tag(final_name, new_ign, new_tag)

        cfg = self.switcher._load_game_config(final_name)
        if new_puuid:
            cfg["puuid"] = new_puuid
        cfg["use_banner_background"] = use_banner
        cfg["banner_zoom"] = self.config_data.get("banner_zoom", 1.0)
        cfg["banner_offset_x"] = self.config_data.get("banner_offset_x", 0.0)
        cfg["banner_offset_y"] = self.config_data.get("banner_offset_y", 0.0)
        cfg["banner_blur"] = self.config_data.get("banner_blur", 4.0)
        self.switcher._save_game_config(final_name, cfg)

        ui_cfg = self.switcher.get_ima_config().get("ui_settings", {})
        ui_cfg["use_banner_background"] = use_banner
        ui_cfg["banner_blur"] = cfg["banner_blur"]
        self.switcher.set_ima_config({"ui_settings": ui_cfg})

        for acc in self.switcher.get_saved_accounts():
            acc_cfg = self.switcher._load_game_config(acc)
            acc_cfg["use_banner_background"] = use_banner
            acc_cfg["banner_blur"] = cfg["banner_blur"]
            self.switcher._save_game_config(acc, acc_cfg)

        if self.selected_icon_path:
            self.switcher.set_account_icon(final_name, Path(self.selected_icon_path))
        else:
            self.switcher.remove_account_icon(final_name)

        if hasattr(AccountWidget, '_map_pixmap_cache'):
            AccountWidget._map_pixmap_cache.clear()

        self.accept()


class HoverButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anim = QPropertyAnimation(self, b"iconSize", duration=150, easingCurve=QEasingCurve.OutQuad)

    def enterEvent(self, event):
        self.original_icon_size = self.iconSize()
        self.hover_icon_size = QSize(int(self.original_icon_size.width() * 1.2), int(self.original_icon_size.height() * 1.2))
        self.anim.setEndValue(self.hover_icon_size)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setEndValue(self.original_icon_size)
        self.anim.start()

class UpdateSignals(QObject):
    check_finished = pyqtSignal(dict)
    progress = pyqtSignal(int, int, int)
    download_finished = pyqtSignal(bool, str)

class UpdateCheckWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, switcher=None, app_version=None, parent=None):
        super().__init__(parent)
        self.switcher = switcher
        self.app_version = app_version

    def run(self):
        try:
            import updater
            res_dict = updater.check_for_app_update(local_version=self.app_version)
            self.finished.emit(res_dict)
        except Exception as error:
            logging.error(f"Update check worker exception: {error}")
            self.finished.emit({
                "has_update": False,
                "version": str(self.app_version or ""),
                "url": "",
                "notes": f"Error: {error}",
                "size": 0,
                "error": str(error)
            })

class UpdateDialog(PopupDialog):
    def __init__(self, switcher_instance, parent=None, source_button=None):
        super().__init__("Software Update", parent)
        self.switcher = switcher_instance
        self.source_button = source_button
        self.setFixedWidth(420)
        self.setMinimumHeight(240)

        self.has_update = False
        self.download_url = None
        self.installer_path = None
        self.file_size = 0
        self.check_worker = None

        self.signals = UpdateSignals(self)
        self.signals.check_finished.connect(self.on_update_check_finished)
        self.signals.progress.connect(self.on_download_progress)
        self.signals.download_finished.connect(self.on_download_finished)

        self.init_update_ui()
        self.start_check_for_updates()

    def showEvent(self, event):
        super().showEvent(event)
        if self.source_button and self.source_button.isVisible():
            btn_glob = self.source_button.mapToGlobal(QPoint(0, 0))
            btn_center_x = btn_glob.x() + self.source_button.width() // 2
            btn_bottom_y = btn_glob.y() + self.source_button.height() + 8
            
            new_x = btn_center_x - self.width() // 2
            new_y = btn_bottom_y

            screen = QApplication.screenAt(btn_glob) or QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                if new_x + self.width() > geom.right() - 10:
                    new_x = geom.right() - self.width() - 10
                if new_x < geom.left() + 10:
                    new_x = geom.left() + 10
                if new_y + self.height() > geom.bottom() - 10:
                    new_y = btn_glob.y() - self.height() - 8
            self.move(new_x, new_y)
        else:
            self.center_on_parent()

    def init_update_ui(self):
        self.content_layout.setContentsMargins(20, 15, 20, 20)
        self.content_layout.setSpacing(12)

        logo_path = get_asset_path("app_icon.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pix = QPixmap(logo_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
            logo_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(logo_label)

        from game_switcher import APP_VERSION
        self.header_label = QLabel(f"<b>iMA Switcher</b> (Current: v{APP_VERSION})")
        self.header_label.setStyleSheet("font-size: 15px; color: #e0d6d1;")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.header_label)
        
        self.content_layout.addSpacing(10)

        self.status_label = QLabel("Checking for updates from GitHub...")
        self.status_label.setStyleSheet("font-size: 13px; color: #c89f68;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.content_layout.addWidget(self.status_label)
        
        self.content_layout.addSpacing(10)

        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: #242223;
                color: #e0d6d1;
                border: 1px solid #4f4a4b;
                border-radius: 10px;
                padding: 8px;
                font-size: 12px;
            }
        """)
        self.notes_edit.hide()
        self.content_layout.addWidget(self.notes_edit)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #242223;
                border: 1px solid #4f4a4b;
                border-radius: 10px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #c89f68;
                border-radius: 9px;
            }
        """)
        self.progress_bar.hide()
        self.content_layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.action_btn = QPushButton("Checking...")
        self.action_btn.setEnabled(False)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #c89f68;
                color: #2c2a2b;
                font-size: 13px;
                font-weight: bold;
                border-radius: 12px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #d9b68b;
            }
            QPushButton:disabled {
                background-color: #4f4a4b;
                color: #888888;
            }
        """)
        self.action_btn.clicked.connect(self.on_action_button_clicked)
        button_layout.addStretch()
        button_layout.addWidget(self.action_btn)
        button_layout.addStretch()

        self.content_layout.addLayout(button_layout)

    def start_check_for_updates(self):
        self.status_label.setText("Checking for update...")
        self.action_btn.setText("Checking...")
        self.action_btn.setEnabled(False)
        self.notes_edit.hide()

        if hasattr(self, 'timeout_timer') and self.timeout_timer:
            self.timeout_timer.stop()
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.on_check_timeout)
        self.timeout_timer.start(15000)

        from game_switcher import APP_VERSION
        if hasattr(self, 'check_worker') and self.check_worker and self.check_worker.isRunning():
            self.check_worker.quit()
            self.check_worker.wait()

        self.check_worker = UpdateCheckWorker(self.switcher, app_version=APP_VERSION, parent=self)
        self.check_worker.finished.connect(self.on_update_check_finished)
        self.check_worker.start()

    def on_check_timeout(self):
        self.action_btn.setEnabled(True)
        self.setFixedSize(420, 240)
        self.status_label.setText("⚠️ Connection timed out. Please try again.")
        self.action_btn.setText("Check Again")

    def on_update_check_finished(self, result):
        if hasattr(self, 'timeout_timer') and self.timeout_timer:
            self.timeout_timer.stop()
        self.action_btn.setEnabled(True)

        has_update = False
        url = ""
        notes = ""
        size = 0

        if isinstance(result, dict):
            has_update = result.get("has_update", False)
            url = result.get("url", "")
            notes = result.get("notes", "")
            size = result.get("size", 0)

        self.has_update = has_update
        self.download_url = url
        self.file_size = size

        if has_update:
            self.setFixedSize(520, 420)
            size_mb = size / (1024 * 1024) if size else 0
            size_str = f" ({size_mb:.1f} MB)" if size_mb > 0 else ""
            self.status_label.setText(f"🎉 New update available!{size_str}")
            self.notes_edit.setPlainText(f"Release Details:\n{notes}")
            self.notes_edit.show()
            self.action_btn.setText("Update Now")
        else:
            self.setFixedSize(420, 240)
            self.status_label.setText("✓ You are on the latest version.")
            self.action_btn.setText("Check Again")

    def on_action_button_clicked(self):
        if self.has_update:
            self.start_download()
        else:
            self.start_check_for_updates()

    def start_download(self):
        if not self.download_url:
            return
        self.action_btn.setEnabled(False)
        self.status_label.setText("Downloading latest build...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        def _progress_cb(downloaded, total):
            if total > 0:
                pct = int((downloaded / total) * 100)
                self.signals.progress.emit(pct, downloaded, total)

        def _download_worker():
            import updater
            success, msg = updater.download_and_apply_update(self.download_url, progress_callback=_progress_cb)
            self.signals.download_finished.emit(bool(success), str(msg or ""))

        threading.Thread(target=_download_worker, daemon=True).start()

    def on_download_progress(self, pct, downloaded, total):
        self.progress_bar.setValue(pct)
        d_mb = downloaded / (1024 * 1024)
        t_mb = total / (1024 * 1024)
        self.status_label.setText(f"Downloading update... {d_mb:.1f} MB / {t_mb:.1f} MB ({pct}%)")

    def on_download_finished(self, success, error_msg):
        if success:
            self.status_label.setText("✓ Download complete! Restarting app...")
            self.progress_bar.setValue(100)
        else:
            logging.error(f"Update download/apply failed: {error_msg}")
            display_err = error_msg if error_msg else "Unknown error"
            self.status_label.setText(f"❌ Update failed: {display_err}")
            self.action_btn.setEnabled(True)
            self.action_btn.setText("Retry Update")

    def apply_and_close(self):
        self.switcher.apply_update(str(self.installer_path))

class InstallerDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Install iMA Switcher", parent)
        self.setFixedSize(500, 470)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window) 
        
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)

        logo_path = get_asset_path("app_icon.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pix = QPixmap(logo_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
            logo_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(logo_label)

        self.content_layout.addWidget(QLabel("Choose Installation Folder:"))
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        default_path = Path(os.getenv('LOCALAPPDATA')) / "iMA Switcher"
        self.path_edit.setText(str(default_path))
        self.path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        path_layout.addWidget(self.path_edit)
        
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        browse_button.clicked.connect(self.select_folder)
        path_layout.addWidget(browse_button)
        self.content_layout.addLayout(path_layout)
        
        self.content_layout.addWidget(QLabel("Riot Client Executable Path:"))
        riot_path_layout = QHBoxLayout()
        self.riot_path_edit = QLineEdit()
        self.riot_path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        riot_path_layout.addWidget(self.riot_path_edit)
        
        riot_browse_button = QPushButton("Browse")
        riot_browse_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        riot_browse_button.clicked.connect(self.select_riot_games_folder)
        riot_path_layout.addWidget(riot_browse_button)
        self.content_layout.addLayout(riot_path_layout)

        self.riot_path_warning_label = QLabel("")
        self.riot_path_warning_label.setStyleSheet("color: red; font-size: 10px;")
        self.content_layout.addWidget(self.riot_path_warning_label)

        from game_switcher import GameSwitcher
        switcher = GameSwitcher()
        switcher.initialize_riot_client_paths() 
        found_riot_path = switcher.riot_games_config.get("ExeLocationDefault")
        if found_riot_path and os.path.exists(found_riot_path):
            self.riot_path_edit.setText(found_riot_path)
            self.riot_path_warning_label.setText("")
        else:
            self.riot_path_edit.setText("")
            self.riot_path_warning_label.setText("Please select 'RiotClientServices.exe'.")

        self.desktop_shortcut_checkbox = QCheckBox("Add shortcut to Desktop")
        self.desktop_shortcut_checkbox.setChecked(True)
        self.desktop_shortcut_checkbox.setStyleSheet("color: #FFFFFF;")
        self.content_layout.addWidget(self.desktop_shortcut_checkbox)

        self.start_menu_shortcut_checkbox = QCheckBox("Add shortcut to Start Menu (Optional)")
        self.start_menu_shortcut_checkbox.setChecked(True)
        self.start_menu_shortcut_checkbox.setStyleSheet("color: #FFFFFF;")
        self.content_layout.addWidget(self.start_menu_shortcut_checkbox)

        self.content_layout.addStretch()
        
        install_button = QPushButton("Install")
        install_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        install_button.clicked.connect(self.accept);
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(install_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)
        
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Installation Folder")
        if folder_path:
            self.path_edit.setText(folder_path)

    def select_riot_games_folder(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select RiotClientServices.exe", "", "Executable Files (*.exe)")
        if file_path:
            self.riot_path_edit.setText(file_path)
            self.riot_path_warning_label.setText("") # Clear warning if user manually selects

    def find_riot_client_path(self):
        common_paths = [
            os.path.join("C:", os.sep, "Riot Games", "Riot Client", "RiotClientServices.exe"),
            os.path.join(os.getenv('PROGRAMFILES'), "Riot Games", "Riot Client", "RiotClientServices.exe"),
            os.path.join(os.getenv('PROGRAMFILES(X86)'), "Riot Games", "Riot Client", "RiotClientServices.exe"),
        ]
        
        found_path = None
        for path in common_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            self.riot_path_edit.setText(found_path)
            self.riot_path_warning_label.setText("")
        else:
            self.riot_path_edit.setText("")
            self.riot_path_warning_label.setText("RiotClientServices.exe not found. Please locate it manually.")

    def get_install_path(self):
        return self.path_edit.text()

    def get_riot_games_path(self):
        return self.riot_path_edit.text()

    def should_add_desktop_shortcut(self):
        return self.desktop_shortcut_checkbox.isChecked()

    def should_add_start_menu_shortcut(self):
        return self.start_menu_shortcut_checkbox.isChecked()

    



from game_switcher import GameSwitcher

class BackupRestoreDialog(PopupDialog):
    def __init__(self, parent=None, mode=None):
        title = "Backup Profiles" if mode == "backup" else "Restore Profiles"
        super().__init__(title, parent)
        self.setFixedSize(350, 200)
        self.selection = None

        label_text = "Choose backup location:" if mode == "backup" else "Choose restore location:"
        message_label = QLabel(label_text)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.content_layout.addWidget(message_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        local_button = QPushButton("Local")
        local_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        local_button.clicked.connect(lambda: self.set_selection("local"))
        button_layout.addWidget(local_button)

        drive_button = QPushButton("Google Drive")
        drive_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        drive_button.clicked.connect(lambda: self.set_selection("google_drive"))
        button_layout.addWidget(drive_button)

        self.content_layout.addLayout(button_layout)

    def set_selection(self, selection):
        self.selection = selection
        self.accept()

    def get_selection(self):
        return self.selection


class HistoryWorker(QThread):
    history_loaded = pyqtSignal(list)

    def __init__(self, switcher, account_name, force_refresh=False):
        super().__init__()
        self.switcher = switcher
        self.account_name = account_name
        self.force_refresh = force_refresh

    def run(self):
        if not self.switcher:
            self.history_loaded.emit([])
            return
        matches = self.switcher.fetch_account_match_history(self.account_name, force_refresh=self.force_refresh)
        self.history_loaded.emit(matches)


class AccountHistoryDialog(PopupDialog):
    def __init__(self, account_name, in_game_name=None, in_game_tag=None, parent=None, switcher_instance=None):
        title = f"Match History - {account_name}"
        super().__init__(title, parent)
        self.account_name = account_name
        self.in_game_name = in_game_name
        self.switcher = switcher_instance
        self.worker = None
        self.sort_mode = "acs"
        self.setFixedSize(880, 620)

        # Inherit theme colors dynamically
        t = get_theme()
        self.theme = t
        self.main_widget.setStyleSheet(f"""
            #popup_widget {{ background-color: {t['bg_main']}; border-radius: 15px; border: 1px solid {t['border']}; }}
            QLabel {{ color: {t['text_secondary']}; }}
        """)

        header_widget = QWidget(objectName="HistoryHeaderWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)

        self.account_combo = QComboBox()
        self.populate_account_combo()
        self.account_combo.currentIndexChanged.connect(self.on_account_combo_changed)
        header_layout.addWidget(self.account_combo, 2)

        self.rank_icon_label = QLabel()
        self.rank_icon_label.setFixedSize(28, 28)
        header_layout.addWidget(self.rank_icon_label)

        self.rank_rr_label = QLabel()
        header_layout.addWidget(self.rank_rr_label, 2)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh History")
        self.refresh_btn.setObjectName("ApplyButton")
        self.refresh_btn.clicked.connect(lambda: self.load_history(force_refresh=True))
        header_layout.addWidget(self.refresh_btn)

        self.content_layout.addWidget(header_widget)

        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)

        self.setup_matches_page()
        self.setup_detail_page()

        self.update_header_rank_info()
        QTimer.singleShot(100, lambda: self.load_history(force_refresh=False))

    def populate_account_combo(self):
        self.account_combo.blockSignals(True)
        self.account_combo.clear()
        if self.switcher:
            saved_accounts = self.switcher.get_saved_accounts()
            for acc_name, data in saved_accounts.items():
                _, _, _, ign, tag, _, _ = data
                label = f"{acc_name} ({ign}#{tag})" if ign and tag else acc_name
                self.account_combo.addItem(label, acc_name)
                if acc_name == self.account_name:
                    self.account_combo.setCurrentIndex(self.account_combo.count() - 1)
        self.account_combo.blockSignals(False)

    def set_account(self, account_name):
        self.account_name = account_name
        if self.switcher:
            saved = self.switcher.get_saved_accounts().get(account_name)
            if saved:
                _, _, _, self.in_game_name, self.in_game_tag, _, _ = saved

        self.setWindowTitle(f"Match History - {account_name}")
        self.populate_account_combo()
        self.update_header_rank_info()
        self.stacked_widget.setCurrentIndex(0)
        self.load_history(force_refresh=False)

    def on_account_combo_changed(self, index):
        acc_name = self.account_combo.itemData(index)
        if acc_name and acc_name != self.account_name:
            self.set_account(acc_name)

    def update_header_rank_info(self):
        if not self.switcher:
            return
        saved = self.switcher.get_saved_accounts().get(self.account_name)
        if not saved:
            return
        _, _, rank, _, _, current_rr, last_game_rr = saved

        rank_str = rank or "Unranked"
        rank_icon_path = get_asset_path(f"{rank_str.lower().replace(' ', '_')}.png")
        if os.path.exists(rank_icon_path):
            pixmap = QPixmap(rank_icon_path).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.rank_icon_label.setPixmap(pixmap)
            self.rank_icon_label.setVisible(True)
        else:
            self.rank_icon_label.setVisible(False)

        rr_str = f" • {current_rr} RR" if current_rr is not None else ""
        last_rr_str = ""
        if last_game_rr is not None:
            color = self.theme['accent'] if last_game_rr > 0 else (self.theme['danger'] if last_game_rr < 0 else self.theme['text_muted'])
            sign = "+" if last_game_rr > 0 else ""
            last_rr_str = f" <font color='{color}'>({sign}{last_game_rr})</font>"

        self.rank_rr_label.setText(f"<b>{rank_str}</b>{rr_str}{last_rr_str}")

    def setup_matches_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 5, 0, 5)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
            }
        """)

        self.matches_container = QWidget()
        self.matches_container.setStyleSheet("background-color: transparent;")
        self.matches_layout = QVBoxLayout(self.matches_container)
        self.matches_layout.setContentsMargins(0, 2, 0, 2)
        self.matches_layout.setSpacing(4)
        self.matches_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.matches_container)
        layout.addWidget(self.scroll_area)

        self.status_label = QLabel("Loading match history...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 20px;")
        self.matches_layout.addWidget(self.status_label)

        self.stacked_widget.addWidget(page)

    def setup_detail_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("← Back to Matches")
        self.back_btn.setObjectName("ApplyButton")
        self.back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        top_bar.addWidget(self.back_btn)

        self.detail_header_label = QLabel("Match Scoreboard")
        self.detail_header_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        top_bar.addWidget(self.detail_header_label)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)

        self.detail_container = QWidget()
        self.detail_container.setStyleSheet("background-color: transparent;")
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(12)
        self.detail_layout.setAlignment(Qt.AlignTop)

        self.detail_scroll.setWidget(self.detail_container)
        layout.addWidget(self.detail_scroll)

        self.stacked_widget.addWidget(page)

    def load_history(self, force_refresh=False):
        self.refresh_btn.setEnabled(False)
        if force_refresh:
            self.status_label.setText("Fetching latest matches from Henrik API...")
        else:
            self.status_label.setText("Loading match history...")
        self.status_label.setVisible(True)

        for i in reversed(range(self.matches_layout.count())):
            item = self.matches_layout.itemAt(i)
            if item and item.widget() and item.widget() != self.status_label:
                item.widget().deleteLater()

        self.worker = HistoryWorker(self.switcher, self.account_name, force_refresh=force_refresh)
        self.worker.history_loaded.connect(self._on_history_loaded)
        self.worker.start()

    def _on_history_loaded(self, matches):
        self.refresh_btn.setEnabled(True)
        if not matches:
            self.status_label.setText("No recent match history found for this account.")
            self.status_label.setVisible(True)
            return

        self.status_label.setVisible(False)
        for match in matches:
            card = self._create_match_card(match)
            self.matches_layout.addWidget(card)

    def _create_match_card(self, match):
        card = QWidget()
        card.setObjectName("MatchCard")
        card.setCursor(Qt.PointingHandCursor)
        result = match.get("result", "DRAW").upper()
        if result == "WIN":
            result = "VICTORY"
        elif result == "LOSS":
            result = "DEFEAT"
        t = get_theme()

        # Authentic low-contrast vivid translucent gradients matching in-game Valorant UI
        if result == "VICTORY":
            bg_style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(18, 62, 68, 0.40), stop:0.70 rgba(18, 62, 68, 0.40), stop:1 rgba(12, 38, 44, 0.20)); border-left: 3px solid #10b981; border-top: 1px solid rgba(16, 185, 129, 0.2); border-bottom: 1px solid rgba(16, 185, 129, 0.2); border-right: none;"
            hover_bg = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(24, 78, 86, 0.55), stop:0.70 rgba(24, 78, 86, 0.55), stop:1 rgba(16, 48, 56, 0.30)); border-left: 3px solid #34d399; border-top: 1px solid #10b981; border-bottom: 1px solid #10b981; border-right: none;"
            result_color = "#20e693"
        elif result == "DEFEAT":
            bg_style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(62, 22, 32, 0.40), stop:0.70 rgba(62, 22, 32, 0.40), stop:1 rgba(38, 14, 22, 0.20)); border-left: 3px solid #ff4655; border-top: 1px solid rgba(255, 70, 85, 0.2); border-bottom: 1px solid rgba(255, 70, 85, 0.2); border-right: none;"
            hover_bg = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(78, 28, 40, 0.55), stop:0.70 rgba(78, 28, 40, 0.55), stop:1 rgba(48, 18, 28, 0.30)); border-left: 3px solid #ff7b88; border-top: 1px solid #ff4655; border-bottom: 1px solid #ff4655; border-right: none;"
            result_color = "#ff4655"
        else:
            bg_style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(45, 52, 62, 0.40), stop:0.70 rgba(45, 52, 62, 0.40), stop:1 rgba(28, 34, 42, 0.20)); border-left: 3px solid #94a3b8; border-top: 1px solid rgba(148, 163, 184, 0.2); border-bottom: 1px solid rgba(148, 163, 184, 0.2); border-right: none;"
            hover_bg = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(58, 66, 78, 0.55), stop:0.70 rgba(58, 66, 78, 0.55), stop:1 rgba(36, 42, 52, 0.30)); border-left: 3px solid #cbd5e1; border-top: 1px solid #94a3b8; border-bottom: 1px solid #94a3b8; border-right: none;"
            result_color = "#94a3b8"

        card.setStyleSheet(f"""
            #MatchCard {{
                {bg_style}
                border-radius: 0px;
            }}
            #MatchCard:hover {{
                {hover_bg}
            }}
        """)

        raw_map_name = match.get("map", "Map")
        if "/" in raw_map_name:
            raw_map_name = raw_map_name.rstrip("/").split("/")[-1]
        card.map_name = raw_map_name.strip().strip('"').strip("'")
        maps_dir = (self.switcher.base_dir / "maps") if self.switcher else Path("maps")
        card.map_pixmap = None
        for candidate in [card.map_name.lower(), card.map_name, card.map_name.lower().replace(" ", "_"), card.map_name.replace(" ", "_")]:
            p = maps_dir / f"{candidate}.png"
            if p.exists():
                card.map_pixmap = QPixmap(str(p))
                break

        def card_paint_event(event):
            opt = QStyleOption()
            opt.initFrom(card)
            p = QPainter(card)
            p.setRenderHint(QPainter.Antialiasing)
            card.style().drawPrimitive(QStyle.PE_Widget, opt, p, card)

            if card.map_pixmap and not card.map_pixmap.isNull():
                map_w = 260
                map_h = card.height()
                map_rect = QRect(card.width() - map_w, 0, map_w, map_h)

                scaled = card.map_pixmap.scaled(map_w, map_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

                buffer = QPixmap(map_w, map_h)
                buffer.fill(Qt.transparent)

                bp = QPainter(buffer)
                bp.drawPixmap(0, 0, scaled)

                grad = QLinearGradient(0, 0, map_w * 0.55, 0)
                grad.setColorAt(0.0, QColor(0, 0, 0, 0))
                grad.setColorAt(1.0, QColor(0, 0, 0, 255))

                bp.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                bp.fillRect(buffer.rect(), grad)
                bp.end()

                p.drawPixmap(map_rect.x(), map_rect.y(), buffer)

            p.end()

        card.paintEvent = card_paint_event

        layout = QHBoxLayout(card)
        layout.setContentsMargins(6, 4, 12, 4)
        layout.setSpacing(10)

        # 1. Left Section (Agent portrait + Rank icon/RR + KDA/Score)
        left_container = QWidget()
        left_container.setFixedWidth(230)
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        agent_name = match.get("agent", "Agent")
        agent_icon_path = get_asset_path(f"{agent_name}.png")
        if not os.path.exists(agent_icon_path) and self.switcher:
            agent_icon_path = str(self.switcher.base_dir / "Agents" / f"{agent_name}.png")

        agent_lbl = QLabel()
        agent_lbl.setFixedSize(48, 48)
        if os.path.exists(agent_icon_path):
            pix = QPixmap(agent_icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            agent_lbl.setPixmap(pix)
        else:
            agent_lbl.setText("⚔️")
            agent_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        left_layout.addWidget(agent_lbl)

        saved = self.switcher.get_saved_accounts().get(self.account_name) if self.switcher else None
        rank_str = match.get("rank") or (saved[2] if saved and saved[2] else "Unranked")
        rank_icon_path = get_asset_path(f"{rank_str.lower().replace(' ', '_')}.png")
        
        rank_vbox = QVBoxLayout()
        rank_vbox.setSpacing(1)
        rank_vbox.setAlignment(Qt.AlignCenter)
        if os.path.exists(rank_icon_path):
            rank_lbl = QLabel()
            rank_lbl.setPixmap(QPixmap(rank_icon_path).scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            rank_vbox.addWidget(rank_lbl, 0, Qt.AlignCenter)

        rr_change = match.get("rr_change")
        if rr_change is not None:
            rr_sign = "+" if rr_change > 0 else ""
            rr_color = "#20e693" if rr_change > 0 else ("#ff4655" if rr_change < 0 else "#94a3b8")
            rr_chip = QLabel(f"<b>{rr_sign}{rr_change}</b>")
            rr_chip.setStyleSheet(f"font-size: 12px; font-weight: 900; color: {rr_color}; background: transparent;")
            rank_vbox.addWidget(rr_chip, 0, Qt.AlignCenter)
        else:
            rr_chip = QLabel("<b>--</b>")
            rr_chip.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b; background: transparent;")
            rank_vbox.addWidget(rr_chip, 0, Qt.AlignCenter)

        left_layout.addLayout(rank_vbox)

        kda_vbox = QVBoxLayout()
        kda_vbox.setSpacing(1)
        kda_raw = match.get("kda", "0/0/0").replace(" / ", " / ")
        kda_lbl = QLabel(f"<font color='#ffffff' size='4'><b>KDA</b></font> &nbsp;&nbsp;<font color='#ffffff' size='4'><b>{kda_raw}</b></font>")
        kda_lbl.setStyleSheet("font-size: 14px; font-family: 'Segoe UI', sans-serif; background: transparent;")
        kda_vbox.addWidget(kda_lbl)

        score_val = match.get("score", "0")
        players = match.get("players", [])
        for p in players:
            if self.in_game_name and p.get("name", "").lower() == self.in_game_name.lower():
                score_val = f"{p.get('score', 0):,}"
                break
        score_lbl = QLabel(f"<font color='#64748b' size='2'>SCORE</font> &nbsp;<font color='#cbd5e1' size='2'><b>{score_val}</b></font>")
        score_lbl.setStyleSheet("font-size: 12px; background: transparent;")
        kda_vbox.addWidget(score_lbl)
        left_layout.addLayout(kda_vbox)

        layout.addWidget(left_container)
        layout.addSpacing(30)

        # 2. VICTORY / DEFEAT + Score Section (Positioned close to KDA, strictly locked vertically)
        center_container = QWidget()
        center_container.setFixedWidth(130)
        res_layout = QVBoxLayout(center_container)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setAlignment(Qt.AlignCenter)
        res_layout.setSpacing(1)

        res_label = QLabel(result)
        res_label.setStyleSheet(f"font-size: 16px; font-weight: 900; color: {result_color}; letter-spacing: 1.5px; background: transparent;")
        res_layout.addWidget(res_label, 0, Qt.AlignCenter)

        score_text = match.get("score", "-")
        score_parts = score_text.split(" - ")
        if len(score_parts) == 2:
            s1, s2 = score_parts[0], score_parts[1]
            if result == "VICTORY":
                formatted_score_html = f"<font color='#20e693' size='4'><b>{s1}</b></font> <font color='#94a3b8'>-</font> <font color='#ffffff' size='4'><b>{s2}</b></font>"
            else:
                formatted_score_html = f"<font color='#ffffff' size='4'><b>{s1}</b></font> <font color='#94a3b8'>-</font> <font color='#ff4655' size='4'><b>{s2}</b></font>"
        else:
            formatted_score_html = score_text

        score_label = QLabel(formatted_score_html)
        score_label.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent;")
        res_layout.addWidget(score_label, 0, Qt.AlignCenter)

        layout.addWidget(center_container)

        # 3. MVP Badge Section (Fixed position over left fade edge of map artwork)
        is_match_mvp = match.get("is_user_match_mvp", False)
        is_team_mvp = match.get("is_user_team_mvp", False)
        
        right_container = QWidget()
        right_container.setFixedWidth(110)
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(15, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        if is_match_mvp or is_team_mvp:
            mvp_lbl = QLabel("MATCH MVP" if is_match_mvp else "TEAM MVP")
            mvp_color = "#ffd700" if is_match_mvp else "#ffffff"
            mvp_lbl.setStyleSheet(f"font-size: 11px; font-weight: 900; color: {mvp_color}; background: transparent; letter-spacing: 0.5px;")
            
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 220))
            shadow.setOffset(0, 1)
            mvp_lbl.setGraphicsEffect(shadow)
            
            right_layout.addWidget(mvp_lbl)

        layout.addWidget(right_container)
        layout.addStretch(1)

        def on_click(event):
            self.show_match_detail(match)

        card.mousePressEvent = on_click
        return card

    def show_match_detail(self, match):
        for i in reversed(range(self.detail_layout.count())):
            item = self.detail_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.current_detail_match = match
        map_name = match.get("map", "Map")
        mode_name = match.get("mode", "Competitive")
        score_text = match.get("score", "-")
        result = match.get("result", "DRAW")
        if result == "WIN":
            result = "VICTORY"
        elif result == "LOSS":
            result = "DEFEAT"
        t = get_theme()

        self.detail_header_label.setText(f"{map_name} • {mode_name} ({score_text})")

        banner = QWidget()
        if result == "VICTORY":
            banner_style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(14, 85, 95, 0.9), stop:1 rgba(10, 45, 60, 0.9)); border: 1.5px solid #148f77;"
            res_color = "#38ef7d"
        elif result == "DEFEAT":
            banner_style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(95, 25, 45, 0.9), stop:1 rgba(50, 15, 30, 0.9)); border: 1.5px solid #922b21;"
            res_color = "#ff4b2b"
        else:
            banner_style = "background: rgba(60, 70, 80, 0.9); border: 1.5px solid #5d6d7e;"
            res_color = "#aeb6bf"

        banner.setStyleSheet(f"{banner_style} border-radius: 8px; padding: 10px;")
        banner_layout = QHBoxLayout(banner)

        rr_change = match.get("rr_change")
        rr_text = f" <font color='{'#38ef7d' if rr_change and rr_change > 0 else '#ff4b2b'}'>({'+' if rr_change and rr_change > 0 else ''}{rr_change} RR)</font>" if rr_change is not None else ""
        res_lbl = QLabel(f"<font color='{res_color}'><b>{result}</b></font> ({score_text}){rr_text}")
        res_lbl.setStyleSheet("font-size: 17px; border: none; background: transparent;")
        banner_layout.addWidget(res_lbl)
        banner_layout.addStretch()

        meta_lbl = QLabel(f"📍 {map_name}  -  {mode_name}  -  {match.get('date', '')}")
        meta_lbl.setStyleSheet(f"font-size: 13px; color: {t['text_secondary']}; border: none; background: transparent;")
        banner_layout.addWidget(meta_lbl)

        self.detail_layout.addWidget(banner)

        self._render_scoreboard_content()
        self.stacked_widget.setCurrentIndex(1)

    def _set_sort_mode(self, mode_key):
        self.sort_mode = mode_key
        if hasattr(self, 'current_detail_match'):
            self.show_match_detail(self.current_detail_match)

    def _render_scoreboard_content(self):
        match = self.current_detail_match
        players = list(match.get("players", []))

        if self.sort_mode == "acs" or self.sort_mode == "score":
            players.sort(key=lambda p: p.get("acs", p.get("score", 0)), reverse=True)
        elif self.sort_mode == "kda":
            players.sort(key=lambda p: (p.get("kills", 0) + p.get("assists", 0)) / max(1, p.get("deaths", 0)), reverse=True)
        elif self.sort_mode == "econ":
            players.sort(key=lambda p: p.get("econ_rating", 0), reverse=True)
        elif self.sort_mode == "fb":
            players.sort(key=lambda p: p.get("first_bloods", 0), reverse=True)
        elif self.sort_mode == "plants":
            players.sort(key=lambda p: p.get("plants", 0), reverse=True)
        elif self.sort_mode == "defuses":
            players.sort(key=lambda p: p.get("defuses", 0), reverse=True)

        self.detail_layout.addWidget(self._create_team_scoreboard("INDIVIDUALLY SORTED", players, self.theme['accent']))

    def _create_team_scoreboard(self, team_title, players_list, team_color):
        t = get_theme()
        box = QWidget()
        box.setObjectName("TeamScoreboardBox")
        box.setStyleSheet("""
            #TeamScoreboardBox {
                background-color: #0e1722;
                border-radius: 8px;
                border: 1px solid #1f3347;
            }
            #TeamScoreboardBox QLabel {
                border: none;
                background: transparent;
            }
        """)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Header Row
        header_row = QWidget()
        header_row.setObjectName("TeamHeaderRow")
        header_row.setStyleSheet("""
            #TeamHeaderRow {
                background-color: #162838;
                border-radius: 4px;
                border: none;
            }
            #TeamHeaderRow QLabel {
                color: #8fa7bb;
                font-size: 11px;
                font-weight: 800;
                border: none;
                background: transparent;
                padding: 6px 4px;
            }
            #TeamHeaderRow QLabel:hover {
                color: #ffffff;
            }
        """)
        h_layout = QHBoxLayout(header_row)
        h_layout.setContentsMargins(8, 0, 8, 0)
        h_layout.setSpacing(4)

        lbl_player = QLabel("INDIVIDUALLY SORTED")
        lbl_player.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        lbl_acs = QLabel("AVG COMBAT SCORE")
        lbl_acs.setAlignment(Qt.AlignCenter)

        lbl_kda = QLabel("KDA")
        lbl_kda.setAlignment(Qt.AlignCenter)

        lbl_econ = QLabel("ECON RATING")
        lbl_econ.setAlignment(Qt.AlignCenter)

        lbl_fb = QLabel("FIRST BLOODS")
        lbl_fb.setAlignment(Qt.AlignCenter)

        lbl_plants = QLabel("PLANTS")
        lbl_plants.setAlignment(Qt.AlignCenter)

        lbl_defuses = QLabel("DEFUSES")
        lbl_defuses.setAlignment(Qt.AlignCenter)

        # Highlight currently active sort column
        active_sort_style = "background-color: #244563; color: #ffffff; border-radius: 3px;"
        if self.sort_mode in ("acs", "score"):
            lbl_acs.setStyleSheet(active_sort_style)
        elif self.sort_mode == "kda":
            lbl_kda.setStyleSheet(active_sort_style)
        elif self.sort_mode == "econ":
            lbl_econ.setStyleSheet(active_sort_style)
        elif self.sort_mode == "fb":
            lbl_fb.setStyleSheet(active_sort_style)
        elif self.sort_mode == "plants":
            lbl_plants.setStyleSheet(active_sort_style)
        elif self.sort_mode == "defuses":
            lbl_defuses.setStyleSheet(active_sort_style)

        for lbl, mode in [
            (lbl_acs, "acs"), (lbl_kda, "kda"), (lbl_econ, "econ"),
            (lbl_fb, "fb"), (lbl_plants, "plants"), (lbl_defuses, "defuses")
        ]:
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.mousePressEvent = lambda _, m=mode: self._set_sort_mode(m)

        h_layout.addWidget(lbl_player, 5)
        h_layout.addWidget(lbl_acs, 2)
        h_layout.addWidget(lbl_kda, 2)
        h_layout.addWidget(lbl_econ, 2)
        h_layout.addWidget(lbl_fb, 2)
        h_layout.addWidget(lbl_plants, 2)
        h_layout.addWidget(lbl_defuses, 2)

        layout.addWidget(header_row)

        # Identify friendly team and party stacks
        my_team = "blue"
        party_counts = {}
        for p in players_list:
            p_name = p.get("name", "")
            if self.in_game_name and p_name.lower() == self.in_game_name.lower():
                my_team = p.get("team", "blue").lower()
            pid = str(p.get("party_id") or "").strip()
            if pid:
                party_counts[pid] = party_counts.get(pid, 0) + 1

        party_palette = ["#38bdf8", "#fbbf24", "#a855f7", "#ec4899", "#34d399", "#f97316"]
        party_color_map = {}
        party_badge_map = {}
        party_idx = 0
        for pid, cnt in party_counts.items():
            if cnt >= 2:
                party_color_map[pid] = party_palette[party_idx % len(party_palette)]
                party_badge_map[pid] = f"P{party_idx + 1}"
                party_idx += 1

        for p in players_list:
            p_name = p.get("name", "Player")
            p_tag = p.get("tag", "")
            full_tag = f"{p_name} <font color='#a0b2c2' size='2'>#{p_tag}</font>" if p_tag else p_name
            
            is_me = False
            if self.in_game_name and p_name.lower() == self.in_game_name.lower():
                is_me = True
            elif p_name.lower() == self.account_name.lower():
                is_me = True

            p_team = p.get("team", "red").lower()
            is_match_mvp = p.get("is_match_mvp", False)
            is_team_mvp = p.get("is_team_mvp", False)
            p_party = str(p.get("party_id") or "").strip()

            if is_me:
                row_bg = "rgba(140, 112, 54, 0.90)"
                row_border = "1.5px solid #d4af37"
            elif p_team == my_team:
                row_bg = "rgba(14, 110, 98, 0.88)"
                row_border = "1px solid rgba(0, 200, 160, 0.35)"
            else:
                row_bg = "rgba(128, 34, 48, 0.88)"
                row_border = "1px solid rgba(220, 50, 70, 0.35)"

            row = QWidget()
            row.setObjectName("PlayerRow")
            row.setStyleSheet(f"""
                #PlayerRow {{
                    background-color: {row_bg};
                    border: {row_border};
                    border-radius: 6px;
                }}
                #PlayerRow:hover {{
                    border: 1.5px solid #ffffff;
                }}
            """)

            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(6, 4, 8, 4)
            r_layout.setSpacing(4)

            # 1. Player column: Party Badge (if queued in stack) + Agent Icon + Name + MVP Badge
            player_cell = QWidget()
            pc_layout = QHBoxLayout(player_cell)
            pc_layout.setContentsMargins(0, 0, 0, 0)
            pc_layout.setSpacing(6)

            if p_party in party_color_map:
                p_color = party_color_map[p_party]
                p_badge = QLabel(party_badge_map[p_party])
                p_badge.setStyleSheet(f"font-size: 9px; font-weight: 900; color: #111111; background-color: {p_color}; border-radius: 3px; padding: 2px 4px;")
                p_badge.setToolTip(f"Queued in Party Stack ({party_badge_map[p_party]})")
                pc_layout.addWidget(p_badge)

            p_agent_name = p.get('character', 'Agent')
            agent_icon_path = get_asset_path(f"{p_agent_name}.png")
            if not os.path.exists(agent_icon_path) and self.switcher:
                agent_icon_path = str(self.switcher.base_dir / "Agents" / f"{p_agent_name}.png")

            agent_lbl = QLabel()
            agent_lbl.setFixedSize(36, 36)
            agent_lbl.setStyleSheet("border-radius: 3px; background: transparent;")
            if os.path.exists(agent_icon_path):
                agent_lbl.setPixmap(QPixmap(agent_icon_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                agent_lbl.setText("⚔️")
            pc_layout.addWidget(agent_lbl)

            name_box = QWidget()
            name_box_layout = QHBoxLayout(name_box)
            name_box_layout.setContentsMargins(0, 0, 0, 0)
            name_box_layout.setSpacing(6)

            name_lbl = QLabel(f"<b>{full_tag}</b>")
            name_lbl.setStyleSheet("font-size: 13px; color: #ffffff;")
            name_box_layout.addWidget(name_lbl)

            if is_match_mvp:
                mvp_lbl = QLabel("MATCH MVP")
                mvp_lbl.setStyleSheet("font-size: 11px; font-weight: 900; color: #ffd700; background: transparent; letter-spacing: 0.5px;")
                shadow = QGraphicsDropShadowEffect(mvp_lbl)
                shadow.setBlurRadius(8)
                shadow.setColor(QColor(0, 0, 0, 220))
                shadow.setOffset(0, 1)
                mvp_lbl.setGraphicsEffect(shadow)
                name_box_layout.addWidget(mvp_lbl)
            elif is_team_mvp:
                mvp_lbl = QLabel("TEAM MVP")
                mvp_lbl.setStyleSheet("font-size: 11px; font-weight: 900; color: #ffffff; background: transparent; letter-spacing: 0.5px;")
                shadow = QGraphicsDropShadowEffect(mvp_lbl)
                shadow.setBlurRadius(8)
                shadow.setColor(QColor(0, 0, 0, 220))
                shadow.setOffset(0, 1)
                mvp_lbl.setGraphicsEffect(shadow)
                name_box_layout.addWidget(mvp_lbl)

            name_box_layout.addStretch()
            pc_layout.addWidget(name_box)

            r_layout.addWidget(player_cell, 5)

            # 2. AVG COMBAT SCORE
            acs_val = p.get("acs", 0)
            r_acs = QLabel(str(acs_val))
            r_acs.setAlignment(Qt.AlignCenter)
            r_acs.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
            r_layout.addWidget(r_acs, 2)

            # 3. KDA
            k, d, a = p.get("kills", 0), p.get("deaths", 0), p.get("assists", 0)
            r_kda = QLabel(f"{k} <font color='#888888'>/</font> {d} <font color='#888888'>/</font> {a}")
            r_kda.setAlignment(Qt.AlignCenter)
            r_kda.setStyleSheet("font-size: 12px; font-weight: 600; color: #e0d6d1;")
            r_layout.addWidget(r_kda, 2)

            # 4. ECON RATING
            econ_val = p.get("econ_rating", 0)
            r_econ = QLabel(str(econ_val))
            r_econ.setAlignment(Qt.AlignCenter)
            r_econ.setStyleSheet("font-size: 12px; font-weight: 600; color: #e0d6d1;")
            r_layout.addWidget(r_econ, 2)

            # 5. FIRST BLOODS
            fb_val = p.get("first_bloods", 0)
            r_fb = QLabel(str(fb_val))
            r_fb.setAlignment(Qt.AlignCenter)
            r_fb.setStyleSheet("font-size: 12px; font-weight: 600; color: #e0d6d1;")
            r_layout.addWidget(r_fb, 2)

            # 6. PLANTS
            plants_val = p.get("plants", 0)
            r_plants = QLabel(str(plants_val))
            r_plants.setAlignment(Qt.AlignCenter)
            r_plants.setStyleSheet("font-size: 12px; font-weight: 600; color: #e0d6d1;")
            r_layout.addWidget(r_plants, 2)

            # 7. DEFUSES
            defuses_val = p.get("defuses", 0)
            r_defuses = QLabel(str(defuses_val))
            r_defuses.setAlignment(Qt.AlignCenter)
            r_defuses.setStyleSheet("font-size: 12px; font-weight: 600; color: #e0d6d1;")
            r_layout.addWidget(r_defuses, 2)

            layout.addWidget(row)

        return box
