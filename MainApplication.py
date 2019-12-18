import sys
import os
import sqlite3
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QGridLayout, QLabel, QWidget)
from PyQt5.QtGui import (QImage, QPixmap, QIcon)
from PyQt5.QtCore import Qt
import h5py
import cv2
import numpy as np


class MainApplication(QWidget):
    def __init__(self, results_database, hdf5_file):
        # General variables initialization
        QWidget.__init__(self)
        self.hdf5file = hdf5_file
        self.data = h5py.File(self.hdf5file, 'r')
        self.conn, self.c, self.timestamp_counter = self.create_db(results_database)

        if self.timestamp_counter is None:
            self.timestamp_counter = 0

        # Image processing variables initialization
        self.current_timestamp = self.data['timestamps']['timestamps'][self.timestamp_counter]
        self.total_frames = len(self.data['timestamps']['timestamps'])

        # Labels for showing saving condition
        self.pic1 = QLabel(self)
        self.good_frame_marker = QLabel('MARKING GOOD FRAMES')
        self.bad_frame_marker = QLabel('MARKING BAD FRAMES')
        self.good_frame_marker.setStyleSheet('color: green; font: 35pt Arial')
        self.bad_frame_marker.setStyleSheet('color: red; font: 35pt Arial')
        # Labels for showing helpful text and frame counting
        self.keys_information = QLabel('Q = [ON/OFF] Change frame to good or bad \n'
                                    'left arrow = Save current label and go to previous image \n'
                                    'right arrow = Save current label and go to next image')
        self.keys_information.setStyleSheet('color: gray; font: 12pt Arial')
        self.frame_information = QLabel('Current frame:' + str(self.timestamp_counter+1) + '/' + str(self.total_frames))
        self.frame_information.setStyleSheet('font: 15pt Arial')
        self.frame_information.setAlignment(Qt.AlignRight)

        # Qt initialization
        self.app = QApplication([])
        self.creates_background_window()
        self.creates_images_window()
        self.creates_user_button_interface()

    def load_hdf5_image(self):
        # agroup = list(data.keys())  # For debugging purposes
        self.camera1_data = self.data['rgb']
        # Camera 1
        self.current_timestamp = self.data['timestamps']['timestamps'][self.timestamp_counter]
        self.image_camera1 = np.array(self.camera1_data[str(self.current_timestamp)])
        self.image_camera1 = cv2.resize(self.image_camera1, (1024, 768))
        # Show BB on image
        bb_vehicles = np.array(self.data['bounding_box']['vehicles'][str(self.current_timestamp)])
        bb_walkers = np.array(self.data['bounding_box']['walkers'][str(self.current_timestamp)])
        if all(bb_vehicles != -1):
            for bb_idx in range(0, len(bb_vehicles), 4):
                coordinate_min = (int(bb_vehicles[0 + bb_idx]), int(bb_vehicles[1 + bb_idx]))
                coordinate_max = (int(bb_vehicles[2 + bb_idx]), int(bb_vehicles[3 + bb_idx]))
                cv2.rectangle(self.image_camera1, coordinate_min, coordinate_max, (0, 255, 0), 1)
        if all(bb_walkers != -1):
            for bb_idx in range(0, len(bb_walkers), 4):
                coordinate_min = (int(bb_walkers[0 + bb_idx]), int(bb_walkers[1 + bb_idx]))
                coordinate_max = (int(bb_walkers[2 + bb_idx]), int(bb_walkers[3 + bb_idx]))
                cv2.rectangle(self.image_camera1, coordinate_min, coordinate_max, (0, 0, 255), 1)
        # Show timestamp on image
        cv2.putText(self.image_camera1, 'Timestamp', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(self.image_camera1, str(self.current_timestamp), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    def creates_background_window(self):
        # Top level widget and main window
        self.resize(1024, 768)
        self.setWindowTitle('RGB images classification tool')
        self.setWindowIcon(QIcon('cat.jpeg'))

        # Centralizes the main window
        qr = self.frameGeometry()  # main window dimensions
        qr.moveCenter(QDesktopWidget().availableGeometry().center())  # Get resolution from own monitor
        self.move(qr.topLeft())  # Moves the top left border of the main window

        # Creates a grid layout to put the widgets
        self.layout = QGridLayout()
        self.setLayout(self.layout)

    def creates_images_window(self):
        # Image reading part; adjusting for QT input type
        self.load_hdf5_image()  # image_camera1 and image_camera2 get updated here
        height, width, _ = self.image_camera1.shape
        bytes_per_line = 3*width  # https://stackoverflow.com/questions/34232632/convert-python-opencv-image-numpy-array-to-pyqt-qpixmap-image
        plot1 = QImage(cv2.cvtColor(self.image_camera1, cv2.COLOR_BGR2RGB), width, height, 
        bytes_per_line, QImage.Format_RGB888)
        self.pixmap1 = QPixmap.fromImage(plot1)
        self.pic1.setPixmap(self.pixmap1)

        self.layout.addWidget(self.pic1, 0, 1)  # row, column


    def creates_user_button_interface(self):
        """
        COMMANDS INTERFACE
        Q = [ON/OFF] SET FRAME TO GOOD OR BAD
        LEFT ARROW = PREVIOUS IMAGE
        RIGHT ARROW = NEXT IMAGE
        """
        self.layout.addWidget(self.keys_information, 3, 1)  # row, col
        self.layout.addWidget(self.frame_information, 3, 1)
        self.layout.addWidget(self.good_frame_marker, 2, 1)
        self.layout.addWidget(self.bad_frame_marker, 2, 1)
        self.bad_frame_marker.hide()

    # A key has been pressed!
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.save_current_label()
            self.change_frame_forward()
        elif event.key() == Qt.Key_Left:
            self.save_current_label()
            self.change_frame_backwards()
        elif event.key() == Qt.Key_Q:
            self.change_frame_marker(event.key())

    def change_frame_forward(self):
        if self.timestamp_counter == (self.total_frames-1):
            print('You got to the end of the frames! Finally :)')
        else:
            self.timestamp_counter += 1
            self.creates_images_window()
            print(f'Current frame: {self.timestamp_counter+1}/{self.total_frames}')
            self.frame_information.setText(f'Current frame: {self.timestamp_counter+1}/{self.total_frames}')

    def change_frame_backwards(self):
        if self.timestamp_counter > 0:
            self.timestamp_counter += -1
        else:
            print('You are at the beginning of the file. Can\'t go back further.')
        self.creates_images_window()
        print(f'Current frame: {self.timestamp_counter+1}/{self.total_frames}')
        self.frame_information.setText(f'Current frame: {self.timestamp_counter+1}/{self.total_frames}')

    def change_frame_marker(self, key_number):
        if key_number == 81:  # Q button
            if self.good_frame_marker.isHidden():
                self.good_frame_marker.show()
                self.bad_frame_marker.hide()
            elif self.good_frame_marker.isVisible():
                self.bad_frame_marker.show()
                self.good_frame_marker.hide()

    def save_current_label(self):
        # Checks what is the status on each label
        good_frame_marker = 0
        if self.good_frame_marker.isVisible():
            good_frame_marker = 1
        # Checks if this entry already exists to only update
        entry_exists = self.c.execute("SELECT timestamps FROM frames_analysis WHERE timestamps=(?)", (int(self.current_timestamp), )).fetchall()
        if entry_exists:
            self.c.execute("UPDATE frames_analysis SET timestamps=(?), good_frame=(?) WHERE timestamps=(?)",
                           (int(self.current_timestamp), good_frame_marker, int(self.current_timestamp)))
        else:
            self.c.execute("INSERT INTO frames_analysis VALUES (?, ?)", (int(self.current_timestamp), good_frame_marker))
        self.conn.commit()

    def create_db(self, db_full_path):
        if os.path.exists(db_full_path):
            conn = sqlite3.connect(db_full_path)
            c = conn.cursor()
            timestamp_counter = c.execute("SELECT COUNT(*) FROM frames_analysis").fetchone()[0]-1  # Dealing with python indexing
            return conn, c, timestamp_counter
        else:  # Creates header (table)
            conn = sqlite3.connect(db_full_path)
            c = conn.cursor()
            c.execute("CREATE TABLE frames_analysis (timestamps integer, good_frame integer)")
            conn.commit()
        return conn, c, None

    def run_app(self):
        # Display widget in a new window
        self.show()
        # Executes the application
        app = self.app.exec_()
        self.conn.close()
        sys.exit(app)


