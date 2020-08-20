#!/usr/bin/env python

#region licensing

#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

#This program is a modified version of the Scribble example.
#The notice above is kept as a result.

#endregion licensing

#region imports

#https://stackoverflow.com/questions/3615125/should-wildcard-import-be-avoided
#will change to qualified imports later
import sys
import webbrowser
import json
import csv
from PyQt5 import QtCore, QtGui, QtWidgets, QtPrintSupport
from fbs_runtime.application_context.PyQt5 import ApplicationContext
#------
from rectmap import Ui_MainWindow
from advexport import Ui_AdvExportWindow
from fstringdialog import Ui_StringDialog
#------
appctxt = ApplicationContext()
prefpath = appctxt.get_resource('preferences.json')
default_prefpath = appctxt.get_resource('default.json')
#endregion imports

'''todo (vaguely in this order):
        done - full settings implementation (logic)
        done - clear field button
        done - forced resize option (define custom canvas area, preload)
        done - resize on image load (includes settings logic: crop if big, stretch if small, default otherwise)
        done - resize logic post image load
        done - try qdoublevalidator/qvalidator for the conversion handles
        done - conversion table
        done - qualify pyqt5 calls (not "from pyqt5.a import b, c, d" but "from pyqt5 import a, b, c, d" and use "a.aa" calls)
        done - simple csv export
        done - fstring export
        done - "all" option on simple csv export
        done - advanced csv export (old: custom ordering of csv with qlistwidget)
        done - custom fields (but not the fact they get deleted, which is part of the table overhaul)
        done - custom fstring identifiers
        done - save image
        done - update coordinate table upper-left labels on draw finish
        ^excludes overlap functionality
        done - highlight row on draw finish (because it already does that)
        done - disable "change color" button if disabled (because color is now mandatory)
        done - click row (or row element) to show rectangle info
        done - right-click custom context menu
        done - define behavior for changing custom colors (warn that custom colors will be discarded if colors are enabled and then disabled)

        done - edit table values and update accordingly
        done - csv import (data must be ordered x1, y1, x2, y2, custom fields, ..., converted values.)
        ^although it's really bad lol
        make undo work to not just delete rectangles, but undo other actions (or drop entirely)
        table validators/restrict editing
        https://stackoverflow.com/questions/37621753/how-validate-a-cell-in-qtablewidget
        docstring standards conformity
        other pylint stuff (probably in a fork)

        dropped = maybe sometime later

        dropped - stop deleting data entered in custom fields on each table update
        ^requires the rework where the table stops being the actual container instead of just a representation
        dropped - fix overlap system such that the label is real-time updatable
        ^this probably requires the logic-ui overhaul since overlap is calculated per-rectangle
        ^i don't think it has any real value at the moment anyways
        dropped - click row (or row element) to highlight associated rectangle in some way
        ^start a timer that regularly changes the alpha on these rectangles, as rect[n][1] is a qcolor of rgba; change the a component
        ^upon the row being changed, immediately force the alpha to be 255, loading from an array of the currently flashing rects

        rewrite = when logic and ui are separated

        really what ought to happen is the table SHOULD NOT be the actual container, but merely a user-viewable representation
        even that would go a long way...

        rewrite -- unbreak the overlap system (which doesn't even work correctly in its current state)
        rewrite -- disable live overlap calculation in table if live table is disabled (which really just means fix the overlap system)
        rewrite -- unbreak the draw system (don't redraw every single element on each update)
        rewrite -- unbreak the table system (use more and different signals)
        

        Note: eraseRect via QPainter erases the area *inside* the rectangle defined, same as filling a borderless rectangle with white;
        as such, unbreaking the draw system might not be as reasonable as currently thought...
'''

'''undo actions: (format: action | [old_data])
*note: fstring edit has its own undo handler, and will undo independently
of a ctrl+z so long as the user is focused on that input box
change-preference | [preference, value]
change-table-data | [[row, column], value]
add-custom-field | <NONE> (delete last implied)
delete-rectangle | [[rectangle_object, <index in drawing_area.rects>],...]
open-image | old_filepath
change-individual-color | [[drawing_area.rects index, qcolor object], ...]
draw-rectangle | <NONE> (delete last implied)
change-conversion-handles | [x1,y1,x2,y2]

change "rectangle object" to be an array of [rect_object, qcolor]?

push each one of these to an array of n max length
also make a setting of such
don't add a preference change of the undo array length to the array itself
so we can just avoid the issues that are associated with that lol
'''

#stylistic note: i've opted to use snake_case for most parts of this program
#there are some things that remain camelCase, as it felt more natural for me to retain
#Qt-like style - the custom signals are an example

#also yes this program is in great need of a code review and refactoring
#apparently a single python script handling both graphics and logic is :thonk:
#https://softwareengineering.stackexchange.com/questions/127245/how-can-i-separate-the-user-interface-from-the-business-logic-while-still-mainta
#gsearch: "separate business logic from ui"
#https://softwareengineering.stackexchange.com/questions/336915/should-i-put-ui-and-logic-in-separate-classes
#this will be done soontm in a different branch

def get_prefs(source="user"):
    '''Get `data` from either preferences.json or default.json.
    `source` is a `str`, either `"user"` or `"default"`. The default is `"user"`.\n
    Using `"user"` returns the local preferences from preferences.json.
    Using `"default"` returns the default preferences from default.json.\n
    Returns a standard Python dict.'''
    if source == "user":
        pref_file = open(prefpath)
        data = json.load(pref_file)
        pref_file.close()
        return data
    elif source == "default":
        pref_file = open(default_prefpath)
        data = json.load(pref_file)
        pref_file.close()
        return data

def write_prefs(data):
    '''Write `data` to preferences.json with 4-space indents.
    `data` is a standard Python dict, likely the result of get_prefs().'''
    pref_file = open(prefpath, "w+") #write and truncate
    pref_file.write(json.dumps(data, indent=4))
    pref_file.close()

class CanvasArea(QtWidgets.QWidget):
    '''The primary canvas on which the user draws rectangles.
    Note that CanvasArea is referred to as "the canvas" across (most) docstrings and comments.'''
    #these are custom signals that will not work if placed in __init__
    #they must be class variables/attributes declared here
    posChanged = QtCore.pyqtSignal(int, int)
    sizeChanged = QtCore.pyqtSignal()
    #will be used later
    rectangleStarted = QtCore.pyqtSignal()
    rectangleUpdated = QtCore.pyqtSignal(QtCore.QRect)
    rectangleFinished = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(CanvasArea, self).__init__(parent)

        #instance attributes...
        #self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.scribbling = False
        self.image = QtGui.QImage()
        self.starting_point = QtCore.QPoint()
        self.end_point = QtCore.QPoint()
        #if colors will be implemented, then the structure will need to be modified
        #perhaps each element can be an array of [QtCore.QRect, (r,g,b)]
        self.rects = []
        self.loaded_image_path = None
        self.loaded_image_size = None
        self.current_color = QtGui.QColor(0, 0, 255, 255)

        #A QtWidgets.QWidget normally only receives mouse move events (mouseMoveEvent) when a mouse button is being pressed.
        #This sets it to always receive mouse events, regardless.
        self.setMouseTracking(True)

        self.settings = {
            "active_redraw": True,
            "active_coordinates": False,
            "crop_image": False, #crop large images
            "stretch_image": False, #stretch small images
            "keep_ratio": True, #preserve aspect ratio on stretch
            "default_width": 1,
            "default_color": QtGui.QColor(0, 0, 255, 255)
        }
    def open_image(self, file_name):
        '''Sets the image at `file_name` to be the canvas background.
        It will then resize the canvas as needed and redraw rectangles.'''
        self.loaded_image_path = file_name
        self.calculate_sizes()
        self.draw_all_rects()
        '''
        loadedImage = QtGui.QImage()
        if not loadedImage.load(file_name):
            return False

        #returns the maximum height and width given the two sizes
        new_size = loadedImage.size().expandedTo(self.size())
        #also see qsize.scale()
        self.resize_image(loadedImage, new_size)
        self.image = loadedImage
        self.update()
        return True
        '''

    def calculate_sizes(self):
        '''Determine what size the image should be, and if needed, resize the canvas.'''
        image = QtGui.QImage()
        image.load(self.loaded_image_path)

        image_size = image.size()
        canvas_size = self.size()

        if self.settings['crop_image'] and (image_size.width() > canvas_size.width() or image_size.height() > canvas_size.height()):
            self.loaded_image_size = image_size
        elif self.settings['stretch_image'] and (image_size.width() < canvas_size.width() or image_size.height() < canvas_size.height()):
            if self.settings['keep_ratio']:
                #scale the size to the largest aspect ratio-preserving size within canvas_size.width() and canvas_size.height()
                image_size.scale(canvas_size.width(), canvas_size.height(), QtCore.Qt.KeepAspectRatio)
                self.loaded_image_size = image_size
            else:
                self.loaded_image_size = canvas_size
        else:
            #if there aren't any special settings, just set the canvas to be the size of the loaded image
            self.setFixedSize(image_size)
            self.sizeChanged.emit()
            self.loaded_image_size = image_size

    def save_image(self, file_name, file_format):
        '''Save the canvas as the specified file name in the specified format.
        Also resize the final image based on the current canvas size - fixes
        weird whitespace if a larger image was loaded before the current one.'''
        visible_image = self.image

        print(self.size())
        print(visible_image.size())

        #the problem with using this function to resize image to the
        #"correct" size - that is, the size of the canvas - is that
        #the way i crop the image with setFixedSize() does make the canvas
        #the correct size, but it doesn't actually change the size of the image element
        #itself
        #so when we load a large image in and then a smaller image, there
        #would be a large amount of whitespace - using copy() allows us to fix this
        #there are other curious implications of this, particularly wrt drawing
        #rectangles "off-screen"; they're cropped as a result of the final image's
        #size being dependent on the visible area
        #self.resize_image(visible_image, self.size())

        #https://stackoverflow.com/questions/7010611/how-can-i-crop-an-image-in-qt
        final = visible_image.copy(0, 0, self.size().width(), self.size().height()) 

        #if visible_image.save(file_name, file_format):
        if final.save(file_name, file_format):
            return True
        else:
            return False

    def clear_image(self):
        '''Clear the canvas.
        In the future, this might be changed such that the opened image is drawn here.'''
        self.image.fill(QtGui.qRgb(255, 255, 255))
        self.update()

    def undo_last(self):
        '''Delete the most recent rectangle and redraw the canvas.'''
        self.clear_image()
        del self.rects[-1]
        self.draw_all_rects()
        #we also need to update the table here
        #will be done as part of the more expansive undo rework

    def mousePressEvent(self, event): # pylint: disable=invalid-name
        '''What happens when the user begins drawing a rectangle. Requires that
        the left mouse button be clicked for a rectangle to be drawn.'''
        if event.button() == QtCore.Qt.LeftButton:
            self.starting_point = event.pos()
            self.scribbling = True
            self.rectangleStarted.emit()

    def mouseMoveEvent(self, event): # pylint: disable=invalid-name
        '''What happens when the user moves their mouse within the canvas area.
        Always emits posChanged to update the cursor's current pixel position. If
        drawing a rectangle, update a real-time view of the rectangle and its coordinates
        if enabled by the user.'''
        self.posChanged.emit(event.pos().x(), event.pos().y())
        if (event.buttons() & QtCore.Qt.LeftButton) and self.scribbling:
            if self.settings['active_redraw']:
                self.rects.append([QtCore.QRect(self.starting_point, event.pos()), "Default"])
                self.draw_all_rects()
                if self.settings['active_coordinates']:
                    self.rectangleUpdated.emit(self.rects[-1][0])
                del self.rects[-1]

    def mouseReleaseEvent(self, event): # pylint: disable=invalid-name
        '''What happens when the user stops drawing, releasing the left mouse button.
        Adds the final rectangle (based on the point of mouse release) and redraws as necessary.'''
        if event.button() == QtCore.Qt.LeftButton and self.scribbling:
            self.end_point = event.pos()
            self.scribbling = False
            self.rects.append([QtCore.QRect(self.starting_point, self.end_point), "Default"])
            #here we should also add this data to the table and update it
            self.rectangleFinished.emit()
            self.draw_all_rects()

    def paintEvent(self, event): # pylint: disable=invalid-name
        painter = QtGui.QPainter(self)
        dirty_rect = event.rect()
        painter.drawImage(dirty_rect, self.image, dirty_rect)

    def resizeEvent(self, event): # pylint: disable=invalid-name
        if self.width() > self.image.width() or self.height() > self.image.height():
            new_width = max(self.width() + 128, self.image.width())
            new_height = max(self.height() + 128, self.image.height())
            self.resize_image(self.image, QtCore.QSize(new_width, new_height))
            self.update()

        super(CanvasArea, self).resizeEvent(event)

    def draw_all_rects(self):
        '''Redraw all rectangles, iterating over each rectangle object in self.rects.'''
        ####
        '''
        is very inefficient because we don't just update the thing - no, we redraw *everything*
        a better way of doing this (i believe) is to use QGraphicsView since we don't need to store (and redraw) elements - it's done for us

        that said, i wasn't able to implement a proper rectangle deletion function properly without using this "array -> draw everything method" w/ QtGui.QPainter
        it's also a good deal easier to mesh with the table widget and export it into a format i understand

        so maybe one day i'll refactor this but for now this is good enough without absolutely shredding through resources
        '''
        self.clear_image()
        painter = QtGui.QPainter(self.image)

        #at this point we can redraw the image
        if self.loaded_image_path:
            bg_img = QtGui.QPixmap(self.loaded_image_path)
            #because of the way this is set up right now - to use a qrect of x size and place an image in it
            #we don't directly change the size of the image
            #so the instance attribute "loaded_image_size" is used instead
            painter.drawPixmap(QtCore.QRect(0, 0, self.loaded_image_size.width(), self.loaded_image_size.height()), bg_img)
        #drawing area has no border so use of frameGeometry should not be necessary?
        #painter.drawPixmap(QtCore.QRect(0,0,self.frameGeometry().width(),self.frameGeometry().height()),bg_img)
        for rect in self.rects:
            if rect[1] == "Default" and self.current_color != self.settings['default_color']:
                self.current_color = self.settings['default_color']
            elif rect[1] != "Default" and self.current_color != rect[1]:
                self.current_color = rect[1]
            painter.setPen(QtGui.QPen(self.current_color, self.settings['default_width'], QtCore.Qt.SolidLine,
                            QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
            painter.drawRect(rect[0])
        self.update()

    def resize_image(self, image, new_size):
        if image.size() == new_size:
            return

        new_image = QtGui.QImage(new_size, QtGui.QImage.Format_RGB32)
        new_image.fill(QtGui.qRgb(255, 255, 255))
        painter = QtGui.QPainter(new_image)
        painter.drawImage(QtCore.QPoint(0, 0), image)
        self.image = new_image

    def print_(self):
        '''Handles canvas printing via QtPrintSupport.QPrintDialog.'''
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)

        print_dialog = QtPrintSupport.QPrintDialog(printer, self)
        if print_dialog.exec_() == QtPrintSupport.QPrintDialog.Accepted:
            painter = QtGui.QPainter(printer)
            rect = painter.viewport()
            size = self.image.size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.image.rect())
            painter.drawImage(0, 0, self.image)
            painter.end()

    #will probably just remove these later since we can just get drawing_area.settings['default_color'] and so on if we ever need these values...
    #but until then, to differentiate the method and the value, it stays camelcase
    #might just keep them for clarity

    def penColor(self): # pylint: disable=invalid-name
        '''Returns the default current pen color.'''
        return self.settings['default_color']

    def penWidth(self):  # pylint: disable=invalid-name
        '''Returns the current default pen width.'''
        return self.settings['default_width']

    #probably same with these
    def set_pen_color(self, new_color):
        '''Set a new default pen color for the canvas.'''
        self.settings['default_color'] = new_color

    def set_pen_width(self, new_width):
        '''Set a new default pen width for the canvas.'''
        self.settings['default_width'] = new_width

class TableCoordinateDelegate(QtWidgets.QItemDelegate):
    #https://stackoverflow.com/questions/37621753/how-validate-a-cell-in-qtablewidget
    #https://forum.qt.io/topic/81918/qtableview-cell-validation-specific-validator-for-a-column/3
    def createEditor(self, parent, option, index):
        spinbox = QtWidgets.QSpinBox(parent)
        #i see many spaghetti coming from this
        #but also i seriously doubt there will be need for 2 billion pixels...
        spinbox.setMaximum(2147483647)
        spinbox.setMinimum(-2147483648)
        return spinbox

class ApplicationWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    '''The main window. Instantiated once.'''
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("RectangleMappingTool")
        '''
        See https://stackoverflow.com/questions/35185113/configure-qtwidgets.qwidget-to-fill-parent-via-layouts.
        this appears to be the same issue in which this new widget is initialized to a 100px by 25px area
        so we create a new grid layout and place drawing_area into it
        this also affords us some flexibility if we ever want to hide drawing_area and place something different in container_left
        ---
        in order for a qscrollarea to work, the child (here self.scrollAreaWidgetContents) must have its own layout
        however, obviously a layout will auto-resize elements inside it
        so in order to account for this, we will manually set the minimum size of the newly-created drawing area
        thus forcing it to be that size and give us the scroll bars
        the above is what i understood from a bunch of qt forum and stackoverflow posts
        although the docs say that a standard resize() will be respected
        i could not get it to do that
        '''
        #region Canvas initialization
        #I decided to not rename "drawing_area" to "canvas_area" for clarity reasons
        #there is no difference between "canvas_area" and "CanvasArea" when set out loud
        #so they'll stey different
        self.drawing_area = CanvasArea(self.scrollAreaWidgetContents)
        self.container_left.setWidgetResizable(True)
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.drawing_area)
        left_layout.setAlignment(QtCore.Qt.AlignHCenter)
        self.scrollAreaWidgetContents.setLayout(left_layout)
        #we will need to set a signal later that resizes this widget based on a given background image
        #(or we just directly resize it after calling open())
        self.drawing_area.setFixedSize(400, 300)
        self.drawing_area.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor)) #make this responsive to a setting

        self.drawing_area.rectangleFinished.connect(self.update_tables)
        self.drawing_area.posChanged.connect(self.update_coords)
        self.drawing_area.sizeChanged.connect(self.update_size_text)
        self.drawing_area.rectangleStarted.connect(self.update_on_rect_start)
        self.drawing_area.rectangleUpdated.connect(self.update_rect_labels_active)
        self.drawing_area.rectangleFinished.connect(self.update_on_rect_finish)
        #endregion

        #region Action signals and slots
        self.actionUndo.triggered.connect(self.undo)
        self.actionPen_Color.triggered.connect(self.change_default_pen_color)
        self.actionPen_Width.triggered.connect(self.change_pen_width)
        self.actionGitHub_Repository.triggered.connect(self.open_github)
        self.actionAbout.triggered.connect(self.about)
        self.actionOpen_image.triggered.connect(self.open_image)
        self.actionClear_all.triggered.connect(self.clear_all)
        self.actionSave_image_as.triggered.connect(self.save_file)
        self.actionImport_coordinates.triggered.connect(self.csv_import)
        self.actionExport_coordinates.triggered.connect(lambda: self.tabWidget.setCurrentIndex(2))
        #endregion

        #region Tab 1: Coordinate Table
        #accept only ints; see tabledelgate definition
        delegate = TableCoordinateDelegate()
        for i in range(0, 4):
            self.table_widget.setItemDelegateForColumn(i, delegate)
        self.add_custom_button.clicked.connect(self.add_custom_field)
        #below is set in the ui file already
        #self.table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_table_menu)
        #much like in the advanced export window, this signal seems to be emitted *before*
        #the selection is registered to have changed
        #so we do the 10 ms thing again, which makes me suspicious i'm doing something wrong
        #probably the order in which things are processed
        self.table_widget.currentCellChanged.connect(lambda: QtCore.QTimer.singleShot(10, self.update_rect_labels))
        #see todo notes above
        self.table_widget.itemChanged.connect(self.update_data_from_item_change)
        self.change_rect_color_button.clicked.connect(self.recolor_selected_rectangles)
        self.delete_rect_button.clicked.connect(self.delete_selected_rectangles)
        #endregion

        #region Tab 2: Conversion
        #restricts the entry to a double with one decimal and the letter "e"
        #there is also a second process to ensure the values are actually valid python floats
        self.conv_x1_edit.setValidator(QtGui.QDoubleValidator())
        self.conv_y1_edit.setValidator(QtGui.QDoubleValidator())
        self.conv_x2_edit.setValidator(QtGui.QDoubleValidator())
        self.conv_y2_edit.setValidator(QtGui.QDoubleValidator())
        self.set_handles_button.clicked.connect(self.set_conversion_values)
        self.toggle_show_conv_button.clicked.connect(self.toggle_conversion_info)
        #endregion

        #region Tab 3: Export Data
        #create a radio group that makes figuring out these buttons' states easier
        #note that there is no actual representation of them on-screen
        self.radio_group = QtWidgets.QButtonGroup()
        for radio_button in self.tab_3.findChildren(QtWidgets.QRadioButton):
            self.radio_group.addButton(radio_button)
        self.radio_group.buttonClicked.connect(self.update_csv_export_text)
        self.export_csv_button.clicked.connect(self.simple_csv_export)
        self.export_advanced_button.clicked.connect(self.advanced_csv_export)
        self.export_txt_button.clicked.connect(self.fstring_export)
        self.open_external_fstring.clicked.connect(self.new_fstring_window)
        #technically this connects us to a signal not exclusive to just tab 3
        #but i wasn't able to find a way to connect to only tab 3, as it's apparently
        #a generic qwidget, not a qtabbar
        self.tabWidget.tabBarClicked.connect(self.update_inline_valid_vars)
        #endregion

        #region Tab 4: Settings
        self.set_color_button.clicked.connect(self.change_default_pen_color)
        self.set_width_button.clicked.connect(self.change_pen_width)
        self.reset_settings_button.clicked.connect(self.reset_prefs)
        #fun fact: this validator seems to prevent blank values from emitting editingFinished
        self.conv_round_edit.setValidator(QtGui.QIntValidator())
        self.conv_round_edit.editingFinished.connect(lambda: self.change_preference("conv_round", int(self.conv_round_edit.text())))
        self.left_identifier_edit.editingFinished.connect(lambda: self.change_preference("left_identifier", self.left_identifier_edit.text()))
        self.right_identifier_edit.editingFinished.connect(lambda: self.change_preference("right_identifier", self.right_identifier_edit.text()))

        #im not sure if there's a better way to do this lol
        #pylint is fuming but my screen is wide enough so ill change it later
        self.active_redraw_checkbox.toggled.connect(lambda: self.change_preference("active_redraw", self.active_redraw_checkbox.isChecked()))
        self.active_coordinates_checkbox.toggled.connect(lambda: self.change_preference("active_coordinates", self.active_coordinates_checkbox.isChecked()))
        self.active_overlaps_checkbox.toggled.connect(lambda: self.change_preference("active_overlaps", self.active_overlaps_checkbox.isChecked()))
        self.check_overlaps_checkbox.toggled.connect(lambda: self.change_preference("check_overlaps", self.check_overlaps_checkbox.isChecked()))
        self.crop_image_checkbox.toggled.connect(lambda: self.change_preference("crop_image", self.crop_image_checkbox.isChecked()))
        self.stretch_image_checkbox.toggled.connect(lambda: self.change_preference("stretch_image", self.stretch_image_checkbox.isChecked()))
        self.use_crosshair_checkbox.toggled.connect(lambda: self.change_preference("use_crosshair", self.use_crosshair_checkbox.isChecked()))
        self.keep_ratio_checkbox.toggled.connect(lambda: self.change_preference("keep_ratio", self.keep_ratio_checkbox.isChecked()))

        self.set_canvas_size_button.clicked.connect(self.change_canvas_size)
        #endregion

        #region Instance attributes
        #Technically some of these don't need to be here and can instead be in drawing_area
        #but I found it easier to refer to these values here rather than doing it across classes
        self.settings = {
            "active_redraw":True,
            "active_coordinates":False,
            "active_overlaps":False, #this setting is broken and needs to be fixed along with the overlap stuff
            "check_overlaps":True,
            "crop_image":False,
            "stretch_image":False,
            "keep_ratio":True,
            "use_crosshair":True,
            "default_color":[0, 0, 255, 255],
            "default_width":1,
            "conv_round":6,
            "left_identifier":"{",
            "right_identifier":"}",
            "max_undo_actions": 25
        }

        self.conversion_values = {
            "x1":None,
            "y1":None,
            "x2":None,
            "y2":None
        }

        self.custom_column_headers = []
        self.undo_queue = []
        '''
        self.flash_timer = QtCore.QTimer()
        self.flash_timer.start(1000)
        self.flash_timer.timeout.connect(self.flash_selected)
        '''
        #endregion

        #region All other initialization
        self.load_from_prefs()

        #you know, something tells me this should not have a billion methods

    def change_preference(self, preference, value):
        '''Change `preference` to `value` and perform additional actions as necessary.
        This includes updating preferences.json.\n
        For more information, please see the README.'''
        #https://stackoverflow.com/questions/8381735/how-to-toggle-a-value-in-python
        self.settings[preference] = value

        #rewrite as dict later?
        if preference in self.drawing_area.settings:
            if preference == "default_color":
                #unpack the list if it's changing the color
                #don't know how this was missed before lol
                value = QtGui.QColor(*value)
            self.drawing_area.settings[preference] = value
        if preference == "use_crosshair":
            if value:
                self.drawing_area.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
            else:
                self.drawing_area.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        if preference == "active_coordinates" or preference == "check_overlaps":
            if self.settings['active_coordinates'] and self.settings['check_overlaps']:
                self.active_overlaps_checkbox.setEnabled(True)
            else:
                self.active_overlaps_checkbox.setEnabled(False)
                self.active_overlaps_checkbox.setChecked(False)
                self.settings['active_overlaps'] = False
        if preference == "stretch_image":
            if value:
                self.keep_ratio_checkbox.setEnabled(True)
            else:
                self.keep_ratio_checkbox.setEnabled(False)
        if preference == "conv_round":
            self.update_tables()

        write_prefs(self.settings)
    def load_from_prefs(self):
        '''Update self.settings based on values read from preferences.json.
        Remove if the __init__ call becomes the only call.
        Also updates UI elements as needed to reflect these.'''
        self.settings = get_prefs()

        for i in self.drawing_area.settings:
            self.drawing_area.settings[i] = self.settings[i]
        #we need to override the default_color value to be a QColor object, not an array
        #to unpack a list and expand it for arguments, place an asterisk before the list
        #see https://stackoverflow.com/questions/3941517/converting-list-to-args-when-calling-function
        self.drawing_area.settings['default_color'] = QtGui.QColor(*self.settings['default_color'])

        #table logic
        #make sure we don't destroy the user's custom fields if we do this
        if self.settings['check_overlaps']:
            pass
        elif self.settings['show_overlaps']: #show_overlaps isn't a valid setting?
            pass
        else:
            #maybe default column should be set to 3 in __init__?
            #or the first condition should just do nothing...
            pass

        #update checkboxes and stuff to match...
        self.active_redraw_checkbox.setChecked(self.settings['active_redraw'])
        self.active_coordinates_checkbox.setChecked(self.settings['active_coordinates'])
        self.active_overlaps_checkbox.setChecked(self.settings['active_overlaps'])
        self.check_overlaps_checkbox.setChecked(self.settings['check_overlaps'])
        self.crop_image_checkbox.setChecked(self.settings['crop_image'])
        self.stretch_image_checkbox.setChecked(self.settings['stretch_image'])
        self.keep_ratio_checkbox.setChecked(self.settings['keep_ratio'])
        self.use_crosshair_checkbox.setChecked(self.settings['use_crosshair'])
        self.conv_round_edit.setText(str(self.settings['conv_round']))
        self.left_identifier_edit.setText(self.settings['left_identifier'])
        self.right_identifier_edit.setText(self.settings['right_identifier'])

        #also enabled/disabled logic
        if self.settings['active_coordinates'] and self.settings['check_overlaps']:
            self.active_overlaps_checkbox.setEnabled(True)
        else:
            self.active_overlaps_checkbox.setEnabled(False)
        if self.settings['stretch_image']:
            self.keep_ratio_checkbox.setEnabled(True)

        #and finally update the canvas and table(s) as required
        self.update_all()
    def reset_prefs(self):
        '''Set the user preference file (preferences.json) to the defaults.
        This is achieved by getting the contents of defaults.json and writing it to the user's preference file.
        It will also call `load_from_prefs()` to deal with necessary post-processing.
        Also calls `reset_prompt()` to warn the user of a potentially destructive action.'''
        if self.reset_prompt():
            default_prefs = get_prefs("default")
            write_prefs(default_prefs)
            self.load_from_prefs()
    def update_on_rect_start(self):
        '''Holds things that should be done when a rectangle is started.
        It is likely to play a larger role when this program is rewritten.'''
        #things to do when a rectangle is started
        self.table_widget.itemChanged.disconnect(self.update_data_from_item_change)
    def update_on_rect_finish(self):
        '''Holds things that should be done when a rectangle is finished.
        It is likely to play a larger role when this program is rewritten.'''
        #things to do when a rectangle is finished.
        #on rework, this should really be the major function.
        self.table_widget.itemChanged.connect(self.update_data_from_item_change)
        #add to undo system
        self.undo_queue.append(["draw_rectangle"])
        self.actionUndo.setText('Undo rectangle draw')
    def update_tables(self):
        '''Rebuild the coordinate and conversion tables based on drawing_area.rects.'''
        #i hate this
        #but i want to finish other functionality before turning to efficiency changes so here we are
        #takes up to 40% cpu!! actual garbage

        #we rebuild the *entire* table on each call
        #this also destroys any entered data in custom fields!!
        #self.table_widget.setRowCount(0)
        self.table_widget.clearContents()
        rectangles = self.drawing_area.rects

        for row_number in range(0, len(rectangles)):
            coords = rectangles[row_number][0].getCoords()
            #print("adding row %s" % str(int(row_number)+1))
            self.table_widget.setRowCount(row_number+1)
            self.table_widget.setItem(row_number, 0, QtWidgets.QTableWidgetItem(str(coords[0])))
            self.table_widget.setItem(row_number, 1, QtWidgets.QTableWidgetItem(str(coords[1])))
            self.table_widget.setItem(row_number, 2, QtWidgets.QTableWidgetItem(str(coords[2])))
            self.table_widget.setItem(row_number, 3, QtWidgets.QTableWidgetItem(str(coords[3]))) #row, column, QtWidgets.QTableWidgetItem; zero-indexed
            self.table_widget.setItem(row_number, 4, QtWidgets.QTableWidgetItem(""))
            color = rectangles[row_number][1]
            if rectangles[row_number][1] != 'Default':
                rgba = list(color.getRgb())
                del rgba[-1]
                color = ','.join([str(component) for component in rgba])
            self.table_widget.setItem(row_number, 5, QtWidgets.QTableWidgetItem(color))#we can add the color property later
            self.table_widget.selectRow(row_number)

        #we can perform brute-force checking with QtCore.QRect.intersects(<QtCore.QRect2>)
        #the algorithm below checks each possible overlap, one-by-one (but does not check the same two rectangles for overlap twice)
        #add an "overlaps with" column if this is enabled
        #this doesn't seem to work for the first few rectangles??
        if self.settings['check_overlaps']:
            #we clear the entire column on each full overlap check
            #while implementing an array for each cell would be much better for various calculations and operations
            #maybe later
            for row_number in range(0, len(rectangles)):
                self.table_widget.setItem(row_number, 4, QtWidgets.QTableWidgetItem(""))
            for rect1_index in range(0, len(rectangles)):
                for rect2_index in range(rect1_index+1, len(rectangles)):
                    intersects = rectangles[rect1_index][0].intersects(rectangles[rect2_index][0])
                    #print(rectangles[rect1_index].intersects(rectangles[rect2_index]))
                    #print(f"Rectangle {rect1_index} overlaps with {rect2_index}?"+str(intersects))
                    current = self.table_widget.item(rect1_index, 4).text()
                    current2 = self.table_widget.item(rect2_index, 4).text()
                    #print("current = <"+current+">")
                    #print("current2 = <"+current2+">")
                    if intersects:
                        if current == "":
                            #print(f"Added {rect2_index+1} to {rect1_index+1}")
                            self.table_widget.item(rect1_index, 4).setText(str(rect2_index+1))
                        else:
                            #print(f"Added {rect2_index+1} to {rect1_index+1}")
                            self.table_widget.item(rect1_index, 4).setText(current+","+str(rect2_index+1))
                        if current2 == "":
                            #print(f"Added {rect1_index+1} to {rect2_index+1}")
                            self.table_widget.item(rect2_index, 4).setText(str(rect1_index+1))
                        else:
                            #print(f"Added {rect1_index+1} to {rect2_index+1}")
                            self.table_widget.item(rect2_index, 4).setText(current2+","+str(rect1_index+1))
        
        #https://stackoverflow.com/questions/33744111/how-to-set-qtreewidgetitem-as-not-editable
        #here we make the color and overlap columns not editable
        #this has to occur after any programmatic changes to their contents are made
        #else it becomes editable again
        for row_number in range(0, len(rectangles)):
            overlap_item = self.table_widget.item(row_number, 4)
            overlap_item.setFlags(overlap_item.flags() & ~QtCore.Qt.ItemIsEditable)
            color_item = self.table_widget.item(row_number, 5)
            color_item.setFlags(color_item.flags() & ~QtCore.Qt.ItemIsEditable)

        #i seriously doubt there's any need to have a live conversion of this table
        #will fix later
        #put in whatever gets connected to RectangleFinished
        self.converted_table_widget.setRowCount(0)
        if self.conversion_values['x1'] != None:
            #define line segment lengths
            canvas_width = self.drawing_area.size().width()
            canvas_height = self.drawing_area.size().height()
            conversion_width = self.conversion_values['x2']-self.conversion_values['x1']
            conversion_height = self.conversion_values['y2']-self.conversion_values['y1']
            places = self.settings['conv_round']

            for row_number in range(0, len(rectangles)):
                coords = rectangles[row_number][0].getCoords()
                #figure out what ratio of the whole each handle is
                x1_ratio = coords[0]/canvas_width
                y1_ratio = coords[1]/canvas_height
                x2_ratio = coords[2]/canvas_width
                y2_ratio = coords[3]/canvas_height

                #now figure out how long the handle segments are in the handle rectangle
                #and add them to the first conversion handle to find their final converted position
                #then round them to the desired number of places
                x1_equiv = round((conversion_width*x1_ratio)+self.conversion_values['x1'], places)
                y1_equiv = round((conversion_height*y1_ratio)+self.conversion_values['y1'], places)
                x2_equiv = round((conversion_width*x2_ratio)+self.conversion_values['x1'], places)
                y2_equiv = round((conversion_height*y2_ratio)+self.conversion_values['y1'], places)

                self.converted_table_widget.setRowCount(row_number+1)
                self.converted_table_widget.setItem(row_number, 0, QtWidgets.QTableWidgetItem(str(x1_equiv)))
                self.converted_table_widget.setItem(row_number, 1, QtWidgets.QTableWidgetItem(str(y1_equiv)))
                self.converted_table_widget.setItem(row_number, 2, QtWidgets.QTableWidgetItem(str(x2_equiv)))
                self.converted_table_widget.setItem(row_number, 3, QtWidgets.QTableWidgetItem(str(y2_equiv)))
    def update_all(self):
        '''Shorthand call to redraw all rectangles and reprocess the coordinate table.\n
        Might need to be updated with the conversion table in the future.
        Since the color field is planned to say "Default" when using to the default pen color\n
        (as opposed to explicitly defining the rgba value), these "default-colored" rectangles
        should immediately reflect changes to the default pen color.'''
        #calling draw_all_rects during initialization throws some errors
        #QPainter::begin: Paint device returned engine == 0, type: 3
        #QPainter::setPen: Painter not active
        #this seems to have no long-lasting effects so i won't implement a check to ensure
        #drawing_area exists before finishing update_all()
        self.drawing_area.draw_all_rects()
        self.update_tables()
    def update_data_from_item_change(self, table_item):
        '''When the user edits a coordinate point in the table, update the canvas to reflect
        the change. Ignores any edits past the fourth column (the last coordinate column).\n
        Note that this is called even for programmatic edits - thus, recolors and changes to
        the overlap count will normally cause this to execute.'''
        rect_index = table_item.row()
        data_index = table_item.column()

        if data_index > 3:
            return None

        rectangle = self.drawing_area.rects[rect_index][0]
        current_coords = list(rectangle.getCoords())
        current_coords[data_index] = int(table_item.text())
        point_1 = QtCore.QPoint(current_coords[0], current_coords[1])
        point_2 = QtCore.QPoint(current_coords[2], current_coords[3])
        new_rect = QtCore.QRect(point_1, point_2)
        self.drawing_area.rects[rect_index][0] = new_rect
        self.drawing_area.draw_all_rects()

        #Implementing undo would require the container-table separation
        #since there seems to be no way to figure out what was there before
        #the table would be updated, then we look to the associated indices in a hidden array...
        #but that doesn't exist so no undo here
    def change_canvas_size(self):
        '''Change the size of the canvas to that specified in `canvas_width_edit` and
        `canvas_height_edit`.\n
        Note that image-canvas maniuplation is not actually done here - they are done
        in CanvasArea itself. This means the `crop_image` and `stretch_image` settings
        have no effect here.\n
        The conversion labels are also updated here, as well.'''
        new_width = int(self.canvas_width_edit.text())
        new_height = int(self.canvas_height_edit.text())
        new_size = QtCore.QSize(new_width, new_height)
        self.drawing_area.setFixedSize(new_size)
        self.conv_x2_label.setText("Bottom-right, x (x = %s px)"%new_width)
        self.conv_y2_label.setText("Bottom-right, y (y = %s px)"%new_height)
    def update_size_text(self):
        '''Update UI text to reflect the current size of the canvas.\n
        This includes the canvas size QLineEdits on the Settings tab and the
        conversion labels on the Conversion tab.'''
        width = str(self.drawing_area.size().width())
        height = str(self.drawing_area.size().height())
        self.canvas_width_edit.setText(width)
        self.canvas_height_edit.setText(height)
        self.conv_x2_label.setText("Bottom-right, x (x = %s px)"%width)
        self.conv_y2_label.setText("Bottom-right, y (y = %s px)"%height)
    def clear_all(self):
        '''Clear all data (after warning the user).'''
        if self.clear_prompt():
            self.drawing_area.rects = []
            self.update_all()
    def remove_last(self):
        '''Remove the most recently added row.'''
        self.table_widget.removeRow(self.table_widget.rowCount()-1)
    def update_coords(self, x_pos, y_pos):
        '''Update the coordinate labels below the canvas.'''
        self.coord_label.setText("x:"+str(x_pos)+" y:"+str(y_pos))
    def set_conversion_values(self):
        '''Validate the entered conversion values/handles.
        If valid, set these handles to self.conversion_values.\n
        Valid handles must be convertible into floats by Python
        and 2nd handles must always be greater than the 1st handles
        of their respective axes.'''
        #validation
        try:
            #ideally I would've done self.formLayout.findChildren
            #however as it turns out ownership of the lineedits is tab_2
            #see https://stackoverflow.com/questions/3077192/get-a-layouts-widgets-in-pyqt
            values = []
            for lineedit in self.tab_2.findChildren(QtWidgets.QLineEdit):
                if lineedit.text() == "": #they can't be blank
                    lineedit.setText("0")
                #the only case i think this throws an error is if bad e notation is typed in
                #trailing/leading decimals are ok
                #as is <float>e<int>
                values.append(float(lineedit.text()))
            #print("float conversion was ok")
            #check if x1 is less than x2 and y1 is less than y2
            #this makes sure that the rectangle and its handles are in the right direction
            #from testing it seems that the lineedits are always returned from findChildren in the same order
            #so this *should* always work
            #if values[0] > values[2] or values[1] > values[3]:
            #    raise ValueError
            #note: the above was changed right before 0.2, where abs() was used to calculate a ratio instead
            #because really x1 > x2 won't always be the case
            #print("rectangle validation was ok")
            #check if aspect ratio was preserved
            canvas_ratio = self.drawing_area.size().height()/self.drawing_area.size().width()
            try:
                conv_ratio = abs(values[3]-values[1])/abs(values[2]-values[0])
            except ZeroDivisionError:
                conv_ratio = 0.0
            #chances are that nobody will ever have the exact same ratio as the canvas
            #but it's here anyways as a warning
            if canvas_ratio != conv_ratio:
                QtWidgets.QMessageBox.information(self, "Aspect ratio is not exact",
                                          '<p>The ratio of the canvas is %s, while that of your handles is %s.</p>'
                                          '<p>Converted values are proportional to the size of the rectangle containing them. '
                                          'You may end up with some stretched/inaccurate values as a result.</p>'%(canvas_ratio, conv_ratio),
                                          QtWidgets.QMessageBox.Ok)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Invalid value entered",
                                          '<p>At least one conversion handle is invalid. This typically means:</p>'
                                          '<ul><li>a number could not be converted to a floating-point number by Python, or</li>\n'
                                          '<li>a strange unforseeable problem has occurred\n</li></ul>'
                                          '<p>Ensure that you have entered the correct values. Note that '
                                          'empty values will be implicitly converted to 0.</p>'
                                          '<p>E notation is valid in the format &lt;float&gt;e&lt;int&gt;.</p>',
                                          QtWidgets.QMessageBox.Ok)
            return None
        #set to instance attr
        self.conversion_values['x1'] = float(self.conv_x1_edit.text())
        self.conversion_values['y1'] = float(self.conv_y1_edit.text())
        self.conversion_values['x2'] = float(self.conv_x2_edit.text())
        self.conversion_values['y2'] = float(self.conv_y2_edit.text())
        self.update_tables()
    def add_custom_field(self):
        '''Prompt the user for the name of a new field, where they can enter custom data for export.
        As of right now, update_tables() will overwrite existing data in these columns. Use
        is strongly discouraged - write to a CSV and add your new data there instead.'''
        #add handling for blank responses...
        new_field_name, response = QtWidgets.QInputDialog.getText(self, "Add new custom field",
                                                  "Custom field name:")
        print(new_field_name, response)
        self.table_widget.insertColumn(self.table_widget.columnCount())
        #a horizontalHeaderItem *does not* exist after calling insertColumn
        #it must explicitly be created, which is done below
        #this is why we can't just get the horizontalHeaderItem and use setText()
        #because it doesn't exist lol
        if new_field_name == "":
            self.table_widget.setHorizontalHeaderItem(self.table_widget.columnCount()-1, QtWidgets.QTableWidgetItem(str(self.table_widget.columnCount())))
        else:
            self.table_widget.setHorizontalHeaderItem(self.table_widget.columnCount()-1, QtWidgets.QTableWidgetItem(new_field_name))
        #to prevent errors on export, each of the cells in the new column are initialized to an empty string (so as to avoid NoneType errors)
        #maybe move this into the export functions themselves?
        #or fix the bad table updating function lol
        for row_number in range(0, self.table_widget.rowCount()):
            self.table_widget.setItem(row_number, self.table_widget.columnCount()-1, QtWidgets.QTableWidgetItem(""))
        
        #add to undo system
        self.undo_queue.append(["add_custom_field"])
        self.actionUndo.setText('Undo custom field add')
        
        #i tried
        #self.table_widget.horizontalHeaderItem(self.table_widget.columnCount()-1).setText(new_field_name)
        #print(self.table_widget.columnCount())
        #print(self.table_widget.horizontalHeaderItem(self.table_widget.columnCount()-2).text())
    def show_table_menu(self, pos):
        '''Holds the custom context menu when the user right-clicks on the coordinate table.
        Here, the user can delete or recolor the currently selected rows/rectangles.'''
        #https://stackoverflow.com/questions/36614635/pyqt-right-click-menu-for-qcombobox
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("Delete", self.delete_selected_rectangles)
        recolor_action = menu.addAction("Recolor", self.recolor_selected_rectangles)
        #https://doc.qt.io/qt-5/qwidget.html#mapToGlobal
        #exec is necessary to show this menu
        #mapToGlobal will determine where it should go
        #it will translate the widget coordinate pos to the global position
        #so that the menu is placed correctly relative to the mouse;
        #"where is <pos>'s position in table_widget relative to the global screen?"
        action = menu.exec_(self.table_widget.mapToGlobal(pos))
    def get_selected_rows(self):
        '''Returns a list containing the rows currently selected by the user.'''
        #return selected rows
        #https://stackoverflow.com/questions/5927499/how-to-get-selected-rows-in-qtableview
        #print(row, column)
        selected_rows = []
        #for item in self.table_widget.selectedIndexes():
        for item in self.table_widget.selectedItems():
            #print(item.row(), item.column())
            if item.row() not in selected_rows:
                selected_rows.append(item.row())
        return selected_rows
    def delete_selected_rectangles(self):
        '''Deletes the rectangles currently selected on the table.'''
        selected = self.get_selected_rows()
        self.delete_rows(selected)
    def delete_rows(self, rows):
        '''Delete `rows` (`list`) from the table and their respective rectangles on the canvas.'''
        #https://stackoverflow.com/questions/3940128/how-can-i-reverse-a-list-in-python
        #work from most recent to least recent to prevent conflicts
        for row_index in reversed(rows):
            self.table_widget.removeRow(row_index)
            self.converted_table_widget.removeRow(row_index)
            del self.drawing_area.rects[row_index]
        self.drawing_area.draw_all_rects()
    def update_rect_labels_active(self, temp_rect):
        '''Update the upper-left labels above the table to reflect the coordinates of a 
        rectangle currently being drawn, `temp_rect`, which is a QRect object.'''
        coords = temp_rect.getCoords()
        number = self.table_widget.rowCount() + 1
        self.current_selected_label.setText("Currently drawing rectangle %s"%number)
        self.current_coordinates_label.setText(f"Coordinates: {coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}")
        self.current_overlaps_label.setText("")
    def update_rect_labels(self):
        '''On row selection change, update the upper-left labels to reflect what the user
        currently has selected. Also modifies buttons if necessary.'''
        selected = self.get_selected_rows()
        self.delete_rect_button.setEnabled(True)
        self.change_rect_color_button.setEnabled(True)
        if len(selected) == 0:
            #i wasn't able to actually get this case to happen but it's here anyways
            self.current_selected_label.setText("No rectangles selected")
            self.current_coordinates_label.clear()
            self.current_overlaps_label.clear()
            self.delete_rect_button.setEnabled(False)
            self.change_rect_color_button.setEnabled(False)
        elif len(selected) == 1:
            coords = self.drawing_area.rects[selected[0]][0].getCoords()
            self.current_selected_label.setText("Rectangle %s selected"%(selected[0]+1))
            self.current_coordinates_label.setText(f"Coordinates: {coords[0]}, {coords[1]}, {coords[2]}, {coords[3]}")
            #probably set a conditional here...
            self.current_overlaps_label.setText("")
        else:
            #multiple selected
            for i in range(0, len(selected)):
                selected[i] += 1
            rects = ', '.join([str(rect_no) for rect_no in selected])
            self.current_selected_label.setText("Rectangles %s selected"%(rects))
            self.current_coordinates_label.clear()
            self.current_overlaps_label.clear()
    def flash_selected(self):
        '''Would have flashed the currently selected rectangle (based on table row selection)
        by starting a QTimer and toggling that rectangle's alpha value.'''
        #method 1: flash by enlarging rectangle
        #method 2: flash by changing color
        #method 3: flash by hiding and then not
        #maybe later - it's introducing too much complexity for such a minor feature
        pass
    def update_csv_export_text(self, button):
        '''Called when a button in self.radio_group is clicked, passing in the clicked button
        `button`. Based on this button's text, update the description label below the radio buttons.'''
        if button.text() == "Raw coordinates":
            self.selection_label.setText("Raw coordinates: Export the raw pixel-based coordinates of the rectangles in the format x1, y1, x2, y2.")
        elif button.text() == "Converted coordinates":
            self.selection_label.setText("Converted coordinates: Export the converted coordinates of the rectangles in the format x1_conv, y1_conv, x2_conv, y2_conv.")
        elif button.text() == "Both":
            self.selection_label.setText("Both: Export both raw and converted coordinates in the format x1, y1, x2, y2, x1_conv, y1_conv, x2_conv, y2_conv.")
        elif button.text() == "All":
            self.selection_label.setText("All: Export every valid field, including custom fields, color, and overlaps if enabled in the format raw coordinates, other fields, converted coordinates.")
    def simple_csv_export(self):
        '''Export coordinate and/or converted point data, based on radio button selection.
        If the user needs other fields or reordering, they will need to use the advanced
        export option.\n
        In addition, if the user has not defined coordinate handles, they will be unable to
        export data on either converted or both mode. Throw a message box as a result.'''
        header_column = []
        data = []
        #get radio button state here and update the exports as necessary
        #then set the final mode to an int
        #i'm not sure if this is any more efficient than repeatedly checking strings
        mode = self.radio_group.checkedButton().text()
        if mode == "Raw coordinates":
            mode = 1
        elif mode == "Converted coordinates":
            mode = 2
        elif mode == "Both":
            mode = 3
        elif mode == "All":
            mode = 4
        #stop execution if there are no coordinate handles defined for an export that requires them
        if not self.conversion_values['x1'] and (mode == 2 or mode == 3):
            QtWidgets.QMessageBox.information(self, "Coordinate handles not defined",
                                     '<p>You cannot export data that does not exist! Define '
                                     'coordinate handles in the Conversion tab before selecting '
                                     'either the "Converted coordinates" or "Both" options.</p>',
                                     QtWidgets.QMessageBox.Ok)
            return None
        if mode == 1 or mode == 3:
            for i in range(0, 4):
                header_column.append(self.table_widget.horizontalHeaderItem(i).text())
        if mode == 4:
            for i in range(0, self.table_widget.columnCount()):
                header_column.append(self.table_widget.horizontalHeaderItem(i).text())
        if (mode == 2 or mode == 3) or (mode == 4 and self.conversion_values['x1']):
            for i in range(0, 4):
                header_column.append(self.converted_table_widget.horizontalHeaderItem(i).text())
        #we assume that both tables will have the same row count
        position = "--"
        for row_number in range(0, self.table_widget.rowCount()):
            try:
                row_data = []
                if mode == 1 or mode == 3:
                    position = "raw"
                    for column_number in range(0, 4):
                        row_data.append(self.table_widget.item(row_number, column_number).text())
                if mode == 4:
                    position = "raw"
                    for column_number in range(0, self.table_widget.columnCount()):
                        row_data.append(self.table_widget.item(row_number, column_number).text())
                if (mode == 2 or mode == 3) or (mode == 4 and self.conversion_values['x1']):
                    position = "converted"
                    for column_number in range(0, 4):
                        row_data.append(self.converted_table_widget.item(row_number, column_number).text())
                data.append(row_data)
            except AttributeError:
                #i seriously don't know what would trigger this normally
                #other than the empty table case
                QtWidgets.QMessageBox.critical(self, "Export failed",
                                     "<p>Error: bad data at row %s, column %s - %s</p>"
                                     "<p>If you're seeing this error in a public release, "
                                     "then either you have an empty table or something's gone terribly "
                                     "wrong.</p>"%(row_number+1, column_number+1, position),
                                     QtWidgets.QMessageBox.Ok)
                return None
        #print(header_column)
        #print(data)
        #instead of passing csvpath, pass file_name from prompt
        #if it doesn't already exist, Python will create a new file at that location
        initialPath = QtCore.QDir.currentPath() + '/untitled.csv'
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", initialPath,
                "CSV (Comma delimited) (*.csv);;All Files (*)")
        try:
            if file_name:
                with open(file_name, mode='w', newline='') as csv_file:
                    writer = csv.writer(csv_file)

                    writer.writerow(header_column)
                    writer.writerows(data)
                    QtWidgets.QMessageBox.information(self, "Export complete",
                                        "CSV saved!",
                                        QtWidgets.QMessageBox.Ok)
        except Exception as e:
            #i have no idea how to trigger this manually so uhh
            QtWidgets.QMessageBox.critical(self, "Export failed",
                                     "<p>Error:</p><p>%s</p>"%e,
                                     QtWidgets.QMessageBox.Ok)
    def advanced_csv_export(self):
        '''Open the advanced CSV export window via an instance of `AdvancedExportWindow`.
        There is no additional logic in this function since the window is application-modal
        and handles all needed functionality.'''
        self.export_window = AdvancedExportWindow(self.get_column_headers(), self.table_widget, self.converted_table_widget)
        self.export_window.show()
    def csv_import(self):
        '''Import coordinates and colors from a CSV file of the format
        x1, y1, x2, y2, <any>, color, ...\n
        Any fields after color are ignored.'''
        QtWidgets.QMessageBox.information(self, "Import information",
                                        'Click <a href="https://github.com/aacttelemetry">here</a>'
                                        ' for more information on importing.',
                                        QtWidgets.QMessageBox.Ok)
        #step 1: parse data
        #if the last column == y2_conv:
        #work from [:-4]
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File",
                                                   QtCore.QDir.currentPath(),
                                                   "CSV (Comma delimited) (*.csv);;All Files (*)")
        if file_name:
            if self.drawing_area.rects:
                response = QtWidgets.QMessageBox.question(self, "Reset drawing area and import?",
                                                        'Importing new coordinates will reset the canvas! Do you '
                                                        'want to import coordinates from a CSV file anyways?',
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if response == QtWidgets.QMessageBox.No:
                    #closing the window also seems to return this
                    return None
            try:
                final = []
                with open(file_name, mode='r', newline='') as csv_file:
                    reader = csv.reader(csv_file)
                    data = list(reader)
                    for i in range(1,len(data)):
                        row = data[i]
                        point_1 = QtCore.QPoint(int(row[0]), int(row[1]))
                        point_2 = QtCore.QPoint(int(row[2]), int(row[3]))
                        rect = QtCore.QRect(point_1, point_2)
                        if row[5] == "Default":
                            color = "Default"
                        else:
                            color = QtGui.QColor(*[int(item) for item in row[5].split(",")])
                        final.append([rect, color])
                self.table_widget.itemChanged.disconnect(self.update_data_from_item_change)
                self.drawing_area.rects = final
                self.update_all()
                self.table_widget.itemChanged.connect(self.update_data_from_item_change)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Import failed",
                                     "<p>Error:</p><p>%s</p>"%e,
                                     QtWidgets.QMessageBox.Ok)
    def get_column_headers(self):
        '''Standalone function for getting the available variables for an
        export. Returns a list containing the (names of) valid column headers,
        each element a `str` containing the name of the column header.\n
        Note that this *does not* return the objects themselves.'''
        available_vars = []
        for column_number in range(0, self.table_widget.columnCount()):
            header_name = self.table_widget.horizontalHeaderItem(column_number).text()
            available_vars.append(header_name)
        if self.conversion_values['x1']:
            for column_number in range(0, self.converted_table_widget.columnCount()):
                header_name = self.converted_table_widget.horizontalHeaderItem(column_number).text()
                available_vars.append(header_name)
        #var_string = ', '.join([str(item) for item in available_vars])
        #return var_string
        return available_vars
    def update_inline_valid_vars(self, index):
        '''Update `vars_label` with the current valid column headers based on
        the value returned from `get_column_headers()`.'''
        #https://stackoverflow.com/questions/44471380/surround-strings-in-an-array-with-a-certain-character
        #for surrounding each element
        if index == 2:
            #see https://stackoverflow.com/questions/44778/how-would-you-make-a-comma-separated-string-from-a-list-of-strings
            #also used elsewhere in this program
            left_id = self.settings['left_identifier']
            right_id = self.settings['right_identifier']
            vars = ', '.join([str(left_id+item+right_id) for item in self.get_column_headers()])
            self.vars_label.setText("Available variables: "+vars)
    def fstring_export(self):
        '''Using the data currently contained in the inline editor, interpret the data
        as if it were a Python f-string for each rectangle row (newline separated).
        Export the result to a .txt file specified by the user.'''
        #In reality, this function uses two identifying characters to replace variables.
        #An f-string-like format appeared to be the most natural way to ask the user where
        #to put column data.

        #Currently unused, but with how this ended up, any arbitrary and unique identifer could do
        #we can have the user define those in settings or something
        #it's still basically an f-string though
        #identifiers = ["{","}"]

        #Get table headers.
        #wrt to self.table ... these return memory addresses and thus is not terrible
        available_vars = []
        full_dict = {}
        left_id = self.settings['left_identifier']
        right_id = self.settings['right_identifier']
        for column_number in range(0, self.table_widget.columnCount()):
            header_name = self.table_widget.horizontalHeaderItem(column_number).text()
            available_vars.append(header_name)
            full_dict[left_id+header_name+right_id] = [column_number, self.table_widget]
        if self.conversion_values['x1']:
            for column_number in range(0, self.converted_table_widget.columnCount()):
                header_name = self.converted_table_widget.horizontalHeaderItem(column_number).text()
                available_vars.append(header_name)
                full_dict[left_id+header_name+right_id] = [column_number, self.converted_table_widget]
        #print(full_dict)
        user_input = self.fstring_edit.toPlainText()

        #this is what will end up being written to the file
        final = ""
        #again, we assume that both tables will have the same row count
        try:
            for row_number in range(0, self.table_widget.rowCount()):
                temp = user_input
                for i in full_dict:
                    temp = temp.replace(i, full_dict[i][1].item(row_number, full_dict[i][0]).text())
                final += temp+"\n"
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export failed",
                                     "<p>Error: %s</p>"
                                     "<p>You may want to try defining a different identifier "
                                     "or checking your formatting. Ensure there are no spaces "
                                     "between your identifier and your column header names.</p>"
                                     "<p>If all else fails, you should consider exporting this "
                                     "data to a CSV file and working from there.</p>"%e,
                                     QtWidgets.QMessageBox.Ok)
            return None

        initialPath = QtCore.QDir.currentPath() + '/untitled.txt'
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", initialPath,
                "Plain Text (*.txt);;All Files (*)")
        try:
            if file_name:
                with open(file_name, mode='w') as txt_file:
                    txt_file.write(final)
                    txt_file.close()
                    QtWidgets.QMessageBox.information(self, "Export complete!",
                                     '<p>Done. If the output appears wrong or you have leftover '
                                     'column headers, check your formatting.</p>'
                                     '<p>You may want to consider exporting to a CSV file instead '
                                     'if the output continues to be incorrect.</p>',
                                     QtWidgets.QMessageBox.Ok)
        except Exception as e:
            #again, no idea how to manually trigger this
            QtWidgets.QMessageBox.critical(self, "Export failed",
                                     "<p>Error:</p><p>%s</p>"%e,
                                     QtWidgets.QMessageBox.Ok)
        #Rather than write to the output file many times on write-append mode,
        #I elected to just repeatedly append data to a single string.
        #Python strings can be rather large in size (depending on OS), and I don't
        #think there will ever be a need to worry about a string exceeding 1GB.
        #It wouldn't be too hard to turn this into a buffer and write each time it gets
        #too big or something, though.
    def fstring_export_old(self):
        '''This was the old fstring_export function before it was reworked
        to actually work (and avoid exec/eval in the process).
        
        It is kept here for reference.'''
        #With regards to the potentialy security issue above, this is not much different from
        #a user just having a standard Python interpreter available to them. Everything is local,
        #so there's no fear of damaging an external system or something - it will stay as-is for now.

        #Currently unused, but with how this ended up, any arbitrary and unique identifer will do and we can have the user define those
        #it's still basically an f-string though
        #identifiers = ["{","}"]

        #Get table headers.
        available_vars = []
        full_dict = {}
        for column_number in range(0, self.table_widget.columnCount()):
            header_name = self.table_widget.horizontalHeaderItem(column_number).text()
            available_vars.append(header_name)
            full_dict["{"+header_name+"}"] = "self.table_widget.item({row_number}, %s).text()"%column_number
        if self.conversion_values['x1']:
            for column_number in range(0, self.converted_table_widget.columnCount()):
                header_name = self.converted_table_widget.horizontalHeaderItem(column_number).text()
                available_vars.append(header_name)
                full_dict["{"+header_name+"}"] = "self.converted_table_widget.item({row_number}, %s).text()"%column_number
        
        #Convert the contents of the text box into a standard string that can actually be used by exec().
        user_input = repr(self.fstring_edit.toPlainText())
        #user_input = self.fstring_edit.toPlainText()
        print(user_input)
        for i in full_dict:
            user_input = user_input.replace(i, full_dict[i])
        f_string = user_input

        #Actually perform exec() on each row.
        #again, we assume that both tables will have the same row count
        #and at this point we've converted _conv anyways if it exists
        
        final = ""
        for row_number in range(0, self.table_widget.rowCount()):
            #exec('final += f"%s"\n'%f_string, {"final":final, "row_number":row_number})
            #print('final += f%s\n'%f_string)
            print(eval('f"%s"'%f_string))
        print(final)

        #for updating the label:
        #see https://stackoverflow.com/questions/44778/how-would-you-make-a-comma-separated-string-from-a-list-of-strings
    def new_fstring_window(self):
        '''Open a new window composed of only a text editor and a button. This allows the
        user to more easily write an f-string if the inline editor is too small.'''
        new_text = StringDialog.launch(self.fstring_edit.toPlainText(),self.vars_label.text())
        self.fstring_edit.setPlainText(new_text)
    def undo_new(self, action):
        '''What should be the more encompassing undo function.'''
        pass
    def open_image(self):
        '''Handles opening an image.
        This includes the creation of a QtWidgets.QFileDialog and determining if an image is valid.
        It will also ask the user if they want to clear the canvas on image load.'''
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File",
                                                   QtCore.QDir.currentPath())
        if file_name:
            if not QtGui.QImage().load(file_name):
                QtWidgets.QMessageBox.critical(self, "Couldn't load image",
                                     "This image appears to be an unsupported filetype and could not be loaded.",
                                     QtWidgets.QMessageBox.Ok)
                self.open_image()
            else:
                if self.drawing_area.rects:
                    response = QtWidgets.QMessageBox.question(self, "Reset drawing area?",
                                                    'Do you want to clear drawn rectangles and start from scratch?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if response == QtWidgets.QMessageBox.Yes:
                        self.drawing_area.rects = []
                        self.update_all()
                self.drawing_area.open_image(file_name)
                #at this point, we should execute the resize logic
    def save_file(self):
        '''Save the current contents of the canvas to an image of the user's
        desired image format.'''
        initialPath = QtCore.QDir.currentPath() + '/untitled'

        #QImageWriter is used here for determining saveable file formats
        #see https://doc.qt.io/qt-5/qimagewriter.html#supportedImageFormats

        available_formats = ""

        for file_format in QtGui.QImageWriter.supportedImageFormats():
            #see https://stackoverflow.com/questions/57663191/how-to-convert-a-qbytearray-to-a-python-string-in-pyside2
            format_extension = file_format.data().decode()
            format_name = format_extension.upper()
            available_formats += "%s (*.%s);;"%(format_name, format_extension)
        available_formats += "All Files (*)"

        file_name, selected_format = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", initialPath,
                available_formats)
        if file_name:
            #selected_format returns the full string (%s (*.%s)), so we use the space to figure
            #out what type it actually is
            selected_format = selected_format.split(" ")[0] 
            selected_format = selected_format.lower() #dunno if this makes a difference
            return self.drawing_area.save_image(file_name, selected_format)

        return False #return none??
    def undo(self):
        '''Tell the canvas to remove the most recent rectangle.
        Also updates the coordinate table.'''
        self.drawing_area.undo_last()
        #delete most recent table entry on undo
        self.table_widget.removeRow(self.table_widget.rowCount()-1)
    def toggle_conversion_info(self):
        '''Toggle the visibility of the big block of text above the
        conversion table.'''
        if self.conversion_groupbox.isVisible():
            self.conversion_groupbox.setVisible(False)
            self.toggle_show_conv_button.setArrowType(QtCore.Qt.DownArrow)
        else:
            self.conversion_groupbox.setVisible(True)
            self.toggle_show_conv_button.setArrowType(QtCore.Qt.UpArrow)
    def change_default_pen_color(self):
        '''Open a dialog allowing the user to change the default rectangle color.
        Also prompts the user on whether or not they'd like rectangles with a color of
        "Default" to remain the old default color - converting the table fields to rgb -
        or use the newly-defined default color.'''
        new_color = QtWidgets.QColorDialog.getColor(self.drawing_area.penColor())
        if new_color.isValid():
            response = QtWidgets.QMessageBox.question(self, "Recolor default-colored rectangles?",
                                          '<p>Do you want rectangles with a color of "Default" to '
                                          'remain the old default color?</p>'
                                          '<p>If you select "Yes", then rectangles currently with a color of '
                                          '"Default" will have their colors explicitly set to the old default ' 
                                          'color, at which point they will use the (r,g,b) format.</p>'
                                          '<p>If you select "No", these rectangles will take on the color '
                                          'you just selected and will continue to have "Default" '
                                          'as their color in the coordinate table.</p>',
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if response == QtWidgets.QMessageBox.Yes:
                current_default = self.drawing_area.settings['default_color']
                for rect in self.drawing_area.rects:
                    print(current_default)
                    print(current_default.getRgb())
                    rect[1] = current_default
            self.drawing_area.set_pen_color(new_color)
            self.change_preference('default_color', list(new_color.getRgb()))
            self.update_all()
    def recolor_selected_rectangles(self):
        '''Recolor the rectangles reflected by the rows currently selected in the coordinate
        table.'''
        rows = self.get_selected_rows()
        new_color = QtWidgets.QColorDialog.getColor(self.drawing_area.penColor())
        print(new_color)
        if new_color.isValid():
            for rect_index in rows:
                self.drawing_area.rects[rect_index][1] = new_color
            self.update_all()
    def change_pen_width(self):
        '''Open a dialog allowing the user to change the default rectangle width.'''
        new_width, response = QtWidgets.QInputDialog.getInt(self, "Set New Pen Width",
                                                  "Select pen width:",
                                                  self.drawing_area.penWidth(), 1, 50, 1)
        if response:
            self.drawing_area.set_pen_width(new_width)
            self.change_preference('default_width', new_width)
            self.update_all()
    def about(self):
        '''Opens this program's about dialog.'''
        QtWidgets.QMessageBox.about(self, "About RectangleMappingTool",
                '<p>RectangleMappingTool is a program designed for the '
                '<a href="https://github.com/aacttelemetry">AACT Telemetry project</a>, '
                'built with PyQt5 and packaged through fbs.</p>'
                '<p>Its primary purpose is to make creating rectangular bounding regions '
                'based on an image easier.</p>'
                '<p>You can view the source of this program and additional information '
                '<a href="https://github.com/aacttelemetry/RectangleMappingTool">here</a>.</p>')
    def open_github(self):
        '''Opens this program's repo in the user's default browser.'''
        webbrowser.open("https://github.com/aacttelemetry/RectangleMappingTool")
    def reset_prompt(self):
        '''Warns the user that they are about to reset the program's settings to their defaults.
        Returns `True` if "Reset" is selected.
        Returns `False` otherwise.'''
        ret = QtWidgets.QMessageBox.warning(self, "Reset preferences?",
                                          'Are you sure you want to reset your preferences to the default preferences?',
                                          QtWidgets.QMessageBox.Reset | QtWidgets.QMessageBox.Cancel)
        if ret == QtWidgets.QMessageBox.Reset:
            return True
        elif ret == QtWidgets.QMessageBox.Cancel:
            return False
    def clear_prompt(self):
        '''Warns the user that they are about to clear all data.
        Returns `True` if "Yes" is selected.
        Returns `False` otherwise.'''
        ret = QtWidgets.QMessageBox.warning(self, "Clear all data?",
                                          'Are you sure you want to clear all data?\n'
                                          'This will delete all table entries and drawn rectangles.',
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        #i would use "clear", "discard", or "reset", but each of those have different meanings
        #than what i would want here
        if ret == QtWidgets.QMessageBox.Yes:
            return True
        elif ret == QtWidgets.QMessageBox.Cancel:
            return False
    def close_prompt(self):
        '''Warns the user if the canvas has been modified.
        This is determined by the presence of any rectangles.
        Returns True if the user wants to close the program anyways or no rectangles have been drawn.
        Returns False otherwise.'''
        #because "saving" could mean anything from exporting the coords to saving the image
        #there is no handling of saving here
        #a modified drawing_area is one that has any rectangles whatsoever

        #if this ends up being just a pre-close prompt, change the language accordingly
        if self.drawing_area.rects:
            ret = QtWidgets.QMessageBox.information(self, "Close?",
                                          'Ensure that you have exported or saved any data '
                                          'you were working with.\n'
                                          'Click "Close" to continue, or "Cancel" to return.',
                                          QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel)
            if ret == QtWidgets.QMessageBox.Close:
                return True
            elif ret == QtWidgets.QMessageBox.Cancel:
                return False
        else:
            return True
    def closeEvent(self, event): # pylint: disable=invalid-name
        '''Reimplementation of the close event to warn the user on program close.
        See close_prompt().'''
        if self.close_prompt():
            event.accept()
        else:
            event.ignore()

class AdvancedExportWindow(QtWidgets.QMainWindow,Ui_AdvExportWindow):
    '''Opens the advanced CSV export window, where the user is able to reorder and change
    what fields are exported. Includes a raw CSV preview as well as a table preview of
    the results.'''
    def __init__(self, available_vars, main_table, conv_table):
        super().__init__()
        #keep the user from messing with existing data without exiting
        self.setWindowModality(QtCore.Qt.ApplicationModal) 
        self.setupUi(self)
        self.setWindowTitle("Advanced CSV Export")
        for var in available_vars:
            self.available_fields_list.addItem(var)
        self.available_fields_list.itemClicked.connect(self.update_descriptions)
        self.selected_fields_list.itemClicked.connect(self.update_descriptions)
        #for updating the previews
        #i could not for the life of me get this to work without implement a nonzero delay on update
        #it worked perfectly fine adding elements
        #then on removing elements this function would still think the removed element is there
        #but executing this function at a brief point in time after the signal is emitted returns valid values
        #i dont know why???
        self.available_fields_list.itemChanged.connect(lambda: QtCore.QTimer.singleShot(10, self.update_previews))
        self.selected_fields_list.itemChanged.connect(lambda: QtCore.QTimer.singleShot(10, self.update_previews))

        self.advanced_export_button.clicked.connect(self.export_values)

        self.available_vars = available_vars

        #memory references to the actual tables
        #used for getting the data
        self.main_table = main_table
        self.conv_table = conv_table

        #possible descriptions of each standard field
        #custom fields are defined as such in update_descriptions
        self.descriptions = {
            'x1':'The x-coordinate of the top-left point of a rectangle.',
            'y1':'The y-coordinate of the top-left point of a rectangle.',
            'x2':'The x-coordinate of the bottom-right point of a rectangle.',
            'y2':'The y-coordinate of the bottom-right point of a rectangle.',
            'Overlaps with:':'The rectangles (listed by row number) that a rectangle overlaps with.',
            'Color (r,g,b)':"This rectangle's border color, represented as an RGB value.",
            'x1_conv':'The converted x-coordinate of the top-left point of a rectangle.',
            'y1_conv':'The converted y-coordinate of the top-left point of a rectangle.',
            'x2_conv':'The converted x-coordinate of the bottom-right point of a rectangle.',
            'y2_conv':'The converted y-coordinate of the bottom-right point of a rectangle.',
        }
    def update_descriptions(self, list_item):
        '''Update the current item description and name based on the text of the list item
        clicked. Called when a list item in either `QTableWidget` is clicked.\n
        All descriptions are based on `self.descriptions` - custom fields will not be in
        this dict, and thus will result in a description of "Custom field."'''
        name = list_item.text()
        if name in self.descriptions:
            self.selected_field_label.setText(name)
            self.selected_info_label.setText(self.descriptions[name])
        else:
            self.selected_field_label.setText(name)
            self.selected_info_label.setText("Custom field.")
    def calculate_data(self, is_preview):
        '''Calculate the export data in a manner very similar to the main window's
        `simple_csv_export()`. However, this function adds `is_preview`, a `bool`
        that determines whether or not to calculate data to up to 5 rows or all rows.\n
        This is based on `self.selected_fields`, where the user will have already
        defined the order and selection of the fields they'd like to use.'''
        #determine if data from the conversion table is involved
        #if so, split the available variables into two lists via slicing
        if self.available_vars[-1] == "y2_conv":
            main_table_vars = self.available_vars[:-4]
            conv_table_vars = self.available_vars[-4:]
        else:
            main_table_vars = self.available_vars
            conv_table_vars = []

        #generate a dict where each column header is the key
        #and a reference to their respective table and column index (0-indexed) is the value
        #this will allow us to dynamically change what table we reference and what column to reference in that table
        #based on what headers the user wants to export in `export_headers`
        export_header_refs = {}
        
        for i in range(0, len(main_table_vars)):
            export_header_refs[main_table_vars[i]] = [self.main_table, i]
        for i in range(0, len(conv_table_vars)):
            export_header_refs[conv_table_vars[i]] = [self.conv_table, i]

        #figure out what the user will actually export, and in what order
        export_headers = []

        for i in range(0, self.selected_fields_list.count()):
            export_headers.append(self.selected_fields_list.item(i).text())

        data = []
        #depending on whether or not this is a preview, calculate data to up to 5 rows
        #or all available rows
        if is_preview:
            depth = min(5, self.main_table.rowCount())
        else:
            depth = self.main_table.rowCount()
        try:
            #get angry if the user tries to generate a preview or export data without actually having data
            #not sure if ValueError is the correct one to use here
            if depth == 0:
                raise ValueError
            for row_number in range(0, depth):
                row_data = []
                for header in export_headers:
                    #append the text of <table reference>.item(row_number, <index of `header` in table reference>)
                    row_data.append(export_header_refs[header][0].item(row_number, export_header_refs[header][1]).text())
                data.append(row_data)
        except ValueError:
            if is_preview:
                #I could use the status bar here, but I thought that might not be as obvious since
                #it's not used anywhere else and so the user wouldn't look to a status bar first
                #for a program event.
                self.sample_output_label.setText("Preview failed because you have no data!")
                QtCore.QTimer.singleShot(3000, lambda: self.sample_output_label.setText("Sample output (up to 5 rects):"))
            else:
                QtWidgets.QMessageBox.critical(self, "Export failed",
                                        "<p>Error: empty data</p>"
                                        "<p>If you're seeing this error in a public release, "
                                        "then you probably have an empty table.</p>",
                                        QtWidgets.QMessageBox.Ok)
            return None
        except Exception as e:
            #i don't know how this could possibly ever be triggered
            #because now the empty table case is explicitly accounted for
            #but here it is anyways
            if is_preview:
                self.sample_output_label.setText("Preview failed: %s"%e)
                QtCore.QTimer.singleShot(3000, lambda: self.sample_output_label.setText("Sample output (up to 5 rects):"))
            else:
                QtWidgets.QMessageBox.critical(self, "Export failed",
                                        "<p>Error: bad data at row %s, header %s</p>"
                                        "<p>%s</p>"%(row_number+1, header, e),
                                        QtWidgets.QMessageBox.Ok)
            return None
        return [export_headers, data]
    def export_values(self):
        '''Prompt the user for a filepath and save the results of a non-preview
        `self.calculate_data()` call to that CSV file, creating it if it does
        not already exist. Called when the "Export to .csv" button is clicked.'''
        data = self.calculate_data(False)

        if not data:
            return None

        #since this function effectively is the same as the end of simple_csv_export
        #on the main window i *could* create an isolated function they both use and pass
        #data into, but i would rather keep this separate and redundant for clarity

        #if it doesn't already exist, Python will create a new file at that location
        initialPath = QtCore.QDir.currentPath() + '/untitled.csv'
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", initialPath,
                "CSV (Comma delimited) (*.csv);;All Files (*)")
        try:
            if file_name:
                with open(file_name, mode='w', newline='') as csv_file:
                    writer = csv.writer(csv_file)

                    writer.writerow(data[0])
                    writer.writerows(data[1])
                    QtWidgets.QMessageBox.information(self, "Export complete",
                                        "CSV saved!",
                                        QtWidgets.QMessageBox.Ok)
        except Exception as e:
            #i have no idea how to trigger this manually so uhh
            QtWidgets.QMessageBox.critical(self, "Export failed",
                                     "<p>Error:</p><p>%s</p>"%e,
                                     QtWidgets.QMessageBox.Ok)
    def update_previews(self):
        '''Update a table-based and text-based preview of the CSV data.
        Called whenever the list items change (after a 10ms delay - see
        comments above the related signal connections).'''
        #i really don't know any other "easy" way to update this table
        #we could add handlers for each possible event - moves, additions, removals - 
        #but that's effort and too inflexible
        #for this specific use case, i think destroying the entire table on each update
        #is ok
        #self.sample_output_table.clear() #clear keeps the dimensions of the table so this won't work
        
        #get preview data
        data = self.calculate_data(True)

        #don't try to update anything if preview data calculation fails
        if not data:
            return None
        
        #update the sample table
        self.sample_output_table.setColumnCount(0)
        self.sample_output_table.setRowCount(0)
        for header_index in range(0, len(data[0])):
            self.sample_output_table.insertColumn(header_index)
            self.sample_output_table.setHorizontalHeaderItem(header_index, QtWidgets.QTableWidgetItem(data[0][header_index]))
        for row_number in range(0, len(data[1])):
            self.sample_output_table.insertRow(row_number)
            for column_number in range(0, len(data[0])):
                self.sample_output_table.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(data[1][row_number][column_number]))

        #update raw
        #this doesn't actually pass through a csv parser but it will spit out the same output
        full = ','.join([str(item) for item in data[0]])+"\n"
        for row in data[1]:
            full += ','.join([str(item) for item in row])+"\n"
        self.sample_output_raw.setPlainText(full)
        
class StringDialog(QtWidgets.QDialog,Ui_StringDialog):
    '''Opens a new dialog for f-string editing. Also provides the user
    with extra information on how f-strings work. Application modal.\n
    Intended to be called with `StringDialog.launch()`, which requires
    the parameters `current_text` - the text of the inline editor - and
    `available_vars` - a list of the usable column names.'''
    #see this link for returning values from a dialog as if it were a normal function
    #https://stackoverflow.com/questions/37411750/pyqt-qdialog-return-response-yes-or-no
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("F-string Editor")
        #i really like how qt designer didn't magically do this like it did last time
        self.done_button.clicked.connect(self.accept) 
    def getValues(self):
        return self.fstring_edit.toPlainText()
    @staticmethod
    def launch(current_text, available_vars):
        dlg = StringDialog()
        dlg.fstring_edit.setPlainText(current_text)
        dlg.available_vars_label.setText(available_vars)
        #prevent user from changing data without exiting dialog
        r = dlg.exec_()
        if r:
            return dlg.getValues()
        return None

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
