"""
@Author  :   xiyu
@File    :   voluteer.py
@Time    :   2020/7/25/22:37
@Desc    :
"""
DATA_PATH = r"./config/volunteer.json"
ICON_PATH = r"./config/icon.png"
QSS_PATH = r"./config/base.qss"
LOG_PATH = r"./config/volunteer.log"

import os
import sys
import json
import logging
import win32con
import win32clipboard as clip

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTreeWidget, QHeaderView, QGroupBox, \
    QSplitter, QTreeWidgetItem, QTabWidget, QTableView
from PyQt5.QtGui import QMouseEvent, QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView


class TreeWidget(QTreeWidget):

    def __init__(self):
        super(TreeWidget, self).__init__()

    def mousePressEvent(self, event):
        super(TreeWidget, self).mousePressEvent(event)
        return event.ignore()


class VolunteerGui(QMainWindow):

    def __init__(self, data, parent=None):
        super(VolunteerGui, self).__init__(parent)
        self.data = data
        try:
            self._init_ui()
        except Exception as e:
            logger_current.error("初始化异常：%s" % e)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setWindowTitle("填报专业--简易浏览器")

    def _init_ui(self):
        vlay_main = QVBoxLayout()
        vlay_main.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Horizontal)
        self._init_tree()
        self._init_content()

        vlay_main.addWidget(self.splitter)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(vlay_main)

    def eventFilter(self, obj, evt):
        if isinstance(evt, QMouseEvent) and isinstance(obj, TreeWidget):
            self.slot_show_selected_item()
        return False

    def _init_tree(self):
        self.file_tree_wgt = TreeWidget()
        self.file_tree_wgt.setItemsExpandable(True)

        self.file_tree_wgt.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.file_tree_wgt.header().setStretchLastSection(False)
        self.file_tree_wgt.header().close()

        self.file_tree_wgt.setMinimumSize(300, 570)
        self.file_tree_wgt.setMaximumWidth(450)
        self.file_tree_wgt.installEventFilter(self)

        self._load_data_2_tree()

        self.gbox_tree_view = QGroupBox()
        gbox_tree_view_vlay = QVBoxLayout()
        gbox_tree_view_vlay.addWidget(self.file_tree_wgt)
        self.gbox_tree_view.setLayout(gbox_tree_view_vlay)
        self.gbox_tree_view.setMaximumWidth(450)
        self.splitter.addWidget(self.gbox_tree_view)

    def _load_data_2_tree(self):
        self.file_name_layer = QTreeWidgetItem(self.file_tree_wgt)
        self.file_name_layer.__setattr__("node_name", "省份")
        self.file_name_layer.setText(0, "省份")
        self._init_tree_item(self.data, self.file_name_layer)

    def _init_tree_item(self, data, tree_wg):
        for item_name, item in data.items():
            tree_item = QTreeWidgetItem(tree_wg)
            parent_path = tree_wg.__getattribute__("node_name")
            tree_item.__setattr__("node_name", os.path.join(parent_path, item_name))
            tree_item.setText(0, item_name)

            if isinstance(item, dict):
                if "专业列表" in list(item.keys()):
                    item = item.get("专业列表")
                self._init_tree_item(item, tree_item)

    def _init_content(self):
        self.content_wgt = QWidget()
        self.content_wgt.setMinimumSize(500, 570)
        vlay_content = QVBoxLayout(self.content_wgt)

        self.content_tab_wg = QTabWidget()
        vlay_content.addWidget(self.content_tab_wg)

        self.gbox_content_view = QGroupBox()
        gbox_content_view_vlay = QVBoxLayout()
        gbox_content_view_vlay.setContentsMargins(0, 0, 0, 0)
        gbox_content_view_vlay.addWidget(self.content_wgt)
        self.gbox_content_view.setMinimumSize(500, 570)
        self.gbox_content_view.setLayout(gbox_content_view_vlay)
        self.splitter.addWidget(self.gbox_content_view)

    def slot_show_selected_item(self):
        item = self.file_tree_wgt.currentItem()
        try:
            if not item:
                return
            loc = item.__getattribute__("node_name")
            node_list = loc.split("\\")
            if len(node_list) <= 6:  # tab_view
                show_data = self.get_data_from_node_list(node_list[1:])
                self.load_data_2_table(node_list[-1], show_data)
            else:
                url = self.get_data_from_node_list(node_list[1:])
                self.load_data_2_web(url)
        except Exception as e:
            logger_current.error("点击项目树：%s, 异常：%s" % (item, e))

    def get_data_from_node_list(self, node_list):
        origin_data = self.data
        if len(node_list) >= 5:
            node_list.insert(4, "专业列表")
        for item in node_list:
            if origin_data.get(item):
                origin_data = origin_data.get(item)
        return origin_data

    def slot_jump_2_web_page(self, model_idx):
        url = None
        try:
            if self.tab_page.model().data(model_idx) == "跳转":
                col = model_idx.column()
                url = self.tab_page.model().data(model_idx.siblingAtColumn(col-1))
                if not url.startswith("http"):
                    addr = url.split(" ")[0]
                    clip.OpenClipboard()
                    clip.EmptyClipboard()
                    clip.SetClipboardData(win32con.CF_UNICODETEXT, addr)
                    clip.CloseClipboard()
                    url = "https://map.baidu.com"
                self.load_data_2_web(url)
        except Exception as e:
            logger_current.error("点击数据表跳转：%s, 异常：%s" % (url, e))

    def load_data_2_table(self, header_data, detail_data):
        try:
            if self.content_tab_wg.count() and self.content_tab_wg.widget(0).__getattribute__("attr") == "tab":
                if self.tab_page.model():
                    self.tab_page.model().deleteLater()
            else:
                self.tab_page = QTableView()
                self.tab_page.clicked.connect(self.slot_jump_2_web_page)
                self.tab_page.__setattr__("attr", "tab")
                self.tab_page.setAlternatingRowColors(True)
                self.content_tab_wg.addTab(self.tab_page, "数据表页")

            col_num = 3 if [x for x in list(detail_data.values()) if isinstance(x, str)] else 2
            row_num = len(detail_data)
            self.tab_page_model = QStandardItemModel(row_num, col_num)
            if col_num == 2:
                self.tab_page_model.setHorizontalHeaderLabels([header_data, "项目"])
            else:
                self.tab_page_model.setHorizontalHeaderLabels([header_data, "项目", "查看详情"])
            for col_idx in range(col_num):
                if col_idx == 0:  # 第一列类别
                    for row_idx in range(row_num):
                        self.tab_page_model.setItem(row_idx, col_idx, QStandardItem(list(detail_data.keys())[row_idx]))
                elif col_num == 2:  # 无第三列，第二列显示子项 标题内容
                    col2_content = [x for x in list(detail_data.values()) if isinstance(x, dict) and "标签" not in list(detail_data.keys()) and len(x) <= 10]
                    if col2_content:
                        for row_idx in range(row_num):
                            self.tab_page_model.setItem(row_idx, col_idx, QStandardItem("、".join(map(self.strip_colon, col2_content[row_idx].keys()))))
                    else:
                        school_count_list = []
                        for x in detail_data.values():
                            if not x:
                                school_count_list.append("")
                            else:
                                school_count_list.append(len(x))
                        for row_idx in range(row_num):
                            self.tab_page_model.setItem(row_idx, col_idx, QStandardItem(str(school_count_list[row_idx])))
                elif col_num == 3 and col_idx == 1:   # 有第三列，第二列显示详情
                    for row_idx in range(row_num):
                        school_content = list(detail_data.values())[row_idx]
                        if isinstance(school_content, dict):
                            school_content = "、".join(school_content.keys())
                        elif isinstance(school_content, list):
                            school_content = "、".join(school_content)
                        self.tab_page_model.setItem(row_idx, col_idx, QStandardItem(school_content))
                elif col_num == 3 and col_idx == 2:   # 有第三列，第三列跳转页面
                    for row_idx in range(row_num):
                        school_content = list(detail_data.keys())[row_idx]
                        if school_content not in ["专业列表", "标签", "优势专业"]:
                            self.tab_page_model.setItem(row_idx, col_idx, QStandardItem("跳转"))

            self.tab_page.setModel(self.tab_page_model)
            self.tab_page.setEditTriggers(QTableView.NoEditTriggers)
            self.tab_page.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.content_tab_wg.setCurrentIndex(0)
        except Exception as e:
            logger_current.error("更新数据表信息：%s, 异常：%s" % (header_data, e))

    def load_data_2_web(self, url):
        try:
            if self.content_tab_wg.count() > 1 and self.content_tab_wg.widget(1).__getattribute__("attr") == "web":
                self.web_page.load(QUrl(url))
                self.content_tab_wg.setCurrentIndex(1)
            else:
                self.web_page = QWebEngineView()
                self.web_page.__setattr__("attr", "web")
                self.web_page.load(QUrl(url))
                self.web_page.urlChanged.connect(self.slot_refresh_web_page)
                self.content_tab_wg.addTab(self.web_page, "网页搜索")
                self.content_tab_wg.setCurrentIndex(1)
        except Exception as e:
            logger_current.error("更新网页信息：%s, 异常：%s" % (url, e))

    def slot_refresh_web_page(self, url):
        logger_current.info("访问：%s" % url.url())

    @staticmethod
    def strip_colon(input_str):
        if input_str[-1] == "：":
            return input_str.rstrip("：")
        return input_str


def load_data_to_cache():
    with open(DATA_PATH, 'r', encoding='utf-8') as fr:
        data = json.loads(fr.read())
    return data


def set_ui_style(show_app):
    with open(QSS_PATH, 'r', encoding='utf-8') as f:
        qss_style = f.read()
        show_app.setStyleSheet(qss_style)


def log_mark(name):
    logger = logging.getLogger(name)
    return logger


handler1 = logging.FileHandler(LOG_PATH, "a", encoding="UTF-8")
# handler2 = logging.StreamHandler()
logging.basicConfig(level=logging.INFO, datefmt='%Y%m%d %H:%M:%S',
                    format='[%(asctime)s] [%(module)s] [line:%(lineno)d] [%(levelname)s] %(message)s ',
                    handlers=[handler1])
logger_current = log_mark(__name__)


if __name__ == '__main__':
    data = load_data_to_cache()
    app = QApplication(sys.argv)
    volunteer = VolunteerGui(data)
    volunteer.show()
    sys.exit(app.exec_())
