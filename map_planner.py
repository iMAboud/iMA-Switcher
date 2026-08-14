import sys
import os
import math
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QScrollArea,
    QFileDialog,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsDropShadowEffect,
    QMenu,
    QAction,
    QSlider,
    QLineEdit,
    QButtonGroup,
    QDialog,
    QMessageBox
)
from PyQt5.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QPen,
    QBrush,
    QPainterPath,
    QPolygonF,
    QCursor,
    QTransform,
    QImage
)
from PyQt5.QtCore import (
    Qt,
    QSize,
    QPoint,
    QPointF,
    QRectF,
    pyqtSignal,
    QTimer
)

from ui_components import PopupDialog
from theme_manager import get_theme, generate_global_qss, apply_theme_to_app

class AgentTokenItem(QGraphicsItem):
    def __init__(self, agent_name, pixmap, team="attacker", radius=22):
        super().__init__()
        self.agent_name = agent_name
        self.raw_pixmap = pixmap
        self.team = team
        self.radius = radius
        self.show_cone = False
        self.cone_angle = 0.0
        self.cone_span = 45.0
        self.cone_length = 130.0

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.is_hovered = False

    def boundingRect(self):
        extra = self.cone_length + 20 if self.show_cone else self.radius + 15
        return QRectF(-extra, -extra, extra * 2, extra * 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.show_cone:
            cone_color = QColor(239, 68, 68, 45) if self.team == "attacker" else QColor(32, 230, 147, 45)
            cone_border = QColor(239, 68, 68, 140) if self.team == "attacker" else QColor(32, 230, 147, 140)
            
            cone_path = QPainterPath()
            cone_path.moveTo(0, 0)
            rect = QRectF(-self.cone_length, -self.cone_length, self.cone_length * 2, self.cone_length * 2)
            start_angle = -self.cone_angle - (self.cone_span / 2.0)
            cone_path.arcTo(rect, start_angle, self.cone_span)
            cone_path.closeSubpath()
            
            painter.fillPath(cone_path, QBrush(cone_color))
            painter.strokePath(cone_path, QPen(cone_border, 1.5, Qt.DashLine))

        r = self.radius
        outer_rect = QRectF(-r, -r, r * 2, r * 2)

        shadow_color = QColor(0, 0, 0, 160)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(-r + 1, -r + 2, r * 2, r * 2))

        team_color = QColor("#ef4444") if self.team == "attacker" else QColor("#20e693")
        if self.isSelected():
            team_color = QColor("#ffd700")

        border_pen = QPen(team_color, 3.5 if (self.is_hovered or self.isSelected()) else 2.5)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(QColor("#1e1e24")))
        painter.drawEllipse(outer_rect)

        clip_path = QPainterPath()
        clip_path.addEllipse(outer_rect.adjusted(2, 2, -2, -2))
        painter.save()
        painter.setClipPath(clip_path)
        if self.raw_pixmap and not self.raw_pixmap.isNull():
            scaled = self.raw_pixmap.scaled(int((r - 2) * 2), int((r - 2) * 2), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(int(-r + 2), int(-r + 2), scaled)
        else:
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(outer_rect, Qt.AlignCenter, self.agent_name[:2].upper())
        painter.restore()

        name_rect = QRectF(-r - 10, r + 2, (r + 10) * 2, 14)
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.setPen(QColor("#000000"))
        painter.drawText(name_rect.adjusted(1, 1, 1, 1), Qt.AlignCenter, self.agent_name)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(name_rect, Qt.AlignCenter, self.agent_name)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: #2c2a2b; color: #e0d6d1; border: 1px solid #c89f68; border-radius: 8px; padding: 4px; }
            QMenu::item { padding: 6px 20px 6px 10px; border-radius: 6px; }
            QMenu::item:selected { background-color: #c89f68; color: #2c2a2b; font-weight: bold; }
        """)

        switch_team_act = menu.addAction("Switch to Defender" if self.team == "attacker" else "Switch to Attacker")
        toggle_cone_act = menu.addAction("Hide Vision Cone" if self.show_cone else "Show Vision Cone")
        menu.addSeparator()
        remove_act = menu.addAction("Remove Agent")

        chosen = menu.exec_(event.screenPos())
        if chosen == switch_team_act:
            self.team = "defender" if self.team == "attacker" else "attacker"
            self.update()
        elif chosen == toggle_cone_act:
            self.show_cone = not self.show_cone
            self.update()
        elif chosen == remove_act:
            if self.scene():
                self.scene().removeItem(self)

    def mouseDoubleClickEvent(self, event):
        self.team = "defender" if self.team == "attacker" else "attacker"
        self.update()
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if self.show_cone and (event.modifiers() & Qt.ShiftModifier or not self.isSelected()):
            delta = event.delta() / 8.0
            self.cone_angle = (self.cone_angle + delta) % 360.0
            self.update()
            event.accept()
        else:
            delta = event.delta()
            step = 2 if delta > 0 else -2
            self.radius = max(12, min(80, self.radius + step))
            self.prepareGeometryChange()
            self.update()
            event.accept()

class CalloutTextItem(QGraphicsTextItem):
    def __init__(self, text="Tactical Callout", color=QColor("#ffffff"), parent=None):
        super().__init__(text, parent)
        self.setDefaultTextColor(color)
        self.font_size = 14
        self.setFont(QFont("Segoe UI", self.font_size, QFont.Bold))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsFocusable)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)

    def wheelEvent(self, event):
        delta = event.delta()
        step = 2 if delta > 0 else -2
        self.font_size = max(8, min(48, self.font_size + step))
        f = self.font()
        f.setPointSize(self.font_size)
        f.setBold(True)
        self.setFont(f)
        self.update()
        event.accept()

class TacticalMarkerItem(QGraphicsItem):
    def __init__(self, marker_type, color=QColor("#ef4444"), size=32):
        super().__init__()
        self.marker_type = marker_type
        self.color = color
        self.size = size
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)

    def boundingRect(self):
        half = self.size / 2.0
        return QRectF(-half - 4, -half - 4, self.size + 8, self.size + 8)

    def wheelEvent(self, event):
        delta = event.delta()
        step = 4 if delta > 0 else -4
        self.size = max(14, min(160, self.size + step))
        self.prepareGeometryChange()
        self.update()
        event.accept()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        half = self.size / 2.0
        rect = QRectF(-half, -half, self.size, self.size)

        if self.marker_type == "smoke":
            smoke_brush = QBrush(QColor(self.color.red(), self.color.green(), self.color.blue(), 110))
            smoke_pen = QPen(QColor(self.color.red(), self.color.green(), self.color.blue(), 220), 2, Qt.DashLine)
            painter.setBrush(smoke_brush)
            painter.setPen(smoke_pen)
            painter.drawEllipse(rect)

            pulse_inner = rect.adjusted(6, 6, -6, -6)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 35)))
            painter.drawEllipse(pulse_inner)

        elif self.marker_type == "spike":
            painter.setBrush(QBrush(QColor("#f59e0b")))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            points = [QPointF(0, -half), QPointF(half, 0), QPointF(0, half), QPointF(-half, 0)]
            painter.drawPolygon(QPolygonF(points))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.setPen(QColor("#1e1e24"))
            painter.drawText(rect, Qt.AlignCenter, "⚡")

        elif self.marker_type == "ping":
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(rect)
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(rect, Qt.AlignCenter, "!")

        elif self.marker_type == "danger":
            painter.setBrush(QBrush(QColor("#ef4444")))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawEllipse(rect)
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(rect, Qt.AlignCenter, "✕")

class MapGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setStyleSheet("background-color: #17181c; border-radius: 12px;")

        self.current_tool = "select"
        self.current_color = QColor("#ef4444")
        self.current_stroke = 3.0
        self.is_drawing = False
        self.current_path_item = None
        self.current_painter_path = None
        self.start_point = QPointF()
        self._user_zoomed = False

    def fit_map(self):
        if self.scene() and self.scene().sceneRect().isValid() and not self.scene().sceneRect().isEmpty():
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(20, self.fit_map)
        QTimer.singleShot(100, self.fit_map)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not getattr(self, '_user_zoomed', False):
            self.fit_map()

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        if tool_name == "select":
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.ArrowCursor)
        elif tool_name == "pan":
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    def wheelEvent(self, event):
        item = self.itemAt(event.pos())
        if item and item != getattr(self.parent(), 'map_pixmap_item', None):
            super().wheelEvent(event)
            return

        self._user_zoomed = True
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        current_scale = self.transform().m11()
        if 0.35 <= current_scale * zoom_factor <= 4.0:
            self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake_event = event
            super().mousePressEvent(event)
            return

        scene_pos = self.mapToScene(event.pos())

        if event.button() == Qt.LeftButton:
            if self.current_tool == "pen":
                self.is_drawing = True
                self.current_painter_path = QPainterPath(scene_pos)
                pen = QPen(self.current_color, self.current_stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                self.current_path_item = self.scene().addPath(self.current_painter_path, pen)
                self.current_path_item.setFlags(QGraphicsItem.ItemIsSelectable)
                event.accept()
                return

            elif self.current_tool == "arrow":
                self.is_drawing = True
                self.start_point = scene_pos
                self.current_painter_path = QPainterPath(scene_pos)
                pen = QPen(self.current_color, self.current_stroke + 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                self.current_path_item = self.scene().addPath(self.current_painter_path, pen)
                event.accept()
                return

            elif self.current_tool == "smoke":
                marker = TacticalMarkerItem("smoke", self.current_color, size=65)
                marker.setPos(scene_pos)
                self.scene().addItem(marker)
                event.accept()
                return

            elif self.current_tool == "spike":
                marker = TacticalMarkerItem("spike", size=30)
                marker.setPos(scene_pos)
                self.scene().addItem(marker)
                event.accept()
                return

            elif self.current_tool == "ping":
                marker = TacticalMarkerItem("ping", self.current_color, size=28)
                marker.setPos(scene_pos)
                self.scene().addItem(marker)
                event.accept()
                return

            elif self.current_tool == "danger":
                marker = TacticalMarkerItem("danger", size=28)
                marker.setPos(scene_pos)
                self.scene().addItem(marker)
                event.accept()
                return

            elif self.current_tool == "text":
                text_item = CalloutTextItem("Tactical Callout", self.current_color)
                text_item.setPos(scene_pos)
                self.scene().addItem(text_item)
                text_item.setFocus()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            scene_pos = self.mapToScene(event.pos())
            if self.current_tool == "pen" and self.current_path_item:
                self.current_painter_path.lineTo(scene_pos)
                self.current_path_item.setPath(self.current_painter_path)
                event.accept()
                return
            elif self.current_tool == "arrow" and self.current_path_item:
                path = QPainterPath(self.start_point)
                path.lineTo(scene_pos)
                
                dx = scene_pos.x() - self.start_point.x()
                dy = scene_pos.y() - self.start_point.y()
                angle = math.atan2(dy, dx)
                arrow_size = 14.0
                
                p1 = scene_pos - QPointF(arrow_size * math.cos(angle - math.pi / 6.0), arrow_size * math.sin(angle - math.pi / 6.0))
                p2 = scene_pos - QPointF(arrow_size * math.cos(angle + math.pi / 6.0), arrow_size * math.sin(angle + math.pi / 6.0))
                
                path.moveTo(p1)
                path.lineTo(scene_pos)
                path.lineTo(p2)
                
                self.current_path_item.setPath(path)
                event.accept()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing:
            self.is_drawing = False
            self.current_path_item = None
            self.current_painter_path = None
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)
        super().mouseReleaseEvent(event)

class MapPlannerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_dir = Path(__file__).parent.resolve()
        self.maps_dir = self.base_dir / "maps" / "maps planner"
        if not self.maps_dir.exists():
            self.maps_dir = self.base_dir / "maps"

        self.agents_dir = self.base_dir / "Agents"
        if not self.agents_dir.exists():
            self.agents_dir = self.base_dir / "icons"

        self.scene = QGraphicsScene(self)
        self.map_pixmap_item = None
        self.history_stack = []

        self.init_ui()
        self.load_available_maps()
        self.load_available_agents()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Left Control Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(270)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)

        # Map Selector Group
        map_card = QWidget()
        map_card.setStyleSheet("background-color: #242122; border: 1px solid #4a4647; border-radius: 12px; padding: 6px;")
        map_card_layout = QVBoxLayout(map_card)
        map_card_layout.setSpacing(6)
        
        map_header = QLabel("SELECT MAP")
        map_header.setStyleSheet("color: #c89f68; font-size: 11px; font-weight: bold; border: none; padding: 0;")
        map_card_layout.addWidget(map_header)

        self.map_combo = QComboBox()
        self.map_combo.setStyleSheet("""
            QComboBox { background-color: #353233; color: #ffffff; border: 1px solid #4a4647; border-radius: 8px; padding: 6px 12px; font-weight: bold; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox QAbstractItemView { background-color: #2c2a2b; color: #e0d6d1; selection-background-color: #c89f68; selection-color: #2c2a2b; border: 1px solid #4a4647; }
        """)
        self.map_combo.currentIndexChanged.connect(self.on_map_changed)
        map_card_layout.addWidget(self.map_combo)
        sidebar_layout.addWidget(map_card)

        # Tools Palette Group
        tools_card = QWidget()
        tools_card.setStyleSheet("background-color: #242122; border: 1px solid #4a4647; border-radius: 12px; padding: 6px;")
        tools_card_layout = QVBoxLayout(tools_card)
        tools_card_layout.setSpacing(6)

        tools_header = QLabel("TACTICAL TOOLS")
        tools_header.setStyleSheet("color: #c89f68; font-size: 11px; font-weight: bold; border: none; padding: 0;")
        tools_card_layout.addWidget(tools_header)

        tools_grid = QGridLayout()
        tools_grid.setSpacing(6)

        self.tool_buttons = {}
        tool_defs = [
            ("select", "📍 Select / Move", 0, 0),
            ("text", "💬 Callout Text", 0, 1),
            ("pen", "✏️ Draw Path", 1, 0),
            ("arrow", "➡️ Push Arrow", 1, 1),
            ("smoke", "⭕ Vision Smoke", 2, 0),
            ("spike", "⚡ Spike Plant", 2, 1),
            ("ping", "❗ Ping Marker", 3, 0),
            ("danger", "✕ Danger Zone", 3, 1),
        ]

        button_style = """
            QPushButton { background-color: #353233; color: #e0d6d1; border: 1px solid #4a4647; border-radius: 8px; padding: 6px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #4a4647; border-color: #c89f68; }
            QPushButton:checked { background-color: #c89f68; color: #2c2a2b; border-color: #d9b68b; }
        """

        self.tools_btn_group = QButtonGroup(self)
        self.tools_btn_group.setExclusive(True)

        for tool_id, tool_label, r, c in tool_defs:
            btn = QPushButton(tool_label)
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda _, tid=tool_id: self.select_tool(tid))
            self.tool_buttons[tool_id] = btn
            self.tools_btn_group.addButton(btn)
            tools_grid.addWidget(btn, r, c)

        self.tool_buttons["select"].setChecked(True)
        tools_card_layout.addLayout(tools_grid)

        # Color Selector
        color_layout = QHBoxLayout()
        color_layout.setSpacing(6)
        color_label = QLabel("Color:")
        color_label.setStyleSheet("color: #e0d6d1; font-size: 11px; border: none;")
        color_layout.addWidget(color_label)

        palette = [
            ("#ef4444", "Attacker Red"),
            ("#20e693", "Defender Teal"),
            ("#f59e0b", "Spike Gold"),
            ("#3b82f6", "Info Blue"),
            ("#a855f7", "Utility Purple"),
            ("#ffffff", "Neutral White")
        ]
        self.color_buttons = []
        for hex_code, name in palette:
            c_btn = QPushButton()
            c_btn.setFixedSize(22, 22)
            c_btn.setToolTip(name)
            c_btn.setStyleSheet(f"background-color: {hex_code}; border-radius: 11px; border: 1.5px solid #ffffff;")
            c_btn.clicked.connect(lambda _, h=hex_code: self.set_draw_color(h))
            color_layout.addWidget(c_btn)
            self.color_buttons.append(c_btn)

        tools_card_layout.addLayout(color_layout)
        sidebar_layout.addWidget(tools_card)

        # Agent Palette Group
        agents_card = QWidget()
        agents_card.setStyleSheet("background-color: #242122; border: 1px solid #4a4647; border-radius: 12px; padding: 6px;")
        agents_card_layout = QVBoxLayout(agents_card)
        agents_card_layout.setSpacing(6)

        agent_header_layout = QHBoxLayout()
        agent_header = QLabel("AGENT ROSTER")
        agent_header.setStyleSheet("color: #c89f68; font-size: 11px; font-weight: bold; border: none;")
        agent_header_layout.addWidget(agent_header)
        agent_header_layout.addStretch()

        self.team_mode_toggle = QPushButton("Attacker Mode")
        self.team_mode_toggle.setCheckable(True)
        self.team_mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border-radius: 13px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #ef4444;
                min-width: 95px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:checked {
                background-color: #20e693;
                color: #064e3b;
                border: 1px solid #20e693;
            }
            QPushButton:checked:hover {
                background-color: #10b981;
            }
        """)
        self.team_mode_toggle.toggled.connect(self.on_team_mode_toggled)
        agent_header_layout.addWidget(self.team_mode_toggle)
        agents_card_layout.addLayout(agent_header_layout)

        self.agent_search = QLineEdit()
        self.agent_search.setPlaceholderText("Search agent...")
        self.agent_search.setStyleSheet("background-color: #353233; color: #ffffff; border: 1px solid #4a4647; border-radius: 6px; padding: 4px 8px; font-size: 11px;")
        self.agent_search.textChanged.connect(self.filter_agents)
        agents_card_layout.addWidget(self.agent_search)

        # Scrollable Agents Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar { width: 4px; background: transparent; } QScrollBar::handle { background: #4a4647; border-radius: 2px; }")
        
        self.agents_grid_widget = QWidget()
        self.agents_grid = QGridLayout(self.agents_grid_widget)
        self.agents_grid.setContentsMargins(0, 0, 0, 0)
        self.agents_grid.setSpacing(6)
        scroll.setWidget(self.agents_grid_widget)
        agents_card_layout.addWidget(scroll)

        sidebar_layout.addWidget(agents_card, 1)

        # Bottom Actions Group
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #ef4444; color: #ffffff; font-weight: bold; font-size: 11px; border-radius: 8px; padding: 8px; border: none; }
            QPushButton:hover { background-color: #f87171; }
        """)
        clear_btn.clicked.connect(self.clear_drawings)
        actions_layout.addWidget(clear_btn)

        export_btn = QPushButton("Export PNG")
        export_btn.setStyleSheet("""
            QPushButton { background-color: #c89f68; color: #2c2a2b; font-weight: bold; font-size: 11px; border-radius: 8px; padding: 8px; border: none; }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        export_btn.clicked.connect(self.export_map_image)
        actions_layout.addWidget(export_btn)

        sidebar_layout.addLayout(actions_layout)
        main_layout.addWidget(sidebar)

        # Center Map Viewport
        self.view = MapGraphicsView(self.scene, self)
        main_layout.addWidget(self.view, 1)

    def load_available_maps(self):
        self.map_combo.blockSignals(True)
        self.map_combo.clear()
        
        map_files = []
        if self.maps_dir.exists():
            for f in self.maps_dir.glob("*.png"):
                map_files.append(f.stem.capitalize())
        
        if not map_files:
            fallback = ["Ascent", "Bind", "Haven", "Split", "Icebox", "Breeze", "Fracture", "Pearl", "Lotus", "Sunset", "Abyss"]
            map_files = fallback

        map_files = sorted(list(set(map_files)))
        self.map_combo.addItems(map_files)
        self.map_combo.blockSignals(False)

        if map_files:
            self.set_map(map_files[0])

    def on_map_changed(self, index):
        map_name = self.map_combo.currentText()
        if map_name:
            self.set_map(map_name)

    def set_map(self, map_name):
        map_path = self.maps_dir / f"{map_name}.png"
        if not map_path.exists():
            map_path = self.maps_dir / f"{map_name.lower()}.png"
        if not map_path.exists():
            map_path = self.base_dir / "maps" / f"{map_name.lower()}.png"

        if map_path.exists():
            pixmap = QPixmap(str(map_path))
            
            self.scene.clear()
            self.map_pixmap_item = self.scene.addPixmap(pixmap)
            self.map_pixmap_item.setZValue(-1000)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
            
            self.view._user_zoomed = False
            self.view.fit_map()
            QTimer.singleShot(20, self.view.fit_map)
            QTimer.singleShot(100, self.view.fit_map)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(30, self.view.fit_map)
        QTimer.singleShot(150, self.view.fit_map)

    def load_available_agents(self):
        for i in reversed(range(self.agents_grid.count())):
            w = self.agents_grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.agent_buttons = []
        agent_paths = sorted(list(self.agents_dir.glob("*.png")))
        
        row, col = 0, 0
        for p in agent_paths:
            agent_name = p.stem
            pixmap = QPixmap(str(p))
            
            btn = QPushButton()
            btn.setFixedSize(48, 48)
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(QSize(38, 38))
            btn.setToolTip(f"Add {agent_name} to Map")
            btn.setStyleSheet("""
                QPushButton { background-color: #353233; border: 1px solid #4a4647; border-radius: 8px; }
                QPushButton:hover { background-color: #4a4647; border-color: #c89f68; }
            """)
            btn.clicked.connect(lambda _, a=agent_name, pm=pixmap: self.add_agent_token(a, pm))
            
            self.agents_grid.addWidget(btn, row, col)
            self.agent_buttons.append((agent_name, btn))
            
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def filter_agents(self, query):
        q = query.strip().lower()
        for name, btn in self.agent_buttons:
            btn.setVisible(q in name.lower())

    def on_team_mode_toggled(self, checked):
        if checked:
            self.team_mode_toggle.setText("Defender Mode")
        else:
            self.team_mode_toggle.setText("Attacker Mode")

    def add_agent_token(self, agent_name, pixmap):
        team = "defender" if self.team_mode_toggle.isChecked() else "attacker"
        token = AgentTokenItem(agent_name, pixmap, team=team, radius=22)
        
        center_pos = self.view.mapToScene(self.view.viewport().rect().center())
        token.setPos(center_pos.x() + (len(self.scene.items()) % 5) * 15, center_pos.y() + (len(self.scene.items()) % 5) * 15)
        
        self.scene.addItem(token)
        self.select_tool("select")

    def select_tool(self, tool_id):
        for tid, btn in self.tool_buttons.items():
            btn.setChecked(tid == tool_id)
        self.view.set_tool(tool_id)

    def set_draw_color(self, hex_color):
        self.view.current_color = QColor(hex_color)

    def clear_drawings(self):
        items_to_remove = [item for item in self.scene.items() if item != self.map_pixmap_item]
        for item in items_to_remove:
            self.scene.removeItem(item)

    def export_map_image(self):
        rect = self.scene.sceneRect()
        if rect.isEmpty():
            return
        
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        self.scene.render(painter, QRectF(image.rect()), rect)
        painter.end()

        save_path, _ = QFileDialog.getSaveFileName(self, "Export Tactical Map", f"Tactical_{self.map_combo.currentText()}.png", "PNG Images (*.png)")
        if save_path:
            image.save(save_path, "PNG")

class MapPlannerTitleBar(QWidget):
    def __init__(self, title, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.drag_position = QPoint()
        self.setFixedHeight(44)
        self.setObjectName("MapPlannerTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        base_dir = Path(__file__).parent.resolve()
        logo_path = base_dir / "Assets" / "app_icon.png"
        if not logo_path.exists():
            logo_path = base_dir / "app_icon.png"

        self.logo_label = QLabel()
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        layout.addWidget(self.logo_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #c89f68; font-size: 14px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(title_label)

        layout.addStretch()

        self.minimize_button = QPushButton()
        self.minimize_button.setFixedSize(30, 30)
        minimize_icon_path = base_dir / "Assets" / "minimize.png"
        if minimize_icon_path.exists():
            self.minimize_button.setIcon(QIcon(str(minimize_icon_path)))
            self.minimize_button.setIconSize(QSize(16, 16))
        else:
            self.minimize_button.setText("—")
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #353233; color: #e0d6d1; border: 1px solid #4a4647;
                border-radius: 15px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4a4647; border-color: #c89f68; }
        """)
        self.minimize_button.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.minimize_button)

        self.close_button = QPushButton()
        self.close_button.setFixedSize(30, 30)
        x_icon_path = base_dir / "Assets" / "x.png"
        if x_icon_path.exists():
            self.close_button.setIcon(QIcon(str(x_icon_path)))
            self.close_button.setIconSize(QSize(14, 14))
        else:
            self.close_button.setText("✕")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #353233; color: #e0d6d1; border: 1px solid #4a4647;
                border-radius: 15px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e84057; color: #ffffff; border-color: #e84057; }
        """)
        self.close_button.clicked.connect(self.parent_window.close)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.parent_window.move(event.globalPos() - self.drag_position)
            event.accept()

class MapPlannerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1150, 780)
        self.resize(1200, 820)

        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #1c1a1b;
                border: 1px solid #c89f68;
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title_bar = MapPlannerTitleBar("iMA Map Planner", self)
        layout.addWidget(title_bar)

        self.planner_widget = MapPlannerWidget(self)
        layout.addWidget(self.planner_widget, 1)

        self.setCentralWidget(container)

class MapPlannerDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Map Planner", parent)
        self.setFixedSize(1150, 780)
        
        self.planner_widget = MapPlannerWidget(self)
        self.content_layout.addWidget(self.planner_widget)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4647; color: #e0d6d1; font-weight: bold; font-size: 12px;
                border-radius: 8px; padding: 8px 22px; border: 1px solid #6b6365;
            }
            QPushButton:hover { background-color: #5a5556; border-color: #c89f68; }
        """)
        close_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        self.content_layout.addLayout(btn_layout)

def launch_standalone_map_planner():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    apply_theme_to_app(app)
    window = MapPlannerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    launch_standalone_map_planner()
