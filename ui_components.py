import sys
import copy
import logging
import os
import threading
import time
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
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath
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


class CrosshairCanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.bg_type = "Dark Grid"
        self.zoom = 1.0
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
        cx = w / 2.0
        cy = h / 2.0

        if self.bg_type == "Light Grid":
            painter.fillRect(0, 0, w, h, QColor("#e8e2de"))
            painter.setPen(QColor("#d4ceca"))
            for x in range(0, w, 20): painter.drawLine(x, 0, x, h)
            for y in range(0, h, 20): painter.drawLine(0, y, w, y)
        else: # Dark Grid (Default)
            painter.fillRect(0, 0, w, h, QColor("#1f1d1e"))
            painter.setPen(QColor("#2d292a"))
            for x in range(0, w, 20): painter.drawLine(x, 0, x, h)
            for y in range(0, h, 20): painter.drawLine(0, y, w, y)

        if not self.profile:
            return

        primary = self.profile.get("primary", {})
        preset_colors = [
            QColor(255, 255, 255), QColor(0, 255, 0), QColor(127, 255, 0),
            QColor(190, 255, 0), QColor(255, 255, 0), QColor(0, 255, 255),
            QColor(255, 0, 255), QColor(255, 0, 0),
        ]

        # Resolution of exact color
        p_col_dict = primary.get("primaryColor")
        if isinstance(p_col_dict, dict) and 'r' in p_col_dict:
            main_color = QColor(
                int(p_col_dict.get('r', 255)),
                int(p_col_dict.get('g', 255)),
                int(p_col_dict.get('b', 255)),
                int(p_col_dict.get('a', 255))
            )
        elif primary.get("bUseCustomColor", False):
            custom_hex = primary.get("customColor", "#00FF88FF")
            main_color = QColor(custom_hex) if isinstance(custom_hex, str) and custom_hex.startswith("#") else QColor(0, 255, 136)
        else:
            color_idx = primary.get("color", 0)
            if isinstance(color_idx, int) and 0 <= color_idx < len(preset_colors):
                main_color = preset_colors[color_idx]
            elif isinstance(color_idx, dict):
                main_color = QColor(color_idx.get('r', 0), color_idx.get('g', 255), color_idx.get('b', 136), color_idx.get('a', 255))
            else:
                main_color = QColor(255, 255, 255)

        scale = self.zoom
        b_outline = primary.get("bOutlineEnabled", True)
        outline_op = float(primary.get("outlineOpacity", 1.0))
        outline_thick = float(primary.get("outlineThickness", 1)) * scale
        outline_color = QColor(0, 0, 0, int(outline_op * 255))

        def draw_rect(x_center, y_center, rect_w, rect_h, color):
            rx = cx + x_center * scale - (rect_w * scale) / 2.0
            ry = cy + y_center * scale - (rect_h * scale) / 2.0
            rw = rect_w * scale
            rh = rect_h * scale

            if b_outline and outline_thick > 0:
                out_x = rx - outline_thick
                out_y = ry - outline_thick
                out_w = rw + outline_thick * 2
                out_h = rh + outline_thick * 2
                painter.fillRect(QRectF(out_x, out_y, out_w, out_h), outline_color)

            painter.fillRect(QRectF(rx, ry, rw, rh), color)

        # 1. Outer Lines (Strict Boolean Check)
        outer = primary.get("outerLines", {})
        o_len = float(outer.get("lineLength", 0))
        o_op = float(outer.get("lineOpacity", 1.0))
        is_outer_enabled = outer.get("bDisplayOuterLines", outer.get("bbDisplayOuterLines", False))
        if is_outer_enabled and o_len > 0 and o_op > 0:
            o_thick = float(outer.get("lineThickness", 2))
            o_off = float(outer.get("lineOffset", 10))
            show_top = outer.get("bShowTopLine", True)
            line_col = QColor(main_color.red(), main_color.green(), main_color.blue(), int(o_op * 255))

            draw_rect(-(o_off + o_len / 2.0), 0, o_len, o_thick, line_col)
            draw_rect((o_off + o_len / 2.0), 0, o_len, o_thick, line_col)
            draw_rect(0, (o_off + o_len / 2.0), o_thick, o_len, line_col)
            if show_top: draw_rect(0, -(o_off + o_len / 2.0), o_thick, o_len, line_col)

        # 2. Inner Lines
        inner = primary.get("innerLines", {})
        i_len = float(inner.get("lineLength", 0))
        i_op = float(inner.get("lineOpacity", 1.0))
        is_inner_enabled = inner.get("bDisplayInnerLines", inner.get("bbDisplayInnerLines", True))
        if is_inner_enabled and i_len > 0 and i_op > 0:
            i_thick = float(inner.get("lineThickness", 2))
            i_off = float(inner.get("lineOffset", 3))
            show_top = inner.get("bShowTopLine", True)
            line_col = QColor(main_color.red(), main_color.green(), main_color.blue(), int(i_op * 255))

            draw_rect(-(i_off + i_len / 2.0), 0, i_len, i_thick, line_col)
            draw_rect((i_off + i_len / 2.0), 0, i_len, i_thick, line_col)
            draw_rect(0, (i_off + i_len / 2.0), i_thick, i_len, line_col)
            if show_top: draw_rect(0, -(i_off + i_len / 2.0), i_thick, i_len, line_col)

        # 3. Center Dot (Rendered as Anti-Aliased Circle)
        if primary.get("bDisplayCenterDot", False):
            dot_op = float(primary.get("centerDotOpacity", 1.0))
            dot_size = float(primary.get("centerDotSize", 2))
            dot_col = QColor(main_color.red(), main_color.green(), main_color.blue(), int(dot_op * 255))

            painter.setRenderHint(QPainter.Antialiasing, True)
            rx = cx - (dot_size * scale) / 2.0
            ry = cy - (dot_size * scale) / 2.0
            rw = dot_size * scale
            rh = dot_size * scale

            if b_outline and outline_thick > 0:
                out_x = rx - outline_thick
                out_y = ry - outline_thick
                out_w = rw + outline_thick * 2
                out_h = rh + outline_thick * 2
                painter.setBrush(outline_color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QRectF(out_x, out_y, out_w, out_h))

            painter.setBrush(dot_col)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(rx, ry, rw, rh))
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
                    "bDisplayInnerLines": True,
                    "lineOpacity": 1.0,
                    "lineLength": 6,
                    "lineThickness": 2,
                    "lineOffset": 3,
                    "bShowTopLine": True
                },
                "outerLines": {
                    "bDisplayOuterLines": False,
                    "lineOpacity": 0.35,
                    "lineLength": 2,
                    "lineThickness": 2,
                    "lineOffset": 10,
                    "bShowTopLine": True
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
            elif (t == "h" or t == "0h") and i + 1 < len(tokens):
                inner["bDisplayInnerLines"] = (tokens[i+1] == "1")
                i += 1
            elif t == "0t" and i + 1 < len(tokens):
                try: inner["lineThickness"] = int(tokens[i+1])
                except: pass
                inner["bDisplayInnerLines"] = True
                i += 1
            elif t == "0l" and i + 1 < len(tokens):
                try: inner["lineLength"] = int(tokens[i+1])
                except: pass
                inner["bDisplayInnerLines"] = True
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
            elif t == "1h" and i + 1 < len(tokens):
                outer["bDisplayOuterLines"] = (tokens[i+1] == "1")
                i += 1
            elif t == "1b" and i + 1 < len(tokens):
                # 1b in Valorant is Outer Line Outline Enabled, outer lines active!
                outer["bDisplayOuterLines"] = True
                i += 1
            elif t == "1t" and i + 1 < len(tokens):
                try: outer["lineThickness"] = int(tokens[i+1])
                except: pass
                outer["bDisplayOuterLines"] = True
                i += 1
            elif t == "1l" and i + 1 < len(tokens):
                try: outer["lineLength"] = int(tokens[i+1])
                except: pass
                outer["bDisplayOuterLines"] = True
                i += 1
            elif t == "1o" and i + 1 < len(tokens):
                try: outer["lineOffset"] = int(tokens[i+1])
                except: pass
                outer["bDisplayOuterLines"] = True
                i += 1
            elif t == "1a" and i + 1 < len(tokens):
                try: outer["lineOpacity"] = float(tokens[i+1])
                except: pass
                outer["bDisplayOuterLines"] = True
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
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #4f4a4b;
                height: 10px;
                background: #4a4647;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #c89f68;
                border: 2px solid #2c2a2b;
                width: 18px;
                height: 18px;
                margin: -6px 0; 
                border-radius: 9px;
            }
            QSlider::add-page:horizontal {
                background: #4a4647;
            }
            QSlider::sub-page:horizontal {
                background: #c89f68;
                border-radius: 5px;
            }
        """)

        self.spin_box = QDoubleSpinBox() # Use QDoubleSpinBox for float values
        self.spin_box.setRange(min_val, max_val)
        self.spin_box.setSingleStep(step)
        self.spin_box.setDecimals(1) # Display one decimal place
        self.spin_box.setFixedWidth(60)
        self.spin_box.setAlignment(Qt.AlignCenter)
        self.spin_box.setStyleSheet("""
            QDoubleSpinBox { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 5px; color: #e0d6d1; font-weight: bold; }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0px; border: none; background: transparent; }
        """)

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
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignRight)
        
        self.btn_true = QPushButton(text_true)
        self.btn_false = QPushButton(text_false)
        
        self.btn_true.setCheckable(True)
        self.btn_false.setCheckable(True)

        self.btn_true.clicked.connect(lambda: self.set_state(True))
        self.btn_false.clicked.connect(lambda: self.set_state(False))

        common_style = """
            QPushButton { 
                background-color: #4f4a4b; color: #e0d6d1; 
                font-weight: bold; border-radius: 8px; padding: 8px; min-width: 100px; border: 1px solid #3a3637;
            }
            QPushButton:hover {
                border: 1px solid #c89f68;
            }
            QPushButton:pressed {
                background-color: #5a5556;
            }
            QPushButton:checked {
                background-color: #c89f68; color: #2c2a2b; border: 1px solid #d9b68b;
            }
        """
        self.btn_true.setStyleSheet(common_style)
        self.btn_false.setStyleSheet(common_style)
        
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
        self.main_widget.setStyleSheet("#popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #c89f68; } QLabel { color: #FFFFFF; }")
        
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
        scroll_area.setStyleSheet("background-color: #3a3637; border: 1px solid #4f4a4b; border-radius: 10px;")

        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: #3a3637;")
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
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a4647;
                    border: 2px solid #4f4a4b;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #5a5556;
                    border-color: #c89f68;
                }
            """)
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

        self.setMinimumWidth(750)
        default_settings = default_settings or {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container_widget = QWidget(objectName="container")
        container_widget.setStyleSheet("""
            #container {
                background-color: #2c2a2b; 
                border: 1px solid #c89f68;
                border-radius: 15px;
            }
            QLabel { color: white; font-weight: bold; background: transparent; }
            QLineEdit, QListWidget { 
                background-color: #4a4647; 
                border: 1px solid #c89f68; 
                border-radius: 8px; 
                padding: 10px; 
                color: #e0d6d1; 
            }
            QPushButton { 
                background-color: #c89f68; 
                color: #2c2a2b; 
                font-weight: bold; 
                border-radius: 15px; 
                padding: 8px; 
                border: none;
            }
            QPushButton:hover { background-color: #d9b68b; }

            QScrollBar:vertical {
                border: none;
                background-color: #2c2a2b;
                width: 14px;
                margin: 0px 0 0px 0;
                border-radius: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #e0d6d1;
                min-height: 30px;
                border-radius: 7px;
                border: 1px solid #c89f68;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #c89f68;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
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
        left_layout.setSpacing(15)
        top_layout.addLayout(left_layout, 5)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        top_layout.addLayout(right_layout, 4)

        self.accounts_data = accounts_data
        self.menu_icon_path = default_settings.get("menu_icon_path", "")
        if not self.menu_icon_path:
            base_dir = parent.switcher.base_dir if (parent and hasattr(parent, 'switcher')) else Path(__file__).parent
            default_icon = Path(base_dir) / "Assets" / "valorant" / "5.png"
            if default_icon.exists():
                self.menu_icon_path = str(default_icon)
        
        left_layout.addWidget(QLabel("Menu Title:"))
        self.title_edit = QLineEdit(default_settings.get("title", "Valorant"))
        left_layout.addWidget(self.title_edit)
        
        left_layout.addWidget(QLabel("Menu Icon:"))
        icon_layout = QHBoxLayout()
        icon_layout.setSpacing(8)
        self.icon_path_edit = QLineEdit(self.menu_icon_path)
        self.icon_path_edit.setPlaceholderText("Optional: Select an icon for the main menu")
        self.icon_path_edit.textChanged.connect(self.update_icon_preview)

        self.icon_preview_btn = QPushButton()
        self.icon_preview_btn.setFixedSize(40, 40)
        self.icon_preview_btn.setIconSize(QSize(28, 28))
        self.icon_preview_btn.setToolTip("Click to choose a Valorant menu icon style")
        self.icon_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #d9b68b; }
        """)
        self.icon_preview_btn.clicked.connect(self.open_valorant_icon_picker)

        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold;
                border-radius: 8px; padding: 10px; border: none;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        browse_button.clicked.connect(self.select_icon)

        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(self.icon_preview_btn)
        icon_layout.addWidget(browse_button)
        left_layout.addLayout(icon_layout)
        self.update_icon_preview(self.menu_icon_path)
        
        settings_group = QGroupBox("iMA Menu Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF; font-weight: bold; border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }
        """)
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
        
        left_layout.addWidget(settings_group)
        left_layout.addStretch()
        
        right_layout.addWidget(QLabel("Arrange Accounts (Drag & Drop):"))
        self.accounts_list = QListWidget()
        self.accounts_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.accounts_list.setIconSize(QSize(32, 32))
        self.accounts_list.setStyleSheet("""
            QListWidget {
                background-color: #3a3637;
                border: 1px solid #c89f68;
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }
            QListWidget::item {
                background-color: #4f4a4b;
                color: #e0d6d1;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;
                padding: 8px 12px;
                margin-bottom: 4px;
                border: 2px dashed transparent;
            }
            QListWidget::item:hover {
                background-color: #5a5556;
                border: 2px dashed #c89f68;
            }
            QListWidget::item:selected {
                background-color: #c89f68;
                color: #2c2a2b;
                border: 2px solid #d9b68b;
            }
            QListWidget::drop-indicator {
                border: 2px dashed #c89f68;
                border-radius: 8px;
                background-color: rgba(200, 159, 104, 0.25);
            }
        """)
        self.populate_accounts(default_settings.get("ordered_accounts"))
        right_layout.addWidget(self.accounts_list)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        export_button = QPushButton("Export")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        export_button.clicked.connect(self.accept)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
        content_layout.addLayout(button_layout)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.center() - self.rect().center())

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
            "ordered_accounts": [self.accounts_list.item(i).text() for i in range(self.accounts_list.count())],
            "show_rank_tips": self.show_rank_tips_toggle.get_state(),
            "show_rr_in_tip": self.show_rr_in_tip_toggle.get_state(),
            "tip_delay": self.tip_delay_slider.value()
        }

class PopupDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        
        self.main_widget = QWidget(objectName="popup_widget")
        self.main_widget.setStyleSheet("#popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #c89f68; } QLabel { color: #FFFFFF; }")
        
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

class CustomMessageDialog(PopupDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, parent)
        self.setFixedSize(350, 180)
        
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)
        
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

class InputDialog(PopupDialog):
    def __init__(self, title, prompt, default_text="", in_game_name_default="", in_game_tag_default="", parent=None):
        super().__init__(title, parent)
        
        self.in_game_name_edit = None
        self.in_game_tag_edit = None

        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet("color: #e0d6d1;")
        self.content_layout.addWidget(prompt_label)
        
        self.input_field = QLineEdit(default_text)
        self.input_field.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.input_field)

        if in_game_name_default is not None or in_game_tag_default is not None:
            self.content_layout.addWidget(QLabel("In-game Name and Tag (optional):"))
            in_game_name_tag_layout = QHBoxLayout()
            in_game_name_tag_layout.setContentsMargins(0,0,0,0)
            in_game_name_tag_layout.setSpacing(5)

            self.in_game_name_edit = QLineEdit(in_game_name_default)
            self.in_game_name_edit.setPlaceholderText("In-game Name")
            self.in_game_name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
            in_game_name_tag_layout.addWidget(self.in_game_name_edit)
            
            in_game_name_tag_layout.addWidget(QLabel("#"))

            self.in_game_tag_edit = QLineEdit(in_game_tag_default)
            self.in_game_tag_edit.setPlaceholderText("Tag")
            self.in_game_tag_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
            in_game_name_tag_layout.addWidget(self.in_game_tag_edit)
            self.content_layout.addLayout(in_game_name_tag_layout)
            self.setFixedSize(350, 250) # Adjust size for two inputs
        else:
            self.setFixedSize(350, 180) # Original size for one input
        
        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
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
        self.setFixedSize(380, 300)
        self.switcher_instance = switcher_instance

        name_label = QLabel("Enter a name for the current account:")
        name_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        name_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.name_edit)

        self.content_layout.addWidget(QLabel("Enter in-game name and tag (optional):"))
        in_game_name_tag_layout = QHBoxLayout()
        in_game_name_tag_layout.setContentsMargins(0,0,0,0)
        in_game_name_tag_layout.setSpacing(5)

        self.in_game_name_edit = QLineEdit()
        self.in_game_name_edit.setPlaceholderText("In-game Name")
        self.in_game_name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        in_game_name_tag_layout.addWidget(self.in_game_name_edit)
        
        in_game_name_tag_layout.addWidget(QLabel("#"))

        self.in_game_tag_edit = QLineEdit()
        self.in_game_tag_edit.setPlaceholderText("Tag")
        self.in_game_tag_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        in_game_name_tag_layout.addWidget(self.in_game_tag_edit)
        self.content_layout.addLayout(in_game_name_tag_layout)

        self.puuid_edit = QLineEdit()
        self.puuid_edit.setPlaceholderText("PUUID (optional)")
        self.puuid_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.puuid_edit)

        self.content_layout.addWidget(QLabel("Select Game:"))
        self.game_combo = QComboBox()
        self.game_combo.setStyleSheet("""
            QComboBox { 
                background-color: #4a4647; 
                border: 1px solid #c89f68; 
                border-radius: 8px; 
                padding: 8px; 
                color: #e0d6d1; 
                font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; /* Can add a custom arrow icon here */ }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; 
                border: 1px solid #c89f68; 
                selection-background-color: #c89f68;
                color: #e0d6d1;
                selection-color: #2c2a2b;
                padding: 5px;
            }
        """)
        
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
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
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
        backup_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b;
            }
        """)
        backup_button.setIcon(QIcon(get_asset_path("Backup.png")))
        backup_button.setIconSize(QSize(24, 24))
        backup_button.clicked.connect(lambda: self._set_selection_and_accept("backup"))
        self.content_layout.addWidget(backup_button)

        restore_button = QPushButton("Restore")
        restore_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b;
            }
        """)
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
        local_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b;
            }
        """)
        local_button.setIcon(QIcon(get_asset_path("Local.png")))
        local_button.setIconSize(QSize(24, 24))
        local_button.clicked.connect(lambda: self.set_selection("local"))
        self.content_layout.addWidget(local_button)

        google_drive_button = QPushButton("Google Drive")
        google_drive_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 15px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b;
            }
        """)
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
        self.main_widget.setStyleSheet("""
            #settings_dropdown_widget {
                background-color: #2c2a2b;
                border-radius: 15px;
                border: 1px solid #4f4a4b;
            }
            QPushButton {
                background-color: #4f4a4b;
                color: #e0d6d1;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #c89f68;
                color: #2c2a2b;
            }
        """)

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
        add_icon = Path(get_asset_path("Add.png"))
        if add_icon.exists():
            add_btn.setIcon(QIcon(str(add_icon)))
            add_btn.setIconSize(QSize(16, 16))
        add_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.add_account))
        row1.addWidget(add_btn)

        save_btn = QPushButton(" Save")
        save_icon = Path(get_asset_path("Save.png"))
        if save_icon.exists():
            save_btn.setIcon(QIcon(str(save_icon)))
            save_btn.setIconSize(QSize(16, 16))
        save_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.save_current_account))
        row1.addWidget(save_btn)

        main_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        backup_btn = QPushButton(" Backup")
        backup_icon = Path(get_asset_path("Backup.png"))
        if backup_icon.exists():
            backup_btn.setIcon(QIcon(str(backup_icon)))
            backup_btn.setIconSize(QSize(16, 16))
        backup_btn.clicked.connect(lambda: self.execute_action(self.actions_handler._handle_backup_selection))
        row2.addWidget(backup_btn)

        restore_btn = QPushButton(" Restore")
        restore_icon = Path(get_asset_path("Restore.png"))
        if restore_icon.exists():
            restore_btn.setIcon(QIcon(str(restore_icon)))
            restore_btn.setIconSize(QSize(16, 16))
        restore_btn.clicked.connect(lambda: self.execute_action(self.actions_handler._handle_restore_selection))
        row2.addWidget(restore_btn)

        main_layout.addLayout(row2)

        ima_btn = QPushButton(" iMA Menu")
        ima_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b;
                color: #e0d6d1;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding: 8px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #c89f68;
                color: #2c2a2b;
            }
        """)
        ima_icon = Path(get_asset_path("ima.png"))
        if ima_icon.exists():
            ima_btn.setIcon(QIcon(str(ima_icon)))
            ima_btn.setIconSize(QSize(18, 18))
        ima_btn.clicked.connect(lambda: self.execute_action(self.actions_handler.export_ima_menu))
        main_layout.addWidget(ima_btn)

        options_btn = QPushButton(" Options")
        options_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b;
                color: #e0d6d1;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding: 8px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #c89f68;
                color: #2c2a2b;
            }
        """)
        options_icon = Path(get_asset_path("Options.png"))
        if options_icon.exists():
            options_btn.setIcon(QIcon(str(options_icon)))
            options_btn.setIconSize(QSize(18, 18))
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
        self.setFixedSize(760, 680)

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

        self.main_widget.setStyleSheet("""
            #popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #4f4a4b; }
            QLabel { color: #e0d6d1; font-weight: normal; }
            QGroupBox {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #c89f68;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 10px;
                color: #FFFFFF;
            }
        """)

        self.content_layout.setSpacing(10)
        
        # Horizontal Body Layout: Sidebar + Stack
        body_layout = QHBoxLayout()
        body_layout.setSpacing(15)

        # Left Sidebar Navigation List
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(170)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #232122;
                border: 1px solid #4f4a4b;
                border-radius: 10px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                color: #e0d6d1;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #3a3637;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #c89f68;
                color: #2c2a2b;
            }
        """)
        body_layout.addWidget(self.nav_list)

        # Right Pages Stack
        self.pages_widget = QStackedWidget()
        self.pages_widget.setStyleSheet("""
            QStackedWidget {
                background-color: #343031;
                border: 1px solid #4f4a4b;
                border-radius: 10px;
            }
        """)
        body_layout.addWidget(self.pages_widget)

        self.content_layout.addLayout(body_layout)

        # Setup pages
        self.setup_ui_tab()          # Page 0: Display
        self.setup_account_tab()     # Page 1: Rank & Account
        self.setup_graphics_tab()    # Page 2: Graphics
        self.setup_audio_tab()       # Page 3: Audio
        self.setup_advanced_tab()    # Page 4: Quality Presets & Riot Client
        self.setup_crosshairs_tab()  # Page 5: Crosshair Manager
        self.setup_updates_tab()     # Page 6: Software Updates

        self.nav_list.currentRowChanged.connect(self.pages_widget.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e0d6d1; font-size: 12px; padding-top: 5px;")
        self.content_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        apply_button = QPushButton("Apply")
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b;
            }
        """)
        apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

        self.populate_account_combos()
        self.load_current_settings()

    def add_page(self, title, icon_file, widget):
        item = QListWidgetItem(title)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
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

        preview_splash_btn = QPushButton("Preview Splash")
        preview_splash_btn.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold;
                border-radius: 8px; padding: 10px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #d9b68b; }
            QPushButton:pressed { background-color: #b88f58; }
        """)
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
        
        combo_style = """
            QComboBox { 
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1; font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; border: 1px solid #c89f68; selection-background-color: #c89f68; color: #e0d6d1; selection-color: #2c2a2b; padding: 5px;
            }
        """

        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["Default", "Fullscreen", "Windowed Fullscreen", "Windowed"])
        self.display_mode_combo.setStyleSheet(combo_style)
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
            
            combo_box.setStyleSheet(combo_style)
            self.riot_combo_boxes[key] = combo_box
            form_layout.addRow(QLabel(self.riot_quality_settings_map[key] + ":"), combo_box)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        self.add_page("Graphics", "Graphics.png", graphics_tab)

    def setup_audio_tab(self):
        audio_tab = QWidget()
        main_layout = QVBoxLayout(audio_tab)
        main_layout.setContentsMargins(15, 5, 15, 15)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        general_group = QGroupBox("General Volume")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(10)
        general_keys = ["EAresFloatSettingName::OverallVolume", "EAresFloatSettingName::SoundEffectsVolume", "EAresFloatSettingName::VoiceOverVolume", "EAresFloatSettingName::VideoVolume"]
        for key in general_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            general_layout.addRow(QLabel(self.audio_settings_map[key] + ":"), slider)
        main_layout.addWidget(general_group)

        music_group = QGroupBox("Music")
        music_layout = QFormLayout(music_group)
        music_layout.setSpacing(10)
        music_keys = ["EAresFloatSettingName::AllMusicOverallVolume", "EAresFloatSettingName::MenuAndLobbyMusicVolume", "EAresFloatSettingName::CharacterSelectMusicVolume"]
        for key in music_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            music_layout.addRow(QLabel(self.audio_settings_map[key] + ":"), slider)
        main_layout.addWidget(music_group)
        
        voice_group = QGroupBox("Voice & Communication")
        voice_layout = QFormLayout(voice_group)
        voice_layout.setSpacing(10)
        voice_keys = ["EAresIntSettingName::MicVolume", "EAresIntSettingName::VoiceVolume"]
        for key in voice_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            voice_layout.addRow(QLabel(self.audio_settings_map[key] + ":"), slider)
        
        self.audio_controls["EAresBoolSettingName::PushToTalkEnabled"] = RadioButtonGroup("Push to Talk", "Automatic")
        voice_layout.addRow(QLabel(self.audio_settings_map["EAresBoolSettingName::PushToTalkEnabled"] + ":"), self.audio_controls["EAresBoolSettingName::PushToTalkEnabled"])
        
        self.audio_controls["EAresBoolSettingName::EnableHRTF"] = RadioButtonGroup("On", "Off")
        voice_layout.addRow(QLabel(self.audio_settings_map["EAresBoolSettingName::EnableHRTF"] + ":"), self.audio_controls["EAresBoolSettingName::EnableHRTF"])
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
        default_button = QPushButton("Default (High)")
        
        preset_style = """
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 8px; border: 1px solid #c89f68;
            }
            QPushButton:hover { background-color: #d9b68b; }
            QPushButton:pressed { background-color: #b88f58; }
        """
        recommended_button.setStyleSheet(preset_style)
        default_button.setStyleSheet(preset_style)
        
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
            spin_box.setStyleSheet("QSpinBox { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 5px; color: #e0d6d1; }")
            spin_box.setFixedWidth(60)
            self.spin_boxes[key] = spin_box
            grid_layout.addWidget(spin_box, row, col + 1, Qt.AlignLeft)

        layout.addLayout(grid_layout)

        riot_client_group = QGroupBox("Riot Client Behavior")
        riot_client_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF; font-size: 13px; font-weight: bold;
                border: 1px solid #c89f68; border-radius: 8px; margin-top: 10px;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; color: #FFFFFF; }
        """)
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
        top_group.setStyleSheet(group_style)
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

        bottom_group = QGroupBox("Layout Settings")
        bottom_group.setStyleSheet(group_style)
        bottom_layout = QGridLayout(bottom_group)
        bottom_layout.setSpacing(10)

        bottom_layout.addWidget(QLabel("Grid Size (Columns):"), 0, 0)
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        self.grid_size_combo.setStyleSheet("""
            QComboBox { 
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1; font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; border: 1px solid #c89f68; selection-background-color: #c89f68; color: #e0d6d1; selection-color: #2c2a2b; padding: 5px;
            }
        """)
        bottom_layout.addWidget(self.grid_size_combo, 0, 1)

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
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 6px; padding: 4px 8px; color: #e0d6d1; font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; border: 1px solid #c89f68; selection-background-color: #c89f68; color: #e0d6d1; selection-color: #2c2a2b; padding: 4px;
            }
        """
        btn_style = """
            QPushButton {
                background-color: #4a4647; color: #e0d6d1; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: 1px solid #6b6365;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #c89f68; }
            QPushButton:pressed { background-color: #3a3637; }
        """
        gold_btn_style = """
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; font-size: 11px;
                border-radius: 6px; padding: 6px 12px; border: none;
            }
            QPushButton:hover { background-color: #d9b68b; }
            QPushButton:pressed { background-color: #b88f58; }
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




        layout.addLayout(top_bar)

        main_split = QHBoxLayout()
        main_split.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        self.ch_canvas = CrosshairCanvasWidget()
        left_col.addWidget(self.ch_canvas, 0, Qt.AlignCenter)

        bg_bar = QHBoxLayout()
        bg_bar.setSpacing(6)
        bg_bar.addWidget(QLabel("BG:"))
        self.ch_bg_combo = QComboBox()
        self.ch_bg_combo.setStyleSheet(combo_style)
        self.ch_bg_combo.addItems(["Dark Grid", "Light Grid"])
        bg_bar.addWidget(self.ch_bg_combo)

        bg_bar.addWidget(QLabel("Zoom:"))
        self.ch_zoom_combo = QComboBox()
        self.ch_zoom_combo.setStyleSheet(combo_style)
        self.ch_zoom_combo.addItems(["1x", "2x"])
        bg_bar.addWidget(self.ch_zoom_combo)
        left_col.addLayout(bg_bar)
        left_col.addStretch()

        main_split.addLayout(left_col, 0)

        self.ch_controls_tab = QTabWidget()
        self.ch_controls_tab.setUsesScrollButtons(False)
        self.ch_controls_tab.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #4f4a4b; border-radius: 6px; background-color: #2c2a2b; }
            QTabBar::tab { 
                background: #3a3637; color: #b0a6a0; padding: 4px 6px; 
                border-top-left-radius: 4px; border-top-right-radius: 4px; 
                font-size: 10px; font-weight: bold; min-width: 50px;
            }
            QTabBar::tab:selected { background: #c89f68; color: #2c2a2b; }
        """)

        # Tab 1: Primary & Color
        tab_color = QWidget()
        layout_color = QFormLayout(tab_color)
        layout_color.setSpacing(6)
        
        self.ch_color_combo = QComboBox()
        self.ch_color_combo.setStyleSheet(combo_style)
        self.ch_color_combo.addItems(["White", "Green", "Yellow Green", "Green Yellow", "Yellow", "Cyan", "Pink", "Red", "Custom Hex"])
        layout_color.addRow(QLabel("Color Preset:"), self.ch_color_combo)

        self.ch_custom_hex_edit = QLineEdit("#00FF88FF")
        self.ch_custom_hex_edit.setStyleSheet("QLineEdit { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 4px; padding: 4px; color: #e0d6d1; }")
        layout_color.addRow(QLabel("Custom Hex:"), self.ch_custom_hex_edit)

        self.ch_dot_enable_cb = QCheckBox("Enable Center Dot")
        self.ch_dot_enable_cb.setStyleSheet("color: #e0d6d1; font-weight: bold;")
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
        self.ch_outline_enable_cb.setStyleSheet("color: #e0d6d1; font-weight: bold;")
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
        self.ch_inner_enable_cb.setStyleSheet("color: #e0d6d1; font-weight: bold;")
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
        self.ch_inner_top_cb.setStyleSheet("color: #e0d6d1;")
        layout_inner.addRow(self.ch_inner_top_cb)

        self.ch_controls_tab.addTab(tab_inner, "Inner")

        # Tab 4: Outer Lines
        tab_outer = QWidget()
        layout_outer = QFormLayout(tab_outer)
        layout_outer.setSpacing(5)

        self.ch_outer_enable_cb = QCheckBox("Show Outer Lines")
        self.ch_outer_enable_cb.setStyleSheet("color: #e0d6d1; font-weight: bold;")
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
        self.ch_outer_top_cb.setStyleSheet("color: #e0d6d1;")
        layout_outer.addRow(self.ch_outer_top_cb)

        self.ch_controls_tab.addTab(tab_outer, "Outer")

        main_split.addWidget(self.ch_controls_tab, 1)
        layout.addLayout(main_split)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        btn_import = QPushButton("Import Code")
        btn_import.setStyleSheet(btn_style)
        btn_import.clicked.connect(self.on_import_crosshair_code)
        action_bar.addWidget(btn_import)

        btn_export = QPushButton("Copy Code")
        btn_export.setStyleSheet(btn_style)
        btn_export.clicked.connect(self.on_export_crosshair_code)
        action_bar.addWidget(btn_export)



        layout.addLayout(action_bar)

        self.ch_bg_combo.currentIndexChanged.connect(lambda: self.ch_canvas.set_bg(self.ch_bg_combo.currentText()))
        self.ch_zoom_combo.currentIndexChanged.connect(lambda: self.ch_canvas.set_zoom(2.0 if "2" in self.ch_zoom_combo.currentText() else 1.0))

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
        group_box.setStyleSheet(group_style)
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(15, 20, 15, 15)

        from game_switcher import APP_VERSION
        version_label = QLabel(f"<b>Current Version:</b> v{APP_VERSION}")
        version_label.setStyleSheet("font-size: 14px; color: #e0d6d1;")
        group_layout.addWidget(version_label)

        check_btn = QPushButton("Check for Updates")
        check_btn.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold;
                border-radius: 8px; padding: 10px 20px; font-size: 13px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        self.update_check_btn = check_btn
        check_btn.clicked.connect(lambda: self.open_update_dialog(source_button=self.update_check_btn))
        group_layout.addWidget(check_btn)

        main_layout.addWidget(group_box)

        changelog_box = QGroupBox("Changelog", updates_tab)
        changelog_box.setStyleSheet(group_style)
        changelog_layout = QVBoxLayout(changelog_box)
        changelog_layout.setSpacing(10)
        changelog_layout.setContentsMargins(15, 20, 15, 15)

        changelog_edit = QTextEdit()
        changelog_edit.setReadOnly(True)
        changelog_edit.setStyleSheet("""
            QTextEdit {
                background-color: #242223;
                color: #e0d6d1;
                border: 1px solid #4f4a4b;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        
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

        p_col_dict = primary.get("primaryColor")
        if isinstance(p_col_dict, dict) and 'r' in p_col_dict:
            r, g, b = int(p_col_dict.get('r', 255)), int(p_col_dict.get('g', 255)), int(p_col_dict.get('b', 255))
            if r == 255 and g == 255 and b == 255: self.ch_color_combo.setCurrentIndex(0)
            elif r == 0 and g == 255 and b == 0: self.ch_color_combo.setCurrentIndex(1)
            elif r == 127 and g == 255 and b == 0: self.ch_color_combo.setCurrentIndex(2)
            elif r == 190 and g == 255 and b == 0: self.ch_color_combo.setCurrentIndex(3)
            elif r == 255 and g == 255 and b == 0: self.ch_color_combo.setCurrentIndex(4)
            elif r == 0 and g == 255 and b == 255: self.ch_color_combo.setCurrentIndex(5)
            elif r == 255 and g == 0 and b == 255: self.ch_color_combo.setCurrentIndex(6)
            elif r == 255 and g == 0 and b == 0: self.ch_color_combo.setCurrentIndex(7)
            else:
                self.ch_color_combo.setCurrentIndex(8)
                self.ch_custom_hex_edit.setText(f"#{r:02X}{g:02X}{b:02X}FF")
        elif primary.get('bUseCustomColor', False):
            self.ch_color_combo.setCurrentIndex(8)
            custom_hex = primary.get('customColor', '#00FF88FF')
            if isinstance(custom_hex, str): self.ch_custom_hex_edit.setText(custom_hex)
        else:
            color_idx = primary.get('color', 0)
            if isinstance(color_idx, int) and 0 <= color_idx <= 7:
                self.ch_color_combo.setCurrentIndex(color_idx)
            else:
                self.ch_color_combo.setCurrentIndex(0)

        self.ch_dot_enable_cb.setChecked(primary.get('bDisplayCenterDot', False))
        self.ch_dot_opacity_slider.setValue(int(float(primary.get('centerDotOpacity', 1.0)) * 100))
        self.ch_dot_size_slider.setValue(int(primary.get('centerDotSize', 2)))

        self.ch_outline_enable_cb.setChecked(primary.get('bOutlineEnabled', True))
        self.ch_outline_opacity_slider.setValue(int(float(primary.get('outlineOpacity', 1.0)) * 100))
        self.ch_outline_thick_slider.setValue(int(primary.get('outlineThickness', 1)))

        self.ch_inner_enable_cb.setChecked(inner.get('bbDisplayInnerLines', inner.get('bDisplayInnerLines', True)))
        self.ch_inner_opacity_slider.setValue(int(float(inner.get('lineOpacity', 1.0)) * 100))
        self.ch_inner_len_slider.setValue(int(inner.get('lineLength', 6)))
        self.ch_inner_thick_slider.setValue(int(inner.get('lineThickness', 2)))
        self.ch_inner_off_slider.setValue(int(inner.get('lineOffset', 3)))
        self.ch_inner_top_cb.setChecked(inner.get('bShowTopLine', True))

        self.ch_outer_enable_cb.setChecked(outer.get('bbDisplayOuterLines', outer.get('bDisplayOuterLines', False)))
        self.ch_outer_opacity_slider.setValue(int(float(outer.get('lineOpacity', 0.35)) * 100))
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
            "rank_check_region": self.rank_check_region_combo.currentData() if hasattr(self, 'rank_check_region_combo') else "eu",
            "auto_rank_update": self.auto_rank_update_toggle.get_state() if hasattr(self, 'auto_rank_update_toggle') else True,
            "grid_size": int(self.grid_size_combo.currentText()) if hasattr(self, 'grid_size_combo') else 4,
            "show_splash_notification": self.show_splash_notification_toggle.get_state() if hasattr(self, 'show_splash_notification_toggle') else True,
            "show_riot_client": self.show_riot_client_toggle.get_state() if hasattr(self, 'show_riot_client_toggle') else False,
            "unified_settings_enabled": self.unified_enabled_toggle.get_state() if hasattr(self, 'unified_enabled_toggle') else False,
            "master_account": self.master_account_combo.currentText() if hasattr(self, 'master_account_combo') else "",
            "sync_keybinds": self.sync_keybinds_toggle.get_state() if hasattr(self, 'sync_keybinds_toggle') else False,
        }

        settings_to_save = {
            "display_mode": self.display_mode_combo.currentText(),
            "quality": quality_settings,
            "riot_settings": riot_settings_to_save,
            "audio_settings": audio_settings_to_save,
            "ui_settings": ui_settings_to_save
        }
        self.switcher.save_graphics_settings(settings_to_save)
        success, message = self.switcher.update_all_game_user_settings(settings_to_save)
        self.switcher.update_ima_menu_if_enabled('update', None)

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
        if hasattr(self, 'grid_size_combo'): self.grid_size_combo.setCurrentText(str(ui_settings.get("grid_size", 4)))
        if hasattr(self, 'show_splash_notification_toggle'): self.show_splash_notification_toggle.set_state(ui_settings.get("show_splash_notification", True))
        if hasattr(self, 'show_riot_client_toggle'): self.show_riot_client_toggle.set_state(ui_settings.get("show_riot_client", False))
        

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

        if is_dialog:
            self.setStyleSheet("background-color: #2c2a2b; border-top-left-radius: 20px; border-top-right-radius: 20px; border-bottom: 1px solid #4f4a4b;")
        else:
            self.setStyleSheet("background-color: #2c2a2b; border-top-left-radius: 20px; border-top-right-radius: 20px;")
        
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
            self.settings_button.setFixedSize(30, 30)
            self.settings_button.setIconSize(QSize(18, 18))
            self.settings_button.setStyleSheet("QPushButton { background-color: #4f4a4b; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }")
            if hasattr(parent, 'create_gear_icon'):
                self.settings_button.setIcon(parent.create_gear_icon(QColor("#e0d6d1")))
            layout.addWidget(self.settings_button)

            layout.addStretch()

            self.status_label = QLabel("Ready")
            self.status_label.setStyleSheet("color: #e0d6d1; font-size: 12px; font-weight: bold; background: transparent;")
            self.status_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.status_label)

            layout.addStretch()

            self.add_account_button = HoverButton()
            self.add_account_button.setFixedSize(30, 30)
            self.add_account_button.setIconSize(QSize(18, 18))
            self.add_account_button.setStyleSheet("QPushButton { background-color: #4f4a4b; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }")
            if hasattr(parent, 'create_add_icon'):
                self.add_account_button.setIcon(parent.create_add_icon(QColor("#e0d6d1"), QColor("#c89f68")))
            add_shadow = QGraphicsDropShadowEffect(self)
            add_shadow.setBlurRadius(15)
            add_shadow.setColor(QColor(0, 0, 0, 160))
            add_shadow.setOffset(0, 2)
            self.add_account_button.setGraphicsEffect(add_shadow)
            layout.addWidget(self.add_account_button)

            refresh_icon_path = get_asset_path("Refresh.png")
            self.refresh_button = QPushButton(QIcon(refresh_icon_path), "")
            self.refresh_button.setFixedSize(30, 30)
            self.refresh_button.setIconSize(QSize(18, 18))
            self.refresh_button.setStyleSheet("QPushButton { background-color: #4f4a4b; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }")
            refresh_shadow = QGraphicsDropShadowEffect(self)
            refresh_shadow.setBlurRadius(15)
            refresh_shadow.setColor(QColor(0, 0, 0, 160))
            refresh_shadow.setOffset(0, 2)
            self.refresh_button.setGraphicsEffect(refresh_shadow)
            layout.addWidget(self.refresh_button)

            self.minimize_button = QPushButton("−")
            self.minimize_button.setFixedSize(30, 30)
            self.minimize_button.setStyleSheet("QPushButton { background-color: #4f4a4b; color: #e0d6d1; font-size: 18px; font-weight: bold; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }")
            self.minimize_button.clicked.connect(self.parent_window.showMinimized)
            minimize_shadow = QGraphicsDropShadowEffect(self)
            minimize_shadow.setBlurRadius(15)
            minimize_shadow.setColor(QColor(0, 0, 0, 160))
            minimize_shadow.setOffset(0, 2)
            self.minimize_button.setGraphicsEffect(minimize_shadow)
            layout.addWidget(self.minimize_button)

            x_icon_path = get_asset_path("x.png")
            close_button = QPushButton()
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

        else:
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #e0d6d1; font-size: 15px; font-weight: bold; background: transparent;")
            layout.addWidget(title_label)

            layout.addStretch()

            x_icon_path = get_asset_path("x.png")
            close_button = QPushButton()
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
        self.main_widget.setStyleSheet("""#popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #4f4a4b; }
            QLabel { color: #e0d6d1; font-weight: bold; }
            QScrollArea { background-color: #3a3637; border: 1px solid #4f4a4b; border-radius: 10px; }""")

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
        self.remove_button.setStyleSheet("""QPushButton { background-color: #f38ba8; color: white; font-size: 14px; font-weight: bold; border-radius: 12px; border: 1px solid transparent; }
            QPushButton:hover { background-color: #e67e80; border-color: white; }""")
        self.remove_button.clicked.connect(self.remove_icon)
        self.remove_button.move(5, 5)  # Top-left corner
        self.remove_button.raise_()

        preview_layout.addWidget(self.icon_display_widget)
        self.content_layout.addWidget(preview_container)

        # --- Icons Grid Section ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: #3a3637;")
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
        cancel_button.setStyleSheet("""QPushButton { background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;}
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }""")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("""QPushButton { background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px; }
            QPushButton:hover { background-color: #d9b68b; }""")
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
        icon_button.setStyleSheet("QPushButton { border: 2px solid transparent; border-radius: 35px; } QPushButton:hover { border-color: #c89f68; }")
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
            self.icon_preview_button.setStyleSheet("""QPushButton { border: 2px solid transparent; border-radius: 60px; }
                QPushButton:hover { border-color: #d9b68b; }""")
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
        super().__init__("iMA Menu Path Not Found", parent)
        self.setFixedSize(450, 250)
        
        message_text = "Could not locate <b>shell.nss</b>.<br><br>Please select your iMA Menu installation folder (the one containing 'shell.nss' and the 'imports' folder)."
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 14px; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)

        self.path_edit = QLineEdit(default_path)
        self.path_edit.setPlaceholderText("Path to iMA Menu folder")
        self.path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        self.content_layout.addWidget(self.path_edit)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet('''
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 8px 15px; border: 1px solid transparent;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
        ''')
        browse_button.clicked.connect(self.browse)
        button_layout.addWidget(browse_button)
        
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet('''
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 8px 25px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        ''')
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        self.content_layout.addLayout(button_layout)

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select iMA Menu Folder", self.path_edit.text())
        if path:
            self.path_edit.setText(str(Path(path)))

    def get_path(self):
        return self.path_edit.text()

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
        self.setStyleSheet("""QWidget#AccountWidget { background-color: #3a3637; border-radius: 20px; border: 3px solid transparent; } 
                              QWidget#AccountWidget[selected="true"] { border-color: #c89f68; } 
                              QLabel#NameLabel { color: #e0d6d1; font-size: 13px; font-weight: bold; } 
                              QWidget#AccountWidget[selected="true"] QLabel#NameLabel { color: #c89f68; } 
                              QWidget#AccountWidget[is_add_button="true"] { background-color: #4f4a4b; border: 3px dashed #c89f68; border-radius: 20px; } 
                              QWidget#AccountWidget[is_add_button="true"]:hover { background-color: #5a5556; } 
                              QWidget#AccountWidget[is_add_button="true"] QLabel#NameLabel { color: #c89f68; }""")
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

        self.last_match_label = QLabel(self)
        self.last_match_label.setAlignment(Qt.AlignCenter)
        self.last_match_label.setStyleSheet("color: #c89f68; font-size: 11px; background-color: #2a2728; border-radius: 12px; padding: 4px 10px; border: 1px solid #4f4a4b;")
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
                    if last_map: match_parts.append(f"📍 {last_map}")
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

        source_pixmap = icon.pixmap(icon.actualSize(QSize(256, 256)))
        scaled_pixmap = source_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        x = (size - scaled_pixmap.width()) / 2
        y = (size - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        painter.end()
        
        self.icon_label.setPixmap(circular_pixmap)

    def paintEvent(self, event):
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def set_selected(self, selected):
        self.is_selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

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

    def update_data(self, account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, ui_settings): # Added ui_settings parameter
        self.account_name = account_name
        self.game = game
        self.rank = rank
        self.in_game_name = in_game_name
        self.in_game_tag = in_game_tag
        self.current_rr = current_rr
        self.last_game_rr = last_game_rr

        # Redraw the entire widget with new data
        self.set_icon(icon, 70)
        self.name_label.setText(self.account_name)

        # Update visibility based on ui_settings
        if ui_settings:
            self.set_show_game_icon(ui_settings.get("show_game_icons", True))
            self.set_show_rank_icon(ui_settings.get("show_rank_icon_left", False))
            self.set_show_name_tag(ui_settings.get("show_name_tag", True))
            self.set_show_current_rr(ui_settings.get("show_current_rr", True))
            self.set_show_last_game_rr(ui_settings.get("show_last_game_rr", True))

        if self.current_rr is not None:
            self.current_rr_label.setText(str(self.current_rr))
        if self.last_game_rr is not None:
            rr_text = f"+{self.last_game_rr}" if self.last_game_rr > 0 else str(self.last_game_rr)
            rr_color = "#a6e3a1" if self.last_game_rr > 0 else ("#f38ba8" if self.last_game_rr < 0 else "#e0d6d1") # White for 0
            self.last_game_rr_label.setText(f"({rr_text})")
            self.last_game_rr_label.setStyleSheet(f"color: {rr_color}; font-size: 11px;")
        
        # Update rank icon based on new rank data
        game_icon_size = 24 # Assuming this is consistent
        if self.rank:
            rank_icon_path = Path(get_asset_path(f"{self.rank.lower().replace(' ', '_')}.png"))
            if rank_icon_path.exists():
                pixmap = QPixmap(str(rank_icon_path)).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.rank_icon_label.setPixmap(pixmap)
            else:
                self.rank_icon_label.clear() # Clear if path doesn't exist
        else:
            self.rank_icon_label.clear() # Clear if no rank

        self.update()

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
        self.in_game_tag = in_game_tag
        self.switcher = switcher_instance
        self.worker = None
        self.setFixedSize(760, 580)

        self.main_widget.setStyleSheet("""
            #popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #c89f68; }
            QLabel { color: #e0d6d1; }
        """)

        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #343031; border-radius: 10px; border: 1px solid #4f4a4b;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)

        self.account_combo = QComboBox()
        self.account_combo.setStyleSheet("""
            QComboBox { 
                background-color: #4a4647; border: 1px solid #c89f68; border-radius: 6px; padding: 4px 10px; color: #e0d6d1; font-weight: bold; font-size: 13px;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; border: 1px solid #c89f68; selection-background-color: #c89f68; color: #e0d6d1; selection-color: #2c2a2b; padding: 4px;
            }
        """)
        self.populate_account_combo()
        self.account_combo.currentIndexChanged.connect(self.on_account_combo_changed)
        header_layout.addWidget(self.account_combo, 2)

        self.rank_icon_label = QLabel()
        self.rank_icon_label.setFixedSize(28, 28)
        header_layout.addWidget(self.rank_icon_label)

        self.rank_rr_label = QLabel()
        self.rank_rr_label.setStyleSheet("font-size: 13px; color: #ffffff; font-weight: bold;")
        header_layout.addWidget(self.rank_rr_label, 2)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh History")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 6px 15px; border: none; }
            QPushButton:hover { background-color: #d9b68b; }
            QPushButton:disabled { background-color: #5a5556; color: #888888; }
        """)
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
            color = "#a6e3a1" if last_game_rr > 0 else ("#f38ba8" if last_game_rr < 0 else "#e0d6d1")
            sign = "+" if last_game_rr > 0 else ""
            last_rr_str = f" <font color='{color}'>({sign}{last_game_rr})</font>"

        self.rank_rr_label.setText(f"<b>{rank_str}</b>{rr_str}{last_rr_str}")

    def setup_matches_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 5, 0, 5)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical { border: none; background-color: #2c2a2b; width: 10px; }
            QScrollBar::handle:vertical { background-color: #c89f68; min-height: 25px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self.matches_container = QWidget()
        self.matches_container.setStyleSheet("background-color: transparent;")
        self.matches_layout = QVBoxLayout(self.matches_container)
        self.matches_layout.setContentsMargins(0, 5, 0, 5)
        self.matches_layout.setSpacing(10)
        self.matches_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.matches_container)
        layout.addWidget(self.scroll_area)

        self.status_label = QLabel("Loading match history...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #c89f68; padding: 20px;")
        self.matches_layout.addWidget(self.status_label)

        self.stacked_widget.addWidget(page)

    def setup_detail_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("← Back to Matches")
        self.back_btn.setStyleSheet("""
            QPushButton { background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 6px; padding: 6px 14px; border: none; }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        self.back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        top_bar.addWidget(self.back_btn)

        self.detail_header_label = QLabel("Match Scoreboard")
        self.detail_header_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        top_bar.addWidget(self.detail_header_label)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical { border: none; background-color: #2c2a2b; width: 10px; }
            QScrollBar::handle:vertical { background-color: #c89f68; min-height: 25px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

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
            bg_color = "#1e3025"
            border_color = "#40a060"
            result_color = "#a6e3a1"
        elif result == "LOSS":
            bg_color = "#351e24"
            border_color = "#a04050"
            result_color = "#f38ba8"
        else:
            bg_color = "#282933"
            border_color = "#585b70"
            result_color = "#9399b2"

        card.setStyleSheet(f"""
            #MatchCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            #MatchCard:hover {{
                border: 1px solid #c89f68;
                background-color: #383435;
            }}
            #MatchCard QLabel {{
                color: #e0d6d1;
                border: none;
                background: transparent;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        res_layout = QVBoxLayout()
        res_label = QLabel(result)
        res_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {result_color};")
        res_layout.addWidget(res_label)

        score_text = match.get("score", "-")
        score_label = QLabel(score_text)
        score_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        res_layout.addWidget(score_label)
        layout.addLayout(res_layout, 1)

        map_layout = QVBoxLayout()
        map_name = match.get("map", "Unknown Map")
        map_label = QLabel(f"📍 <b>{map_name}</b>")
        map_label.setStyleSheet("font-size: 13px; color: #ffffff;")
        map_layout.addWidget(map_label)

        mode_name = match.get("mode", "Competitive")
        mode_label = QLabel(mode_name)
        mode_label.setStyleSheet("font-size: 11px; color: #b0a8a8;")
        map_layout.addWidget(mode_label)
        layout.addLayout(map_layout, 2)

        agent_layout = QVBoxLayout()
        agent_name = match.get("agent", "Agent")
        agent_icon = get_agent_icon_html(agent_name, self.switcher.base_dir) if self.switcher else "⚔️ "
        agent_label = QLabel(f"{agent_icon}<b>{agent_name}</b>")
        agent_label.setStyleSheet("font-size: 13px; color: #c89f68;")
        agent_layout.addWidget(agent_label)

        kda_text = match.get("kda", "-")
        kda_label = QLabel(f"KDA: {kda_text}")
        kda_label.setStyleSheet("font-size: 12px; color: #e0d6d1;")
        agent_layout.addWidget(kda_label)
        layout.addLayout(agent_layout, 2)

        time_layout = QVBoxLayout()
        kd_ratio = match.get("kd", "-")
        kd_label = QLabel(f"KD: {kd_ratio}")
        kd_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        time_layout.addWidget(kd_label)

        date_text = match.get("date", "")
        date_label = QLabel(date_text)
        date_label.setStyleSheet("font-size: 10px; color: #888888;")
        time_layout.addWidget(date_label)
        layout.addLayout(time_layout, 1)

        arrow_label = QLabel("➔")
        arrow_label.setStyleSheet("font-size: 16px; color: #c89f68; font-weight: bold;")
        layout.addWidget(arrow_label)

        def on_click(event):
            self.show_match_detail(match)

        card.mousePressEvent = on_click
        return card

    def show_match_detail(self, match):
        for i in reversed(range(self.detail_layout.count())):
            item = self.detail_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        map_name = match.get("map", "Map")
        mode_name = match.get("mode", "Competitive")
        score_text = match.get("score", "-")
        result = match.get("result", "DRAW")

        self.detail_header_label.setText(f"{map_name} • {mode_name} ({score_text})")

        banner = QWidget()
        banner_bg = "#1e3025" if result == "WIN" else ("#351e24" if result == "LOSS" else "#282933")
        banner_border = "#40a060" if result == "WIN" else ("#a04050" if result == "LOSS" else "#585b70")
        banner.setStyleSheet(f"background-color: {banner_bg}; border: 1px solid {banner_border}; border-radius: 10px; padding: 10px;")
        banner_layout = QHBoxLayout(banner)

        res_lbl = QLabel(f"<b>{result}</b> ({score_text})")
        res_lbl.setStyleSheet("font-size: 16px; color: #ffffff; border: none; background: transparent;")
        banner_layout.addWidget(res_lbl)
        banner_layout.addStretch()

        meta_lbl = QLabel(f"📍 {map_name} • {mode_name} • {match.get('date', '')}")
        meta_lbl.setStyleSheet("font-size: 12px; color: #b0a8a8; border: none; background: transparent;")
        banner_layout.addWidget(meta_lbl)

        self.detail_layout.addWidget(banner)

        players = match.get("players", [])
        blue_players = [p for p in players if p.get("team", "").lower() == "blue"]
        red_players = [p for p in players if p.get("team", "").lower() == "red"]

        if not blue_players and not red_players and players:
            blue_players = players[:5]
            red_players = players[5:]

        if blue_players:
            blue_box = self._create_team_scoreboard("DEFENDERS", blue_players, "#3b82f6")
            self.detail_layout.addWidget(blue_box)

        if red_players:
            red_box = self._create_team_scoreboard("ATTACKERS", red_players, "#ef4444")
            self.detail_layout.addWidget(red_box)

        self.stacked_widget.setCurrentIndex(1)

    def _create_team_scoreboard(self, team_title, players_list, team_color):
        title_str = str(team_title).upper()
        if "BLUE" in title_str or "DEFEND" in title_str:
            display_title = "DEFENDERS"
            color_to_use = "#3b82f6"
        elif "RED" in title_str or "ATTACK" in title_str:
            display_title = "ATTACKERS"
            color_to_use = "#ef4444"
        else:
            display_title = team_title
            color_to_use = team_color

        box = QWidget()
        box.setObjectName("TeamScoreboardBox")
        box.setStyleSheet("""
            #TeamScoreboardBox {
                background-color: #343031;
                border-radius: 10px;
                border: none;
            }
            #TeamScoreboardBox QLabel {
                border: none;
                background: transparent;
            }
        """)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        t_lbl = QLabel(display_title)
        t_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color_to_use}; border: none; background: transparent;")
        layout.addWidget(t_lbl)

        header_row = QWidget()
        header_row.setObjectName("TeamHeaderRow")
        header_row.setStyleSheet("""
            #TeamHeaderRow {
                background-color: #2a2728;
                border-radius: 6px;
                border: none;
            }
            #TeamHeaderRow QLabel {
                color: #888888;
                font-size: 11px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
        """)
        h_layout = QHBoxLayout(header_row)
        h_layout.setContentsMargins(8, 4, 8, 4)

        h_player = QLabel("Player")
        h_layout.addWidget(h_player, 3)

        h_agent = QLabel("Agent")
        h_layout.addWidget(h_agent, 2)

        h_score = QLabel("ACS/Score")
        h_layout.addWidget(h_score, 1)

        h_kda = QLabel("K / D / A")
        h_layout.addWidget(h_kda, 2)

        h_kd = QLabel("K/D")
        h_layout.addWidget(h_kd, 1)

        layout.addWidget(header_row)

        for p in players_list:
            p_name = p.get("name", "Player")
            p_tag = p.get("tag", "")
            full_tag = f"{p_name}#{p_tag}" if p_tag else p_name

            is_me = (self.in_game_name and p_name.lower() == self.in_game_name.lower())

            row = QWidget()
            row.setObjectName("PlayerRow")
            if is_me:
                row.setStyleSheet("""
                    #PlayerRow {
                        background-color: #4a3e2e;
                        border: 1px solid #c89f68;
                        border-radius: 6px;
                    }
                    #PlayerRow QLabel {
                        border: none;
                        background: transparent;
                    }
                """)
            else:
                row.setStyleSheet("""
                    #PlayerRow {
                        background-color: #2c2a2b;
                        border: none;
                        border-radius: 6px;
                    }
                    #PlayerRow QLabel {
                        border: none;
                        background: transparent;
                    }
                """)

            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(8, 6, 8, 6)

            rank_text = p.get("rank", "Unranked")
            r_name = QLabel(f"<b>{full_tag}</b><br><font color='#b0a8a8' size='2'>{rank_text}</font>")
            r_name.setStyleSheet("font-size: 12px; color: #ffffff;" if is_me else "font-size: 12px; color: #e0d6d1;")
            r_layout.addWidget(r_name, 3)

            p_agent_name = p.get('character', 'Agent')
            p_agent_icon = get_agent_icon_html(p_agent_name, self.switcher.base_dir) if self.switcher else "⚔️ "
            r_agent = QLabel(f"{p_agent_icon}{p_agent_name}")
            r_agent.setStyleSheet("font-size: 12px; color: #c89f68;")
            r_layout.addWidget(r_agent, 2)

            r_score = QLabel(str(p.get("score", 0)))
            r_score.setStyleSheet("font-size: 12px; color: #ffffff; font-weight: bold;")
            r_layout.addWidget(r_score, 1)

            k = p.get("kills", 0)
            d = p.get("deaths", 0)
            a = p.get("assists", 0)
            r_kda = QLabel(f"{k} / {d} / {a}")
            r_kda.setStyleSheet("font-size: 12px; color: #e0d6d1;")
            r_layout.addWidget(r_kda, 2)

            r_kd = QLabel(str(p.get("kd", "0.00")))
            r_kd.setStyleSheet("font-size: 12px; font-weight: bold; color: #a6e3a1;" if float(p.get("kd", 0)) >= 1.0 else "font-size: 12px; font-weight: bold; color: #f38ba8;")
            r_layout.addWidget(r_kd, 1)

            layout.addWidget(row)

        return box
