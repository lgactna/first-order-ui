# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\Kisun\Desktop\first-order-ui\src\main\resources\base\windowui.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(821, 527)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.source_image_path_edit = QtWidgets.QLineEdit(self.groupBox_3)
        self.source_image_path_edit.setObjectName("source_image_path_edit")
        self.horizontalLayout_2.addWidget(self.source_image_path_edit)
        self.browse_image_button = QtWidgets.QPushButton(self.groupBox_3)
        self.browse_image_button.setObjectName("browse_image_button")
        self.horizontalLayout_2.addWidget(self.browse_image_button)
        self.verticalLayout_3.addWidget(self.groupBox_3)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.driving_video_path_edit = QtWidgets.QLineEdit(self.groupBox_2)
        self.driving_video_path_edit.setObjectName("driving_video_path_edit")
        self.horizontalLayout.addWidget(self.driving_video_path_edit)
        self.browse_video_button = QtWidgets.QPushButton(self.groupBox_2)
        self.browse_video_button.setObjectName("browse_video_button")
        self.horizontalLayout.addWidget(self.browse_video_button)
        self.verticalLayout_3.addWidget(self.groupBox_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout_3)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.generate_previews_button = QtWidgets.QPushButton(self.centralwidget)
        self.generate_previews_button.setObjectName("generate_previews_button")
        self.verticalLayout_2.addWidget(self.generate_previews_button)
        self.generate_and_save_button = QtWidgets.QPushButton(self.centralwidget)
        self.generate_and_save_button.setObjectName("generate_and_save_button")
        self.verticalLayout_2.addWidget(self.generate_and_save_button)
        self.change_paths_button = QtWidgets.QPushButton(self.centralwidget)
        self.change_paths_button.setObjectName("change_paths_button")
        self.verticalLayout_2.addWidget(self.change_paths_button)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 300))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_4.addWidget(self.groupBox)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 821, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Source Image"))
        self.browse_image_button.setText(_translate("MainWindow", "Browse..."))
        self.groupBox_2.setTitle(_translate("MainWindow", "Driving Video"))
        self.browse_video_button.setText(_translate("MainWindow", "Browse..."))
        self.generate_previews_button.setText(_translate("MainWindow", "Generate previews"))
        self.generate_and_save_button.setText(_translate("MainWindow", "Generate and save"))
        self.change_paths_button.setText(_translate("MainWindow", "Change checkpoint and config paths"))
        self.groupBox.setTitle(_translate("MainWindow", "Preview"))
