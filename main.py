#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Alan Naoto
alt9707@thi.de
Created: 10.12.2019
"""
import argparse
from MainApplication import MainApplication
from PyQt5.QtWidgets import QApplication


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GUI script to filter the frames from a HDF5 dataset")
    parser.add_argument("hdf5_file", default=None, type=str, help="Full path to the HDF5 dataset")
    parser.add_argument("database_path", default=None, type=str, help="Full path to the created or to be created DB file")
    args = parser.parse_args()
    assert args.hdf5_file is not None and args.database_path is not None
    assert args.hdf5_file.endswith('.hdf5')
    assert args.database_path.endswith('.db')

    app = QApplication([])
    ae = MainApplication(args.database_path, args.hdf5_file)
    ae.run_app()
