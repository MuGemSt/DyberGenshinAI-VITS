# coding:utf-8
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QLabel
from qfluentwidgets import ScrollArea, ExpandLayout
from .dashboard_widgets import ChatCard
import DyberPet.settings as settings

basedir = settings.BASEDIR
module_path = os.path.join(basedir, "DyberPet/Dashboard/")


class chatInterface(ScrollArea):
    """Character animations management interface"""
    
    changePet = Signal(name="changePet")
    
    def __init__(self, sizeHintdb: tuple[int, int], parent=None):
        super().__init__(parent=parent)
        self.setObjectName("chatInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.panelLabel = QLabel(self.tr("AI 助手"), self)
        self.chatBot = ChatCard(sizeHintdb, self.scrollWidget)
        self.__initWidget()
        self.__connectSignalToSlot()

    def __initWidget(self):
        # self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 75, 0, 20)
        self.setWidget(self.scrollWidget)
        # self.scrollWidget.resize(1000, 800)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        # self.__connectSignalToSlot()

    def __initLayout(self):
        self.panelLabel.move(60, 20)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(70, 10, 70, 0)

        # 将 QTextEdit 和 QPushButton 添加到布局中
        self.expandLayout.addWidget(self.chatBot)

    def __setQss(self):
        """set style sheet"""
        self.scrollWidget.setObjectName("scrollWidget")
        self.panelLabel.setObjectName("panelLabel")

        theme = "light"  # if isDarkTheme() else 'light'
        with open(
            os.path.join(
                basedir, "res/icons/Dashboard/qss/", theme, "status_interface.qss"
            ),
            encoding="utf-8",
        ) as f:
            self.setStyleSheet(f.read())

    def __connectSignalToSlot(self):
        """connect signal to slot"""
        self.changePet.connect(self.chatBot._changePet)

    def _changePet(self):
        self.changePet.emit()
