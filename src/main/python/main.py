import sys
import imageio
from imageio.plugins.ffmpeg import get_exe as get_ffmpeg_exe
from PyQt5 import QtCore, QtGui, QtWidgets
from fbs_runtime.application_context.PyQt5 import ApplicationContext
#------
from windowui import Ui_MainWindow
from demo_functs import generate_and_save
#------
appctxt = ApplicationContext()
try:
    checkpoint_path = appctxt.get_resource('vox-adv-cpk.pth.tar')
except FileNotFoundError:
    checkpoint_path = None
#config_path = 'config/vox-256.yaml'
config_path = appctxt.get_resource('vox-256.yaml')
#endregion imports

##EEEE

class ApplicationWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    '''The main window. Instantiated once.'''
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("first-order-model-ui")

        self.browse_image_button.clicked.connect(self.open_source_image)
        self.browse_video_button.clicked.connect(self.open_driving_video)
        self.generate_and_save_button.clicked.connect(self.save_output)

        try:
            get_ffmpeg_exe()
            print("User has ffmpeg exe.")
        except imageio.core.fetching.NeedDownloadError:
            print("User doesn't have ffmpeg exe. Needs to be downloaded.")


    def open_source_image(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Source Image",
                                                    QtCore.QDir.currentPath(),
                                                    "PNG (*.png);;All Files (*)")
        if file_name:
            self.source_image_path_edit.setText(file_name)
    def open_driving_video(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Driving Video",
                                                    QtCore.QDir.currentPath(),
                                                    "MP4 (*.mp4);;All Files (*)")
        if file_name:
            self.driving_video_path_edit.setText(file_name)
    def save_output(self):
        if not self.source_image_path_edit.text() or not self.driving_video_path_edit.text():
            print("no")
            return None
        initial_path = QtCore.QDir.currentPath() + '/untitled.mp4'
        savepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", initial_path,
               "MP4 (*.mp4);;All Files (*)")
        imgpath = self.source_image_path_edit.text()
        videopath = self.driving_video_path_edit.text()
        try:
            generate_and_save(imgpath, videopath, savepath, config_path, checkpoint_path)
        except imageio.core.fetching.NeedDownloadError:
            imageio.plugins.ffmpeg.download()

class AppContext(ApplicationContext):
    '''fbs requires that one instance of ApplicationContext be instantiated.
    This represents the app window.'''
    def run(self):
        application_window = ApplicationWindow()
        application_window.show()
        return self.app.exec_()

if __name__ == '__main__':
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)
