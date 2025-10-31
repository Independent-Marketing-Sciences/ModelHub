from PySide6.QtWidgets import (QStyledItemDelegate)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QRect

# Activated in sidemenu config with: self.sideMenu.setItemDelegate(IconAboveTextDelegate())

class IconAboveTextDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        rect = QRect(option.rect)
        icon: QIcon = index.data(Qt.DecorationRole)
        text: str = index.data(Qt.DisplayRole)

        icon_size = option.decorationSize
        pixmap = icon.pixmap(icon_size)
        text_rect = QRect(rect.left(), rect.top() + icon_size.height() + 5, rect.width(), rect.height() - icon_size.height())

        # Center the icon in the item rectangle
        icon_x = rect.center().x() - icon_size.width() // 2
        icon_y = rect.top() + 5
        painter.drawPixmap(QRect(icon_x, icon_y, icon_size.width(), icon_size.height()), pixmap)

        # Draw the text below the icon
        painter.drawText(text_rect, Qt.AlignCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        icon_size = option.decorationSize
        size.setHeight(size.height() + icon_size.height() + 5)
        return size
