import configparser
import json
import os
import sys
import zipfile

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QTextBrowser, QDialog

from libfptr10 import IFptr

config = configparser.ConfigParser()
config.read('config.ini')

DRIVER_PATH = os.path.join(os.getcwd(), config['ATOL_DRIVER']['lib'])

fptr = IFptr(DRIVER_PATH)

settings = {
    IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
    IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_TCPIP,
    IFptr.LIBFPTR_SETTING_IPADDRESS: config['ATOL_DRIVER']['ip'],
    IFptr.LIBFPTR_SETTING_IPPORT: config['ATOL_DRIVER']['port'],
    IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200
}
fptr.setSettings(settings)

ndsType = {
        1: 'vat20',
        2: 'vat10',
        3: 'vat120',
        4: 'vat110',
        5: 'vat0',
        6: 'none'
}

payments_type = {
    False: 'electronically',
    True: 'cash'
}

taxation_system = {
    1: 'osn',
    2: 'usnIncome',
    3: 'usnIncomeOutcome',
    5: 'esn',
    6: 'patent'
}

sale_type = {
    False: 'sell',
    True: 'sellReturn'
}


def _on_file_drop(file_path):
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path.decode('ascii'), 'r') as zip_ref:
            for i in zip_ref.namelist():
                if i.startswith('cheque'):
                    cheque = i
            zip_ref.extract(member=cheque, path='./ofd_jsons/')
        with open('./ofd_jsons/'+cheque, 'r', encoding='UTF-8') as cheque:
            json_cheque = cheque.read()
        json_cheque = json.loads(json_cheque)
        return json_cheque
    else:
        return "need zip"


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DoubleCheck")
        self.setWindowIcon(QtGui.QIcon('favicon.ico'))
        self.resize(365, 630)
        self.setAcceptDrops(True)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setEnabled(True)
        self.textBrowser.setGeometry(QtCore.QRect(10, 10, 341, 531))
        self.textBrowser.setStyleSheet("")
        self.textBrowser.setReadOnly(True)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setAcceptDrops(True)
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setGeometry(QtCore.QRect(10, 550, 81, 20))
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.checkBox.setEnabled(False)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(160, 590, 90, 28))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(80, 550, 170, 28))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setToolTip('Бета')
        self.pushButton_2.setEnabled(False)
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(260, 550, 97, 49))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.radioButton = QtWidgets.QRadioButton(self.widget)
        self.radioButton.setObjectName("radioButton")
        self.radioButton.setEnabled(False)
        self.verticalLayout.addWidget(self.radioButton)
        self.radioButton_2 = QtWidgets.QRadioButton(self.widget)
        self.radioButton_2.setObjectName("radioButton_2")
        self.radioButton_2.setEnabled(False)
        self.verticalLayout.addWidget(self.radioButton_2)
        self.setCentralWidget(self.centralwidget)
        self.notify = QDialog(self)
        self.notify_layout = QtWidgets.QGridLayout(self.notify)
        self.notify.resize(100, 50)
        self.notify_label = QtWidgets.QLabel(self.notify)
        self.notify_layout.addWidget(self.notify_label)
        self.clipboard = QApplication.clipboard()
        self.retranslate()

    def retranslate(self):
        _translate = QtCore.QCoreApplication.translate
        self.textBrowser.setPlaceholderText(_translate("MainWindow", "ZIP файл..."))
        self.checkBox.setText(_translate("MainWindow", "Возврат"))
        self.pushButton.setText(_translate("MainWindow", "Копировать"))
        self.radioButton.setText(_translate("MainWindow", "Наличные"))
        self.radioButton_2.setText(_translate("MainWindow", "Карта"))
        self.pushButton_2.setText(_translate("MainWindow", "Отправить на тестовую кассу"))
        self.some_functions()

    def some_functions(self):
        self.checkBox.clicked.connect(lambda: self.sale_type())
        self.radioButton.toggled.connect(lambda: self.payment_type())
        self.pushButton_2.clicked.connect(lambda: self.send_json())
        self.pushButton.clicked.connect(lambda: self.clipboard.setText(self.textBrowser.toPlainText()))

    def sale_type(self):
        self.receipt['type'] = sale_type.get(self.checkBox.isChecked())
        self.textBrowser.setText(json.dumps(self.receipt, ensure_ascii=False, indent=3).encode('UTF-8').decode())

    def payment_type(self):
        self.receipt['payments'][0]['type'] = payments_type.get(self.radioButton.isChecked())
        self.textBrowser.setText(json.dumps(self.receipt, ensure_ascii=False, indent=3).encode('UTF-8').decode())

    def send_json(self):
        fptr.open()
        if fptr.isOpened() == 1:
            fptr.setParam(fptr.LIBFPTR_PARAM_JSON_DATA, self.textBrowser.toPlainText())
            if fptr.validateJson() == 0:
                self.notify_label.setText('json прошёл проверку, закрой окно для печати')
                self.notify.exec_()
                fptr.setParam(fptr.LIBFPTR_PARAM_JSON_DATA, self.textBrowser.toPlainText())
                fptr.processJson()
                result = fptr.getParamString(IFptr.LIBFPTR_PARAM_JSON_DATA)
                self.notify_label.setText(result)
                self.notify.exec_()
            else:
                self.notify_label.setText('Ошибка в json задании')
                self.notify.exec_()
        else:
            self.notify_label.setText('Касса недоступна')
            self.notify.exec_()
        fptr.close()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        ofd_json = _on_file_drop(files[0].encode())
        if ofd_json == 'need zip':
            self.textBrowser.setText('Нужен zip файл JSON чека')
        else:
            self.gen_json(ofd_json)

    def gen_json(self, ofd_json):
        self.checkBox.setEnabled(True)
        self.radioButton.setEnabled(True)
        self.radioButton_2.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.receipt = {
            "ignoreNonFiscalPrintErrors": False,
            "items": [],
            "operator": {"name": ''},
            "payments": [
                {
                    "sum": 0.0,
                    "type": "electronically"
                }

            ],
            "taxationType": "osn",
            "type": "sellReturn"
        }
        for i in ofd_json['items']:
            self.receipt['items'].append({
                "amount": float(str(i['sum']).zfill(3))/100,
                "infoDiscountAmount": 0,
                "name": i['name'],
                "paymentMethod": "fullPayment",
                "paymentObject": "commodity",
                "price": float(str(i['price']).zfill(3))/100,
                "quantity": i['quantity'],
                "tax": {
                    "type": ndsType.get(i['nds'])
                },
                "type": "position"
            })
        self.receipt['operator']['name'] = ofd_json['operator']
        if ofd_json['cashTotalSum'] > ofd_json['ecashTotalSum']:
            self.receipt['payments'][0]['sum'] = float(str(ofd_json['cashTotalSum']).zfill(3))/100
            self.receipt['payments'][0]['type'] = payments_type[True]
            self.radioButton.setChecked(True)
        elif ofd_json['ecashTotalSum'] > ofd_json['cashTotalSum']:
            self.receipt['payments'][0]['sum'] = float(str(ofd_json['ecashTotalSum']).zfill(3))/100
            self.receipt['payments'][0]['type'] = payments_type[False]
            self.radioButton_2.setChecked(True)
        else:
            self.textBrowser.setText('Не удалось определить тип оплаты')
        self.receipt['taxationType'] = taxation_system.get(ofd_json['taxationType'])
        self.receipt['type'] = sale_type.get(self.checkBox.isChecked())
        self.textBrowser.setText(json.dumps(self.receipt, ensure_ascii=False, indent=3).encode('UTF-8').decode())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MainWidget()
    ui.show()
    sys.exit(app.exec_())
