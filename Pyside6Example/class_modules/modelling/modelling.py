from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMenu, QInputDialog
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QModelIndex, QRect
from PySide6.QtWebEngineWidgets import QWebEngineView
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import statsmodels.api as sm
from imsciences import *
from typing import Optional, List, Tuple
from statsmodels.stats.diagnostic import acorr_ljungbox, acorr_breusch_godfrey, het_breuschpagan, het_white, het_arch, linear_reset, lilliefors
from statsmodels.stats.stattools import jarque_bera, durbin_watson
from linearmodels.panel import compare
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
from scipy.special import gamma
from scipy import stats
from scipy.stats import chi2
import re
import random
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import operator as op
import math
import time
import itertools
import ast
from joblib import Parallel, delayed
from sklearn.linear_model import LinearRegression
import sys
from collections import defaultdict
import kaleido

# Create an instance of dataprocessing from imsciences
ims = dataprocessing()

# Constants
TRANSFORM_OPTIONS = ['None', 'log(x)', 'sqrt(x)', 'exp(x)']

# Some useful functions
def column_to_datetime(df, column):
        """
        Converts the specified column to datetime format, while also ensuring
        that the column names are in lowercase.

        :param column: The name of the column to be converted.
        :return: None (modifies the original DataFrame).
        """
        # Make a copy of the DataFrame and convert column names to lowercase
        df = df.copy(deep=True)
        df.columns = df.columns.str.lower()
        # Convert the specified column to datetime
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], dayfirst=True)
        else:
            print(f"Column '{column}' not found in the DataFrame.")
        
        return df

def map_short_var_names(df,var_details):
    """ Change var names to short var names"""
    col_dict = ims.convert_2_df_cols_to_dict(var_details,key_col = 'variable',value_col='short variable name')
    df = df.rename(columns=col_dict)
    return df

def lowercase_strings(details_tuple):
    """Convert all string elements in the tuple to lowercase."""
    return tuple(
        element.lower() if isinstance(element, str) else element
        for element in details_tuple
    )

def apply_lead(series_x, lead_value):
    """Handle lead function."""
    return np.roll(series_x, -lead_value)

def apply_lag(series_x, lag_value):
    """Handle lag function."""
    return np.roll(series_x, lag_value)

def adstock(series_x, ads_rate):
    ads_x = np.zeros_like(series_x)
    for i in range(len(series_x)):
        if i == 0:
            ads_x[i] = series_x[i]
        else:
            ads_x[i] = series_x[i] + ads_x[i - 1] * ads_rate
    return ads_x

def n_adstock(series_x, ads_rate):
    ads_x = adstock(series_x, ads_rate)
    return ads_x * (1 - ads_rate)

def dimret(series_x, dr_info, pct_conv=True):
    dr_x = np.zeros_like(series_x)
    if np.sum(series_x) != 0:
        if pct_conv:
            dr_alpha = -1 * np.log(1 - dr_info) / np.mean(series_x[series_x > 0])
        else:
            dr_alpha = dr_info
        dr_x = 1 - np.exp(-1 * dr_alpha * series_x)
    return dr_x

def n_dimret(series_x, dr_info, pct_conv=True):
    dr_x = dimret(series_x, dr_info, pct_conv)
    return dr_x * (np.sum(series_x) / np.sum(dr_x))

def dimret_adstock(series_x, ads_rate, dr_info, pct_conv=True):
    dr_ads_x = adstock(series_x, ads_rate)
    if np.sum(series_x) != 0:
        if pct_conv:
            dr_alpha = -1 * np.log(1 - dr_info) / np.mean(series_x[series_x > 0])
        else:
            dr_alpha = dr_info
        dr_ads_x = np.asarray(dr_ads_x,dtype=float)
        dr_ads_x = 1 - np.exp(-1 * dr_ads_x*dr_alpha)
    return dr_ads_x

# def dimret_adstock(series_x, ads_rate, dr_info, pct_conv=True):
#     print("Raw Series:", series_x)
#     # Step 1: Apply adstock
#     dr_ads_x = adstock(series_x, ads_rate)
#     print("Adstock applied:", dr_ads_x)

#     # Step 2: Check if the input series is non-zero
#     if np.sum(series_x) != 0:
#         # Step 3: Calculate diminishing returns alpha
#         if pct_conv:
#             # Check for issues with np.log or np.mean
#             positive_mean = np.mean(series_x[series_x > 0])
#             print("Mean of positive values in series_x:", positive_mean)
#             if positive_mean == 0:
#                 raise ValueError("Mean of positive values in series_x is 0, cannot calculate dr_alpha.")
#             dr_alpha = -1 * np.log(1 - dr_info) / positive_mean
#         else:
#             dr_alpha = dr_info
#         print("Calculated dr_alpha:", dr_alpha)

#         # Step 4: Apply diminishing returns transformation
#         dr_ads_x = np.asarray(dr_ads_x, dtype=float)
#         print("Adstock array before diminishing returns:", dr_ads_x)
#         dr_ads_x = 1 - np.exp(-1 * dr_ads_x * dr_alpha)
#         print("Final transformed array (diminishing returns applied):", dr_ads_x)

#     return dr_ads_x

def n_dimret_adstock(series_x, ads_rate, dr_info, pct_conv=True):
    dr_ads_x = dimret_adstock(series_x, ads_rate, dr_info, pct_conv)
    return dr_ads_x * (np.sum(series_x) / np.sum(dr_ads_x))

def saep_transf(x, alpha, sigma, mu, epsilon):
    f1 = (
        1
        / (2 * sigma * gamma(1 + 1 / alpha))
        * np.exp(-((np.abs((mu - x) / (sigma * (1 - epsilon)))) ** alpha))
    )
    f2 = (
        1
        / (2 * sigma * gamma(1 + 1 / alpha))
        * np.exp(-((np.abs((x - mu) / (sigma * (1 + epsilon)))) ** alpha))
    )
    return np.where(x <= mu, f1, f2)

class ModelDetails(QtWidgets.QWidget):
    # Define a signal that will be emitted when data changes
    model_details_updated = Signal(tuple)
    
    def __init__(self, raw_df):
        super().__init__()
        self.raw_df = column_to_datetime(raw_df, 'obs')
        self.data = self.raw_df
        
        # Defaults
        self.current_start_date = self.data.iloc[:, 0].min().date()
        self.current_end_date = self.data.iloc[:, 0].max().date()
        self.current_kpi = "log(ben_sal_gro_.crosssection.)"
        # self.current_kpi = "log(kpi_sal_rev_onl_exist)"
        self.current_start_date = datetime(2021,4,11).date()
        self.current_end_date = datetime(2024,1,28).date()
        self.xs_weights = "Weights"
        self.current_log_trans_bias = "No"
        self.current_take_anti_logs_at_midpoints = "Yes"
        
        # Change defaults to lowercase
        self.current_kpi = self.current_kpi.lower()
        self.xs_weights = self.xs_weights.lower()
        self.current_log_trans_bias = self.current_log_trans_bias.lower()
        self.current_take_anti_logs_at_midpoints = self.current_take_anti_logs_at_midpoints.lower()
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setup_date_selection()
        self.setup_variable_selection()
        self.setup_xs_weights_selection()
        self.setup_log_trans_bias()
        self.setup_take_anti_logs_at_midpoints()

        # Internal state to store updates without emitting
        self.updated_model_details = lowercase_strings((
            self.current_kpi, 
            self.current_start_date, 
            self.current_end_date,
            self.xs_weights,
            self.current_log_trans_bias,
            self.current_take_anti_logs_at_midpoints))
        
    def setup_date_selection(self):
        """Create widgets for selecting the date range."""
        date_layout = QtWidgets.QHBoxLayout()

        # Start date
        self.start_date_edit = self.create_date_edit(self.current_start_date)
        date_layout.addWidget(QtWidgets.QLabel("Start Date:"))
        date_layout.addWidget(self.start_date_edit)

        # End date
        self.end_date_edit = self.create_date_edit(self.current_end_date)
        date_layout.addWidget(QtWidgets.QLabel("End Date:"))
        date_layout.addWidget(self.end_date_edit)

        self.layout.addLayout(date_layout)

        # Connect signals
        self.start_date_edit.dateChanged.connect(self.update_dates)
        self.end_date_edit.dateChanged.connect(self.update_dates)

    def setup_variable_selection(self):
        """Create widgets for selecting the KPI."""
        kpi_layout = QtWidgets.QHBoxLayout()

        self.variable_input = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(self.data.columns[1:])
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.variable_input.setCompleter(completer)
        self.variable_input.setText(self.current_kpi)

        kpi_layout.addWidget(QtWidgets.QLabel("Select KPI:"))
        kpi_layout.addWidget(self.variable_input)

        self.layout.addLayout(kpi_layout)

        # Connect signal
        self.variable_input.textChanged.connect(self.update_variable)

    def setup_log_trans_bias(self):
        """Create widgets for log transformation adjustment bias to be on or not."""
        log_trans_bias_layout = QtWidgets.QHBoxLayout()
        self.yes_no_dropdown = QtWidgets.QComboBox()
        self.yes_no_dropdown.addItem("Yes")
        self.yes_no_dropdown.addItem("No")
        
        log_trans_bias_layout.addWidget(QtWidgets.QLabel("Adjust for log trans bias:"))
        log_trans_bias_layout.addWidget(self.yes_no_dropdown)
        
        self.layout.addLayout(log_trans_bias_layout)
        
        # Connect signal
        self.variable_input.textChanged.connect(self.update_log_trans_bias)

    def setup_take_anti_logs_at_midpoints(self):
        """Create widgets for log transformation adjustment bias to be on or not."""
        take_anti_logs_at_midpoints_layout = QtWidgets.QHBoxLayout()
        self.yes_no_dropdown = QtWidgets.QComboBox()
        self.yes_no_dropdown.addItem("Yes")
        self.yes_no_dropdown.addItem("No")
        
        take_anti_logs_at_midpoints_layout.addWidget(QtWidgets.QLabel("Take Anti-logs at midpoints:"))
        take_anti_logs_at_midpoints_layout.addWidget(self.yes_no_dropdown)
        
        self.layout.addLayout(take_anti_logs_at_midpoints_layout)
        
        # Connect signal
        self.variable_input.textChanged.connect(self.update_take_anti_logs_at_midpoints)

    @staticmethod
    def create_date_edit(initial_date):
        """Helper to create a QDateEdit with a calendar popup."""
        date_edit = QtWidgets.QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QtCore.QDate(initial_date))
        return date_edit

    def setup_xs_weights_selection(self):
        """Create widgets for selecting the xs weights."""
        xs_weights_layout = QtWidgets.QHBoxLayout()

        self.variable_input = QtWidgets.QLineEdit()
        self.variable_input.setText(self.xs_weights)

        xs_weights_layout.addWidget(QtWidgets.QLabel("Select Weights:"))
        xs_weights_layout.addWidget(self.variable_input)

        self.layout.addLayout(xs_weights_layout)

        # Connect signal
        self.variable_input.textChanged.connect(self.update_variable)
    
    def update_variable(self, new_variable):
        """Update the selected variable."""
        self.updated_model_details = lowercase_strings((
            new_variable,
            self.updated_model_details[1],
            self.updated_model_details[2],
            self.updated_model_details[3],
            self.updated_model_details[4],
            self.updated_model_details[5]
        ))

    def update_dates(self):
        """Update the selected dates."""
        self.updated_model_details = lowercase_strings((
            self.updated_model_details[0],
            self.start_date_edit.date().toPython(), 
            self.end_date_edit.date().toPython(),
            self.updated_model_details[3],
            self.updated_model_details[4],
            self.updated_model_details[5]
        ))
    
    def update_log_trans_bias(self, new_variable):
        """Update the take anti-logs at midpoint"""
        self.updated_model_details = lowercase_strings((
            self.updated_model_details[0],
            self.updated_model_details[1],
            self.updated_model_details[2],
            self.updated_model_details[3],
            new_variable,
            self.updated_model_details[5]
        ))
    
    def update_take_anti_logs_at_midpoints(self, new_variable):
        """Update the log trans bias"""
        self.updated_model_details = lowercase_strings((
            self.updated_model_details[0],
            self.updated_model_details[1],
            self.updated_model_details[2],
            self.updated_model_details[3],
            self.updated_model_details[4],
            new_variable
        ))
        
    def update_xs_weights(self, new_variable):
        """Update the log trans bias"""
        self.updated_model_details = lowercase_strings((
            self.updated_model_details[0],
            self.updated_model_details[1],
            self.updated_model_details[2],
            new_variable,
            self.updated_model_details[4],
            self.updated_model_details[5]
        ))
        
    def emit_current_model_details(self):
        """Emit the current model details explicitly when requested."""
        self.model_details_updated.emit(self.updated_model_details)

class RawData(QtWidgets.QWidget):
    class PandasTableModel(QAbstractTableModel):
        def __init__(self, data, visible_columns):
            super().__init__()
            self._data = data
            self._visible_columns = visible_columns

        def rowCount(self, parent=None):
            return self._data.shape[0]

        def columnCount(self, parent=None):
            return self._data.shape[1]

        def data(self, index, role=Qt.DisplayRole):
            if role == Qt.DisplayRole:
                if 0 <= index.row() < self._data.shape[0] and 0 <= index.column() < self._data.shape[1]:
                    return str(self._data.iat[index.row(), index.column()])
            return None

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if role == Qt.DisplayRole:
                if orientation == Qt.Horizontal:
                    return self._data.columns[section]
                elif orientation == Qt.Vertical:
                    return str(self._data.index[section])
            return None
        
        def set_data(self, new_data, visible_columns):
            """Update the model's data and reset the view."""
            self._data = new_data
            self._visible_columns = visible_columns
            self.layoutChanged.emit()

    def __init__(self, raw_df):
        super().__init__()

        # Convert column to datetime
        self.raw_df = column_to_datetime(raw_df, 'obs')  # Convert to datetime once

        # Convert float columns to float32
        self.raw_df = self.raw_df.astype({col: 'float32' for col in self.raw_df.select_dtypes(include='float').columns})
        self.data = self.raw_df

        # Create layout and table view and search bar
        self.layout = QtWidgets.QVBoxLayout(self)
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setPlaceholderText("Search for variable...")
        self.layout.addWidget(self.search_bar)
        self.table_view = QtWidgets.QTableView(self)
        self.layout.addWidget(self.table_view)

        # Set initial visible columns (start with all columns)
        self.visible_columns = list(range(self.data.shape[1]))
        
        # Set model
        self.model = self.PandasTableModel(self.data, self.visible_columns)
        self.table_view.setModel(self.model)

        # Connect to the search bar to filter data
        self.search_bar.textChanged.connect(self.search)
        
        # Resize only visible columns
        self.resize_visible_columns(self.table_view)

        # Connect the dynamic resizing to the viewport update
        self.table_view.horizontalScrollBar().valueChanged.connect(
            lambda: self.resize_visible_columns(self.table_view)
        )

    def resize_visible_columns(self, table_view):
        """Resize only the visible columns dynamically as they come into view."""
        header = table_view.horizontalHeader()
        visible_rect = table_view.viewport().rect()

        for col in range(header.count()):
            column_pos = table_view.columnViewportPosition(col)

            # Check if column is visible
            if visible_rect.left() <= column_pos < visible_rect.right():
                # Resize the visible column to fit its contents
                table_view.resizeColumnToContents(col)
    
    def search(self):
        """Search for a term in the dataframe and update the view by filtering columns."""
        query = self.search_bar.text().lower()

        # If no query is entered, show all columns
        if not query:
            self.visible_columns = list(range(self.data.shape[1]))
            filtered_data = self.raw_df
        else:
            # Filter columns based on the search query
            matching_columns = [
                col for col in self.raw_df.columns
                if query in col.lower()  # Match column names based on the search query
            ]
            matching_columns_indices = [self.raw_df.columns.get_loc(col) for col in matching_columns]
            filtered_data = self.raw_df[['obs']+matching_columns]
            self.visible_columns = matching_columns_indices

        # Update the table model with the filtered data and visible columns
        self.model.set_data(filtered_data, self.visible_columns)

class VariableDetails(QtWidgets.QWidget):
    variable_details_updated = Signal(pd.DataFrame)
    transformed_dict_updated = Signal(dict)
    model_results_dict_updated = Signal(dict)
    request_model_details = Signal()
    request_xs_details = Signal()
    regression_complete = Signal()
    regression_requested = Signal()

    def __init__(self, raw_df: pd.DataFrame, model_details_input: Tuple, xs_details_input: pd.DataFrame):
        super().__init__()
        self.regression_run = False
        self.data_frame = raw_df
        self.model_details_input = model_details_input
        self.xs_details_input = xs_details_input
        self.transformed_data_window = None
        self.contribution_window = None
        self.decomp_data_window = None
        self.category_colors = {}

        self.layout = QtWidgets.QVBoxLayout(self)
        self.table_widget = QTableWidget(self)
        self.setup_table_widget()

        self.add_button = QtWidgets.QPushButton("Add Variable Row")
        self.add_button.clicked.connect(self.add_variable_row)
        self.layout.addWidget(self.add_button)
        
        self.copy_button = QtWidgets.QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.layout.addWidget(self.copy_button)
        
        self.import_button = QtWidgets.QPushButton("Import Variable Details from File")
        self.import_button.clicked.connect(self.import_from_file)
        self.layout.addWidget(self.import_button)

        self.regression_button = QtWidgets.QPushButton("Run Regression")
        self.regression_button.clicked.connect(self.handle_run_regression)
        self.layout.addWidget(self.regression_button)

        # Automatically import a default file during development
        default_file_path = r"C:\Users\Tom Gray\im-sciences.com\FileShare - MasterDrive\Dev\04 - Python Modelling Toolkit\02 - Code, Implementation & Testing\V0.2 - A sample outlook on UX\Example Variable Details.xlsx"
        if default_file_path:  # Only attempt if the path is set
            self.import_from_file(default_file_path)
        
    def import_from_file(self, file_path: Optional[str] = None):
        """Opens a file dialog to import a DataFrame and populate the table."""
        if not file_path:  # If no file path is provided, open a dialog
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open File", "", "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
            )
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.endswith(".xlsx"):
                    df = pd.read_excel(file_path)
                else:
                    QtWidgets.QMessageBox.warning(self, "Invalid File", "Unsupported file format. Needs to be .xlsx or .csv")
                    return
                
                # Validate if the headers match the expected table columns
                expected_columns = [
                    'variable', 'xs grouping', 'reference point', 'interval', 'category',
                    'coeff min', 'coeff max', 'importance', 'short variable name',
                    'substitution', 'prior', 'notes', 'remove'
                ]
                
                # For check make the columns lower
                df.columns = df.columns.str.lower()
                
                if not all(col in df.columns for col in expected_columns):
                    QtWidgets.QMessageBox.warning(self, "Invalid Data", "The file does not have the required headers.")
                    return
                
                # Make the column headers upper again and replace nan with ""
                df.rename(columns={
                    'variable':'Variable',
                    'xs grouping':"XS Grouping", 
                    'reference point':"Reference Point", 
                    'interval':"Interval",
                    'category':"Category",
                    'coeff min':"Coeff Min",
                    'coeff max':"Coeff Max",
                    'importance':"Importance",
                    'short variable name':"Short Variable Name",
                    'substitution':"Substitution",
                    'prior':"Prior",
                    'notes':"Notes",
                    'remove':"Remove"
                },inplace=True)
                
                # Populate the QTableWidget with the DataFrame
                self.populate_table_from_dataframe(df)

            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load the file: {e}")
    
    def populate_table_from_dataframe(self, df: pd.DataFrame):
        """Populates the QTableWidget with data from the DataFrame."""
        # Set the table's headers based on the DataFrame's columns
        self.table_widget.setColumnCount(len(df.columns))
        self.table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Clear any existing rows
        self.table_widget.setRowCount(0)

        # Populate rows
        for row_idx, row in df.iterrows():
            self.table_widget.insertRow(row_idx)
            for col_idx, col_name in enumerate(df.columns):
                value = row.get(col_name, "")
                if col_name == 'Remove':
                    # Special handling for the "Remove" column with a button
                    remove_button = self.create_remove_button(row_idx)
                    self.table_widget.setCellWidget(row_idx, col_idx, remove_button)
                else:
                    # Create a QLineEdit for editable cells
                    line_edit = QtWidgets.QLineEdit(str(value))
                    self.table_widget.setCellWidget(row_idx, col_idx, line_edit)
    
    def copy_to_clipboard(self):
        """Copy dataframe to clipboard"""
        dataframe = self.run_regression()
        dataframe.to_clipboard(index=False, excel=True)
        print("DataFrame copied to clipboard")
    
    def export_to_excel(self):
        """Export variable details to excel"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Excel File", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            dataframe = self.run_regression()
            dataframe.to_excel(file_path, index=False)
            print(f"DataFrame exported to {file_path}")
    
    def setup_table_widget(self):
        """Configures the QTableWidget."""
        self.table_widget.setColumnCount(13)
        self.table_widget.setHorizontalHeaderLabels([
            'Variable',
            'XS Grouping',
            'Reference Point',
            'Interval',
            'Category',
            'Coeff Min',
            'Coeff Max',
            'Importance',
            'Short Variable Name',
            'Substitution',
            'Prior',
            'Notes',
            'Remove'])
        
        # Set up the context menu only for right-click on the header
        self.table_widget.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.horizontalHeader().customContextMenuRequested.connect(self.on_column_header_context_menu)
        
        self.layout.addWidget(self.table_widget)

    def on_column_header_context_menu(self, pos):
        """Handles the context menu event for column headers."""
        index = self.table_widget.horizontalHeader().logicalIndexAt(pos)
        if index != -1:
            # Only trigger filter action for the right-clicked column
            filter_action = QtGui.QAction("Filter", self)
            filter_action.triggered.connect(lambda checked, col=index: self.open_filter_dialog(col))
            
            # Clear filter action to unfilter rows
            clear_filter_action = QtGui.QAction("Clear Filter", self)
            clear_filter_action.triggered.connect(self.unfilter_rows)  # Unfilter when triggered

            # Create and show the context menu with the filter option
            menu = QtWidgets.QMenu(self.table_widget)
            menu.addAction(filter_action)
            menu.addAction(clear_filter_action)
            menu.exec_(self.table_widget.viewport().mapToGlobal(pos))

    def open_filter_dialog(self, column):
        """Open a dialog or input box to filter data by column."""
        print(f"Filtering column {column + 1}")  # Adjust for 1-based column index
        text, ok = QtWidgets.QInputDialog.getText(self, f"Filter column {column + 1}", f"Enter filter text for column {column + 1}:")
        if ok and text:
            # Apply the filter to the appropriate column here
            self.apply_filter(column, text)
    
    def apply_filter(self, column, text):
        """Applies a filter to the specified column."""
        # Loop through all rows in the QTableWidget
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, column)
            
            # Check if the cell contains a QTableWidgetItem
            if item:
                item_text = item.text().lower()  # Get the text and make it case-insensitive
            else:
                # Check if the cell contains a widget like QLineEdit
                widget = self.table_widget.cellWidget(row, column)
                if widget and isinstance(widget, QtWidgets.QLineEdit):
                    item_text = widget.text().lower()  # Get the text from the QLineEdit
                else:
                    item_text = ""  # Handle empty or None items
            
            # Try to handle numeric filtering (if it's an integer or float)
            try:
                item_value = float(item_text)  # Attempt to convert the value to float
                text_value = float(text)  # Convert the filter text to float as well
                if item_value != text_value:
                    self.table_widget.setRowHidden(row, True)  # Hide row if values don't match
                else:
                    self.table_widget.setRowHidden(row, False)  # Show row if values match
            except ValueError:
                # If the conversion fails, treat the column as a string for filtering
                if text.lower() not in item_text:
                    self.table_widget.setRowHidden(row, True)
                else:
                    self.table_widget.setRowHidden(row, False)
    
    def unfilter_rows(self):
        """Resets the filter and makes all rows visible."""
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setRowHidden(row, False)  # Make all rows visible
    
    def add_variable_row(self):
        """Adds a new row to the table."""
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        
        variable_input = self.create_transform_input()
        xs_input = self.create_line_reader_input()
        reference_point_input = self.create_line_reader_input()
        interval_input = self.create_line_reader_input()
        category_input = self.create_category_input(row_position)
        coeff_min_input = self.create_line_reader_input()
        coeff_max_input = self.create_line_reader_input()
        importance_input = self.create_line_reader_input()
        short_variable_name_input = self.create_line_reader_input()
        subsitution_input = self.create_line_reader_input()
        prior_input = self.create_line_reader_input()
        notes_input = self.create_line_reader_input()
        remove_button = self.create_remove_button(row_position)

        self.table_widget.setCellWidget(row_position, 0, variable_input)
        self.table_widget.setCellWidget(row_position, 1, xs_input)
        self.table_widget.setCellWidget(row_position, 2, reference_point_input)
        self.table_widget.setCellWidget(row_position, 3, interval_input)
        self.table_widget.setCellWidget(row_position, 4, category_input)
        self.table_widget.setCellWidget(row_position, 5, coeff_min_input)
        self.table_widget.setCellWidget(row_position, 6, coeff_max_input)
        self.table_widget.setCellWidget(row_position, 7, importance_input)
        self.table_widget.setCellWidget(row_position, 8, short_variable_name_input)
        self.table_widget.setCellWidget(row_position, 9, subsitution_input)
        self.table_widget.setCellWidget(row_position, 10, prior_input)
        self.table_widget.setCellWidget(row_position, 11, notes_input)
        self.table_widget.setCellWidget(row_position, 12, remove_button)

    def create_line_reader_input(self) -> QtWidgets.QLineEdit:
        """Creates a QLineEdit for all basic inputs"""
        line_edit = QtWidgets.QLineEdit(self)
        return line_edit
    
    def create_category_input(self,row_position:int) -> QtWidgets.QLineEdit:
        """Creates a QLineEdit with auto-completion for categories with dynamic suggestions."""
        line_edit = QtWidgets.QLineEdit(self)
        
        # Create the completer
        completer = QtWidgets.QCompleter(self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        line_edit.setCompleter(completer)

        # Create a model that will be updated with existing categories from the table
        category_model = QtCore.QStringListModel([])
        completer.setModel(category_model)

        # Store the model in the QLineEdit's property to access later
        line_edit.setProperty("category_model", category_model)

        # Connect the textChanged signal to update the completer suggestions
        line_edit.textChanged.connect(lambda text: self.update_category_completer(text, line_edit, row_position))

        return line_edit
    
    def update_category_completer(self, text: str, line_edit: QtWidgets.QLineEdit, row_position: int):
        """Update the completer suggestions based on entered text, using already entered categories."""
        # Get the index of the 'Category' column by searching the header
        category_column_index = None
        for col in range(self.table_widget.columnCount()):
            header_item = self.table_widget.horizontalHeaderItem(col)
            if header_item and header_item.text().lower() == "category":  # Compare header text (case-insensitive)
                category_column_index = col
                break
        
        if category_column_index is None:
            print("Category column not found.")
            return
        
        # Get all existing categories from the table using the dynamically found column index
        existing_categories = []
        for row in range(self.table_widget.rowCount()):
            category_input = self.table_widget.cellWidget(row, category_column_index)  # Use the dynamic index
            if category_input:
                existing_categories.append(category_input.text())

        # Add the new category text to the list (if it's not already there)
        if text and text not in existing_categories:
            existing_categories.append(text)

        # Filter suggestions by entered text
        filtered_categories = [cat for cat in existing_categories if cat.lower().startswith(text.lower())]

        # Get the model from the QLineEdit property and update it
        category_model = line_edit.property("category_model")
        category_model.setStringList(filtered_categories)

        # If the category is new, assign a new color
        if text and text not in self.category_colors:
            self.category_colors[text] = self.get_new_color()

        # Update the row's background color
        self.update_row_color(row_position, text)
    
    def update_row_color(self, row_position: int, category: str):
        """Updates the row's background color based on the assigned category color."""
        color = self.category_colors.get(category, None)
        if color:
            # Update the background color for the category cell widget (QLineEdit)
            category_input = self.table_widget.cellWidget(row_position, 1)
            if category_input:
                category_input.setStyleSheet(f"background-color: {color};")
            
            # Update the background color for the rest of the cells in the row (QTableWidgetItem)
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row_position, col)
                if item:
                    item.setBackground(QtGui.QColor(color))
                else:
                    # For widget cells (like Remove button), you can set the background of the parent widget
                    widget = self.table_widget.cellWidget(row_position, col)
                    if widget:
                        widget.setStyleSheet(f"background-color: {color};")

    def get_new_color(self):
        """Generate a random dark color for a new category."""
        # Ensures the color is dark enough for white text visibility
        r = random.randint(0, 127)  # Dark red
        g = random.randint(0, 127)  # Dark green
        b = random.randint(0, 127)  # Dark blue
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def create_transform_input(self) -> QtWidgets.QLineEdit:
        """Creates a QLineEdit with auto-completion for transformed variables with dynamic suggestions."""
        # Initialize the QLineEdit
        line_edit = QtWidgets.QLineEdit(self)
        
        # Create the completer
        self.completer = QtWidgets.QCompleter(self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        line_edit.setCompleter(self.completer)

        # Initialize the headers and model
        self.headers = self.data_frame.columns.tolist()
        self.completer_model = QtCore.QStringListModel(self.headers)
        self.completer.setModel(self.completer_model)

        # Connect the textChanged signal to the update method
        line_edit.textChanged.connect(self.update_completer)

        return line_edit
    
    def update_completer(self, text: str):
        """Updates the completer suggestions based on the current text."""
        # Split the text to check the last entered token
        tokens = re.split(r'(\W)', text)  # Split by non-word characters (operators, spaces, etc.)
        last_token = tokens[-1].strip() if tokens else ""

        # If the last token is an operator or empty (first input after operator)
        if last_token in {'+', '-', '*', '/', '**', ',', '(', ')', 'OBS'} or not last_token:
            # Check if a letter is typed after the operator
            if text and text[-1].isalpha():
                # Get the first letter typed after the operator
                first_letter = text[-1].lower()

                # Filter headers based on the first letter typed after an operator
                filtered_headers = [header for header in self.headers if header.lower().startswith(first_letter)]
                self.completer_model.setStringList(filtered_headers)  # Update the model with filtered suggestions

                # Ensure the dropdown appears with the updated suggestions
                self.completer.complete()
                self.completer.popup().show()
                QtCore.QCoreApplication.processEvents()  # Ensure the UI updates immediately
        else:
            # Reset the completer to show all headers if no operator was typed
            self.completer_model.setStringList(self.headers)
            self.completer.complete()
            self.completer.popup().show()

    def create_dropdown(self, options: List[str]) -> QtWidgets.QComboBox:
        """Creates a QComboBox populated with the given options."""
        combo = QtWidgets.QComboBox(self)
        combo.addItems(options)
        return combo

    def create_remove_button(self, row_position: int) -> QtWidgets.QPushButton:
        """Creates a remove button for a specific row."""
        button = QtWidgets.QPushButton("❌", self)
        button.clicked.connect(lambda: self.remove_row(row_position))
        return button

    def remove_row(self, row_position: int):
        """Removes a row from the table."""
        self.table_widget.removeRow(row_position)

    def get_variable_details(self):
        """Create variable details dataframe"""
        data = []  # To store all rows as dictionaries
        headers = [self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())]

        for row in range(self.table_widget.rowCount()):
            row_data = {}
            for col in range(self.table_widget.columnCount()):
                # Skip processing if the column has a QPushButton
                cell_widget = self.table_widget.cellWidget(row, col)
                if isinstance(cell_widget, QtWidgets.QPushButton):
                    continue

                # Process QLineEdit or QTableWidgetItem cells
                if isinstance(cell_widget, QtWidgets.QLineEdit):
                    row_data[headers[col]] = cell_widget.text()
                else:
                    item = self.table_widget.item(row, col)
                    row_data[headers[col]] = item.text() if item else None
            
            data.append(row_data)
            
        # Convert the collected data to a DataFrame
        self.variable_details_input_df = pd.DataFrame(data)
        self.variable_details_input_df.columns = self.variable_details_input_df.columns.str.lower()
        self.variable_details_input_df = self.variable_details_input_df.apply(
            lambda col: col.map(lambda x: x.lower() if isinstance(x, str) else x)
        )
        
        return self.variable_details_input_df
    def run_regression(self, variable_details_input_df):
        """Handles regression execution."""
        # Start overall timer
        overall_start_time = time.time()
        
        print("REGRESSION RUNNING")
        self.regression_run = True

        # Start timer for the first section
        start_time = time.time()

        variable_details_input_df = self.get_variable_details()

        # End timer for the first section and print elapsed time
        print(f"Time for get_variable_details: {time.time() - start_time:.2f} seconds")
        
        # Start timer for the second section
        start_time = time.time()

        # Pass data to TransformedData
        self.transformed_data_window = TransformedData(
            self.data_frame, self.model_details_input, variable_details_input_df, self.xs_details_input,
        )
        
        # End timer for the second section and print elapsed time
        print(f"Time for TransformedData initialization: {time.time() - start_time:.2f} seconds")

        # Start timer for the third section
        start_time = time.time()

        # Pass transformed data to Contribution
        self.transformed_dict = self.transformed_data_window.transform_data(
            self.data_frame, self.model_details_input, variable_details_input_df, self.xs_details_input
        )
        
        # # Pass transformed data to Contribution
        # self.transformed_dict = TransformedData(self.data_frame, self.model_details_input, variable_details_input_df, self.xs_details_input).transform_data(
        #     self.data_frame, self.model_details_input, variable_details_input_df
        # )

        # End timer for the third section and print elapsed time
        print(f"Time for transform_data: {time.time() - start_time:.2f} seconds")

        # Start timer for the fourth section
        start_time = time.time()

        # Pass Model Stats to Model Stats and Model Results to Decomp
        self.contribution_window = Contribution(
            self.model_details_input,
            self.xs_details_input,
            variable_details_input_df,
            self.transformed_dict
        )

        # End timer for the fourth section and print elapsed time
        print(f"Time for Contribution initialization: {time.time() - start_time:.2f} seconds")

        # Start timer for the regression itself
        start_time = time.time()

        # Run regression
        # self.model_results, self.model_diagnostics, self.predicted_values, self.residuals = self.contribution_window.ols_regression()
        self.model_results_dict = self.contribution_window.ols_regression()

        # End timer for regression and print elapsed time
        print(f"Time for ols_regression: {time.time() - start_time:.2f} seconds")

        # Start timer for the emissions
        start_time = time.time()

        # Pass updated variables to the decomp window
        # self.decomp_data_window = Decomp(
        #     self.model_details_input,
        #     variable_details_input_df,
        #     self.transformed_dict,
        #     self.model_results,
        #     self.model_diagnostics,
        #     self.predicted_values
        # )
        
        self.variable_details_updated.emit(variable_details_input_df)
        self.transformed_dict_updated.emit(self.transformed_dict)
        self.model_results_dict_updated.emit(self.model_results_dict)
        self.regression_complete.emit()

        # End timer for the emissions and print elapsed time
        print(f"Time for emissions: {time.time() - start_time:.2f} seconds")

        # Print total time for the entire regression
        print(f"Total time for regression: {time.time() - overall_start_time:.2f} seconds")

        print("REGRESSION COMPLETED")

        return variable_details_input_df,self.transformed_dict,self.model_results_dict
    
    def handle_run_regression(self):
        """Requests model details before running regression.""" 
        self.regression_requested.emit()

    def receive_model_details(self, model_details):
        """Receive updated model details and run regression."""
        self.model_details_input = model_details

class XSDetails(QtWidgets.QWidget):
    xs_details_updated = Signal(pd.DataFrame)
    
    def __init__(self, raw_df, model_details_input):
        super().__init__()
        self.raw_df = raw_df
        self.model_details_input = model_details_input
    
        self.layout = QtWidgets.QVBoxLayout(self)
        
        self.table_widget = QtWidgets.QTableWidget(self)
        self.layout.addWidget(self.table_widget)
        
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)
        
        # Add buttons for row and column operations
        self.add_row_button = QtWidgets.QPushButton("Add Row", self)
        self.buttons_layout.addWidget(self.add_row_button)
        self.add_row_button.clicked.connect(self.add_row)
        
        self.add_column_button = QtWidgets.QPushButton("Add Column", self)
        self.buttons_layout.addWidget(self.add_column_button)
        self.add_column_button.clicked.connect(self.add_column)
        
        # Add the option to import the file (hardcoded path)
        self.import_button = QtWidgets.QPushButton("Import XS Details From File", self)
        self.buttons_layout.addWidget(self.import_button)
        self.import_button.clicked.connect(self.import_file)
        
        # Enable custom context menu for headers
        self.table_widget.horizontalHeader().setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.horizontalHeader().customContextMenuRequested.connect(self.show_context_menu)
        
        # Add in functionality for selection columns and rows and deleting them
        # self.table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        # # self.table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        # # self.table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)
        
        self.file_path = r"C:\Users\Tom Gray\im-sciences.com\FileShare - MasterDrive\Dev\04 - Python Modelling Toolkit\02 - Code, Implementation & Testing\V0.2 - A sample outlook on UX\Example XS Details.xlsx"
        self.populate_table()
    
    def import_file(self):
        """Import an Excel file with a hardcoded path."""
        # Hardcoded file path
        file_path = r"C:\Users\Tom Gray\im-sciences.com\FileShare - MasterDrive\Dev\04 - Python Modelling Toolkit\02 - Code, Implementation & Testing\V0.2 - A sample outlook on UX\Example XS Details.xlsx"  # Replace this with your actual file path
        
        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file_path)
            # Here you can process the df if needed before using it
            print(f"File {file_path} imported successfully.")
            self.raw_df = df  # Update the raw_df with the imported DataFrame
        except Exception as e:
            print(f"Error importing file: {e}")
            
    def populate_table(self):
        """Create initial xs details table"""
        if self.file_path:
            try:
                # Load the data from the file into a DataFrame
                df = pd.read_excel(self.file_path)

                # Set the number of rows and columns
                self.table_widget.setRowCount(len(df))
                self.table_widget.setColumnCount(len(df.columns))

                # Set the table headers
                self.table_widget.setHorizontalHeaderLabels(df.columns.tolist())

                # Populate the table with data
                for row in range(len(df)):
                    for col in range(len(df.columns)):
                        item = QtWidgets.QTableWidgetItem(str(df.iloc[row, col]))
                        self.table_widget.setItem(row, col, item)
                        
            except Exception as e:
                print(f"Error populating table from file: {e}")
        else:
            # Default behavior: Use raw_df and model_details_input
            xs_list = self.get_xs(self.raw_df, self.model_details_input)

            # Set number of columns (for CrossSection, Region, SubRegion)
            self.table_widget.setColumnCount(1)

            # Set the table headers
            self.table_widget.setHorizontalHeaderLabels(['Cross Section'])

            # Set row count
            self.table_widget.setRowCount(len(xs_list))

            # Loop through xs_list and populate the first column with QLineEdit widgets
            for row, xs in enumerate(xs_list):
                line_edit = QtWidgets.QLineEdit(xs)
                self.table_widget.setCellWidget(row, 0, line_edit)

    def show_context_menu(self, position):
        """Show context menu to rename the header"""
        header = self.table_widget.horizontalHeader()
        index = header.logicalIndexAt(position.x())
        if index == -1:
            return

        # Create a context menu
        menu = QMenu(self)
        rename_action = menu.addAction("Rename Header")

        # Show the menu at the position of the right-click
        action = menu.exec(self.mapToGlobal(position))
        if action == rename_action:
            self.rename_header(index)

    def rename_header(self, index):
        """Rename a header when the rename option is selected"""
        # Get the current header text
        current_header_item = self.table_widget.horizontalHeaderItem(index)
        current_text = current_header_item.text() if current_header_item else ""

        # Show input dialog to get the new header text
        new_text, ok = QInputDialog.getText(self, "Rename Header", "Enter new header name:", text=current_text)
        if ok and new_text.strip():
            if not current_header_item:
                current_header_item = QTableWidgetItem()
                self.table_widget.setHorizontalHeaderItem(index, current_header_item)
            current_header_item.setText(new_text.strip())

    def get_xs(self, raw_df, model_details_input):
        """Get options for panels"""
        
        def remove_log_and_crosssection(s):
            """Removes log string and .. where there is a cross section"""
            # Remove log() wrapper
            s = re.sub(r"^log\((.*)\)$", r"\1", s)  # Removes log() around the string

            # Remove .x. where x is any string (e.g., ".crosssection." becomes "")
            s = re.sub(r"\.[^\.]*\.", "", s)  # Remove .x. pattern

            return s
        
        # Find raw kpi
        raw_kpi = remove_log_and_crosssection(model_details_input[0])
        
        # Get list of xs
        xs_list = [] 
        for col in list(raw_df.columns):
            if col.startswith(raw_kpi + "_"):  # Check if column starts with raw_kpi_
                kpi_xs = col
                xs = kpi_xs.replace(raw_kpi + "_", "")  # Remove the raw_kpi prefix
                xs = xs.lower()  # Convert to lowercase
                xs_list.append(xs)  # Append to the list
        
        return xs_list

    def add_row(self):
        """Add a new row to the table"""
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        
        # Add QLineEdit for the new row
        line_edit = QtWidgets.QLineEdit()
        self.table_widget.setCellWidget(row_position, 0, line_edit)

    def add_column(self):
        """Add a new column to the table"""
        column_position = self.table_widget.columnCount()
        self.table_widget.insertColumn(column_position)
        
        # Set header text for the new column
        self.set_column_headers()

        # Add empty QLineEdit widgets for all rows in the new column
        for row in range(self.table_widget.rowCount()):
            line_edit = QtWidgets.QLineEdit()
            self.table_widget.setCellWidget(row, column_position, line_edit)

    def set_column_headers(self):
        """Set the column headers based on QLineEdits, including the first column"""
        for col in range(self.table_widget.columnCount()):  # Loop through all columns
            header_item = self.table_widget.horizontalHeaderItem(col)
            
            if header_item is None:
                header_item = QtWidgets.QTableWidgetItem("Column " + str(col + 1))
                self.table_widget.setHorizontalHeaderItem(col, header_item)

            header_item.setText(header_item.text())  # Allow editing directly in the header
            self.table_widget.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.Stretch)
    
    def get_xs_details(self):
        """Create variable details dataframe"""
        data = []  # To store all rows as dictionaries
        headers = [self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())]

        for row in range(self.table_widget.rowCount()):
            row_data = {}
            for col in range(self.table_widget.columnCount()):
                # Skip processing if the column has a QPushButton
                cell_widget = self.table_widget.cellWidget(row, col)
                if isinstance(cell_widget, QtWidgets.QPushButton):
                    continue

                # Process QLineEdit or QTableWidgetItem cells
                if isinstance(cell_widget, QtWidgets.QLineEdit):
                    row_data[headers[col]] = cell_widget.text()
                else:
                    item = self.table_widget.item(row, col)
                    row_data[headers[col]] = item.text() if item else None
            
            data.append(row_data)
            
        # Convert the collected data to a DataFrame
        self.xs_details_input_df = pd.DataFrame(data)

        # Convert headers to lower
        self.xs_details_input_df.columns = self.xs_details_input_df.columns.str.lower()
        
        # Convert strings to lower
        self.xs_details_input_df[self.xs_details_input_df.select_dtypes(include=['object']).columns] = self.xs_details_input_df.select_dtypes(include=['object']).apply(lambda x: x.str.lower())

        
        return self.xs_details_input_df

    def emit_current_xs_details(self):
        """Emit the current xs details explicitly when requested."""
        updated_xs_details_input_df = self.get_xs_details()
        self.xs_details_updated.emit(updated_xs_details_input_df)
    
class TransformedData(QtWidgets.QWidget):
    def __init__(self, raw_df, model_details_input, variable_details_input_df, xs_details_input):
        super().__init__()
        self.raw_df = raw_df
        self.model_details_input = model_details_input
        self.variable_details_input_df = variable_details_input_df
        self.xs_details_input_df = xs_details_input
        
        # # Tran
        # self.transformed_dict = self.transform_data(self.raw_df,self.model_details_input,self.variable_details_input_df)
        
        # Create widgets
        self.create_widgets()
        self.setLayout(self.layout)
        
    def create_widgets(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Create a QTableWidget to display the DataFrame
        self.table_widget = QTableWidget()
        self.layout.addWidget(self.table_widget)

        # Populate the table with the transformed DataFrame data
        self.populate_table()

        # Create an "Export to Excel" button
        self.export_button = QtWidgets.QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)  # Connect to the export function
        self.layout.addWidget(self.export_button)
        
    def populate_table(self):
        """Populate the QTableWidget with DataFrame data."""
        # Set the number of rows and columns based on the transformed DataFrame
        transformed_dict_all_perm = self.transform_data(self.raw_df,self.model_details_input,self.variable_details_input_df,self.xs_details_input_df)
        self.transformed_df = pd.DataFrame(transformed_dict_all_perm[1])
        # self.transformed_df = pd.DataFrame(self.transformed_dict)
        rows, cols = self.transformed_df.shape
        self.table_widget.setRowCount(rows)
        self.table_widget.setColumnCount(cols)
        
        # Set the column headers
        self.table_widget.setHorizontalHeaderLabels(self.transformed_df.columns)
        
        # Convert values to strings and populate the table (optimized by using `.values`)
        data = self.transformed_df.values
        for row in range(rows):
            for col in range(cols):
                # Set each item in the table from the DataFrame values
                self.table_widget.setItem(row, col, QTableWidgetItem(str(data[row, col])))
        
        # Resize columns to fit the contents
        self.table_widget.resizeColumnsToContents()

    def export_to_excel(self):
        """Export the transformed DataFrame to an Excel file."""
        # Open a file dialog to choose the save location
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save File", "", "Excel Files (*.xlsx);;All Files (*)", options=options
        )

        # If a file path is selected, save the DataFrame to the file
        if file_path:
            try:
                self.transformed_df.to_excel(file_path, index=False)
                print(f"Data exported successfully to {file_path}")
            except Exception as e:
                print(f"Failed to export data: {e}")
    
    def apply_reference_point(self, variable_details_input_df, key, transformed_value, permutations_dict, dates):
        """Apply reference point to transformed data"""
        # If referring to the date col
        if key == 'obs':
            return transformed_value
        
        reference_point_dict = {row[0]: row[2] for row in variable_details_input_df.values}
        
        # If there are permutations update the dictionary to reflect which permutation is being used
        if "¬" in key:
            pattern = r"¬\d+"
            key = re.sub(pattern, lambda match: str(permutations_dict.get(match.group(0), match.group(0))), key)
        reference_point = reference_point_dict.get(key, 0)
        
        # Compute the reference value
        if reference_point in ["nan", None, 0]:
            reference_value = 0
        elif reference_point.lower() == "min":
            reference_value = np.min(transformed_value[dates])
        elif reference_point.lower() == "max":
            reference_value = np.max(transformed_value[dates])
        else:
            reference_value = pd.to_numeric(reference_point, errors="coerce") or 0

        # Adjust the transformed value by the reference point
        return transformed_value - reference_value

    # def create_xs_raw_df(self, raw_df, model_details_input, xs_details_input_df, variable_details_input_df):
        
    #     # Get KPI data
    #     kpi, start_date, end_date, _, _ = model_details_input
        
    #     # Get var details and change to dictionary
    #     var_xs_dict = ims.convert_2_df_cols_to_dict(variable_details_input_df,'variable','xs grouping')
    #     var_by_xs_dict = {key:value for key,value in var_xs_dict.items() if value != 'nan'}

    #     for xs in list(xs_details_input_df['crosssection']):
    #         # Create dataframe by crosssection
    #         # if
    #         # xs

            
            
    #         def extract_between_dots(s):
    #             """Find anything with strings between two dots"""
    #             pattern = r"\.(.*?)\."
    #             matches = re.findall(pattern, s)
    #             return s,matches
            
    #         # Check if variables have transformations
    #         var_list = list(variable_details_input_df["variable"])
    #         xs_var_list = []
    #         for var in var_list:
    #             # Extract variable and xs to use
    #             xs_var,xs_to_use = extract_between_dots(var)
    #             xs_var_list.append((xs_var,xs_to_use))
    #         # print(xs_var_list)
            
    #         # Check is XS Grouping is anything other than none or empty
    
    def invert_nested_dict(self, input_dict):
        """Function to invert nested dictionaries"""
        inverted_dict = {}

        for outer_key, inner_dict in input_dict.items():
            inverted_dict[outer_key] = defaultdict(list)
            
            for key, value in inner_dict.items():
                inverted_dict[outer_key][value].append(key)
            
            # Convert defaultdict to normal dict
            inverted_dict[outer_key] = dict(inverted_dict[outer_key])
        
        return inverted_dict
    
    def transform_data(self, raw_df, model_details_input, variable_details_input_df, xs_details_input_df):
        """Prepare data and metadata"""
        
        # Read in the data
        raw_df = raw_df.copy()
        raw_df.columns = raw_df.columns.str.lower()
        raw_df['obs'] = pd.to_datetime(raw_df['obs'])
        kpi, start_date, end_date, _, _, _ = model_details_input
        
        # Process xs details
        xs_details_input_df.columns = xs_details_input_df.columns.str.lower()
        xs_details_input_df[xs_details_input_df.select_dtypes(include=['object']).columns] = xs_details_input_df.select_dtypes(include=['object']).apply(lambda x: x.str.lower())
        unique_xs_list = xs_details_input_df['crosssection'].unique().tolist()
        
        # Create dictionary to know which variables need seperate coefficients by crosssection
        var_xs_grouping_dict = ims.convert_2_df_cols_to_dict(variable_details_input_df,'variable','xs grouping')
        var_xs_grouping_dict = {key:value for key,value in var_xs_grouping_dict.items() if value != 'nan'}

        # # Create dictionary for each xs grouping and what cross sections they contain
        all_columns = xs_details_input_df.columns.tolist()
        filtered_columns = [col for col in all_columns if col != 'crosssection']
        init_xs_dict = {}
        for i in filtered_columns:
            init_xs_dict[i] = ims.convert_2_df_cols_to_dict(xs_details_input_df,'crosssection',i)
        # Invert the input dictionary
        xs_grouping_dict = self.invert_nested_dict(init_xs_dict)

        # Convert start and end dates to datetime
        start_date = np.datetime64(pd.to_datetime(start_date))
        end_date = np.datetime64(pd.to_datetime(end_date))
        
        # Convert the raw DataFrame to a NumPy array and map column indices
        raw_array = raw_df.to_numpy()
        columns = {col: idx for idx, col in enumerate(raw_df.columns)}
        
        # Assuming raw_array is a numpy array with datetime data
        obs_idx = columns["obs"]
        obs = np.full((len(raw_array),), np.datetime64('NaT', 'ns'), dtype="datetime64[ns]")
        obs[:] = np.array(pd.to_datetime(raw_array[:, obs_idx], dayfirst=True), dtype="datetime64[ns]")

        # Define the date range mask and apply it
        date_mask = (obs >= start_date) & (obs <= end_date)
        transformed_dict = {"obs": obs}
        combinations_dict = {"obs": obs}
        
        # Create a raw dictionary
        pd_date_mask = (raw_df['obs'] >= start_date) & (raw_df['obs'] <= end_date)
        raw_dict = raw_df.to_dict(orient='list')
        keys_to_convert = [key for key in raw_dict.keys() if key != "obs" and key != "xslist"]
        for key in keys_to_convert:
            if key in raw_dict:
                raw_dict[key] = np.array(raw_dict[key])
        
        # Create the cross sections column in the combinations dict
        obs_len = len(combinations_dict['obs'])
        xs_list = []
        for xs in unique_xs_list:
            # Add the cross-section to the combinations dict
            list_for_xs = [xs]*obs_len
            xs_list.extend(list_for_xs)
        xs_obs_array = np.array(xs_list,dtype=object)
        combinations_dict["xslist"]=xs_obs_array
        
        # Extend the obs col by the number of xs
        combinations_dict['obs'] = np.tile(combinations_dict['obs'], len(unique_xs_list)) 
        
        # Check if permuations have been introudced
        if not variable_details_input_df["substitution"].isna().all():
            # Create a dictionary mapping variable names to permutations
            substitutions = (
                variable_details_input_df[["variable", "substitution"]]
                .dropna()
                .set_index("variable")["substitution"]
                .to_dict()
                )

            permutations = self.parse_substitution(substitutions)

            # Iterate through the original dictionary
            for key, value_dict in permutations.items():
                # For each key, we create combinations of the values for all nested keys
                if value_dict == None:  # Single variable
                    combinations_dict[key] = None
                else:  # Multiple variables
                    sub_keys = list(value_dict.keys())
                    values = list(value_dict.values())
                    
                    # Generate all combinations of the values
                    all_combinations = list(itertools.product(*values))
                    
                    # Store the combinations as dictionaries of key-value pairs
                    combinations = [
                        {sub_keys[i]: comb[i] for i in range(len(sub_keys))} for comb in all_combinations
                    ]
                    combinations_dict[key] = combinations

        else:
            combinations_dict = [{}]
        
        # Create the possible permutations across all the keys
        combinations_dict_perm = {key: value for key, value in combinations_dict.items() if '¬' in key}
        list_of_values = list(combinations_dict_perm.values())

        all_permutations = {}
        for idx, combo in enumerate(itertools.product(*list_of_values), 1):
            # Combine the dictionaries from the current combination
            combined_dict = {}
            for d in combo:
                combined_dict.update(d)
            all_permutations[idx] = combined_dict

        # Edit combinations_dict to remove transformations
        for key,value in combinations_dict.items():
            if key != "obs" and key != "xslist":
                combinations_dict[key] = None

        # Transform other variables
        self.transformed_dict_all_perm = {}
        transformed_results_cache = {}
        
        # Create a dataset for each permutation of the data
        for perm_number, perm_combination in all_permutations.items():
            panel_dict = {}
            # Stack the dataset by crosssection
            for xs in unique_xs_list:
                # # Apply the mask to filter to xs in dictionary
                panel_mask = combinations_dict["xslist"] == xs
                masked_combinations_dict = {key: value[panel_mask] if value is not None else value for key, value in combinations_dict.items()}
                transformed_dict = {} 
                for key, value in masked_combinations_dict.items():
                    if key == "xslist":
                        transformed_dict[key] = value
                    elif "¬" not in key:
                        # If no permutations are applied
                        cache_key = f"{kpi}_{xs}_{key}"
                        if cache_key not in transformed_results_cache:
                            transformed_results_cache[cache_key] = self.apply_transformation(raw_dict, kpi, xs, xs_grouping_dict)
                            transformed_results_cache[cache_key] = self.apply_reference_point(variable_details_input_df, kpi, transformed_results_cache[cache_key], perm_combination, date_mask)
                        transformed_dict[kpi] = transformed_results_cache[cache_key]
                        # Check is variable is used over multiple cross-sections
                        cache_key = f"{key}_{xs}_{key}"
                        if key in var_xs_grouping_dict:
                            if cache_key not in transformed_results_cache:
                                transformed_results_cache[cache_key] = self.apply_transformation(raw_dict, key, xs, xs_grouping_dict)
                                transformed_results_cache[cache_key] = self.apply_reference_point(variable_details_input_df, key, transformed_results_cache[cache_key], perm_combination, date_mask)
                                # Rename dict key based on xs number
                                transformed_dict[f"{key}_μ_{xs}"] = transformed_results_cache[cache_key]
                            transformed_dict[f"{key}_μ_{xs}"] = transformed_results_cache[cache_key]
                        else:
                            # print("Key check",key)
                            if key not in transformed_results_cache:
                                transformed_results_cache[cache_key] = self.apply_transformation(raw_dict, key, xs, xs_grouping_dict)
                                transformed_results_cache[cache_key] = self.apply_reference_point(variable_details_input_df, key, transformed_results_cache[cache_key], perm_combination, date_mask)
                            transformed_dict[key] = transformed_results_cache[cache_key]
                    else:
                        pattern = r"¬\d+"
                        key_perm = re.sub(pattern, lambda match: str(perm_combination.get(match.group(0), match.group(0))), key)
                        cache_key = f"{key_perm}_{xs}"
                        # Cache the transformed key result
                        if cache_key not in transformed_results_cache:
                            transformed_results_cache[cache_key] = self.apply_transformation(raw_dict, key_perm)
                            transformed_results_cache[cache_key] = self.apply_reference_point(variable_details_input_df, key_perm, transformed_results_cache[cache_key], perm_combination, date_mask)
                        transformed_dict[key_perm] = transformed_results_cache[cache_key]

                panel_dict[xs] = transformed_dict
            
            # Combine all datasets into a single panel DataFrame
            panel_data = []
            for dataset_key, dataset in panel_dict.items():
                dataset_df = pd.DataFrame(dataset)
                dataset_df['dataset_key'] = dataset_key  # Add dataset_key column
                panel_data.append(dataset_df)
            # Concatenate into a single DataFrame
            panel_df = pd.concat(panel_data, axis=0)
            panel_df.fillna(0,inplace=True)
            panel_df.drop('dataset_key', axis=1, inplace=True)
            
            # Reorder df
            # Columns to move to the front
            columns_to_move = ["obs", "xslist"]

            # Reorder and group the DataFrame
            new_column_order = columns_to_move + [col for col in panel_df.columns if col not in columns_to_move]
            panel_df = panel_df[new_column_order]
            panel_df = panel_df[pd_date_mask]
            
            # Reorder for "μ" columns
            panel_df = self.reorder_df(panel_df)
            
        self.transformed_dict_all_perm[perm_number] = panel_df

        return self.transformed_dict_all_perm
    
    def reorder_df(self, df):
        """Reorder the DataFrame to move columns with "μ" to be groups."""
        # Extract columns with "μ"
        columns_with_mu = [col for col in df.columns if "μ" in col]

        if len(columns_with_mu) == 0:
            return df
        else:
            grouped_by_prefix = {}

            # Group the `μ` columns by the substring before "μ"
            for col in columns_with_mu:
                prefix = col.split("μ")[0].strip("_")
                grouped_by_prefix.setdefault(prefix, []).append(col)

            # Rebuild the column order while keeping non-μ columns in place
            final_columns = []
            seen_columns = set()  # Keep track of added columns to avoid duplic
            for col in df.columns:
                if col in columns_with_mu and col not in seen_columns:
                    # Access the relevant group of μ columns
                    prefix = col.split("μ")[0].strip("_")
                    mu_cols_to_append = grouped_by_prefix[prefix]
                    
                    # Append all grouped columns if not already added
                    for mu_col in mu_cols_to_append:
                        if mu_col not in seen_columns:
                            final_columns.append(mu_col)
                            seen_columns.add(mu_col)
                elif col not in seen_columns:
                    # Keep non-μ columns in their original order
                    final_columns.append(col)
                    seen_columns.add(col)

            # Reorder the DataFrame
            reordered_df = df[final_columns]
            
            return reordered_df
    
    def parse_substitution(self, substitutions):
        """Parse the substitution strings to extract adstock transformations."""
        adstock_pattern = r"(¬\d+)\(([^)]+)\)"
        parsed_results = {}

        for var, expression in substitutions.items():
            
            # Skip NaN substitutions
            if pd.isna(expression) and expression != "nan":
                continue

            # Ensure the expression is a string
            if not isinstance(expression, str):
                raise TypeError(f"Expected string or NaN for variable '{var}', got {type(expression).__name__}")
            
            # Match the adstock pattern
            matches = re.findall(adstock_pattern, expression)
            
            if not matches:
                parsed_results[var] = None
            else:
                parsed_results[var] = {
                    key: [float(value) for value in values.split(",")]
                    for key, values in matches
                }
        return parsed_results
    
    def replace_rhs(self, match):
        """Function to replace the right-hand side with datetime objects"""
        operator = match.group(1)  # Capture the operator (>=, <=, etc.)
        rhs = match.group(2)  # Capture the right-hand side of the operator
        
        # # Convert the right-hand side string to a datetime object
        date_obj = np.datetime64(datetime.strptime(rhs, "%Y-%m-%d"))
        
        # Return the transformed expression, with datetime object
        return f"{operator} np.datetime64('{date_obj}')"
        # return f"{operator} np.datetime64('{date_obj_np}')"

    
    def get_variable_value(self, variable, raw_array, column_map):
        """Return the raw column data for a variable."""
        if variable in column_map:
            col_idx = column_map[variable]
            return raw_array[:, col_idx]
        else:
            print(f"Warning: Variable '{variable}' not found. Returning None.")
            return None
    
    def evaluate_xs_expression(self, expression):
        """Evaluate logical expressions like ('.region.' == 'ang') and replace them with 1 or 0."""
        # Recursive resolution of logical comparisons
        while re.search(r"\(([^()]+)\s*(==|!=)\s*([^()]+)\)", expression):
            match = re.search(r"\(([^()]+)\s*(==|!=)\s*([^()]+)\)", expression)
            if match:
                lhs = match.group(1).strip()
                operator = match.group(2).strip()
                rhs = match.group(3).strip()
                # Evaluate the comparison
                result = 1 if (lhs == rhs and operator == "==") or (lhs != rhs and operator == "!=") else 0
                # Replace the matched comparison in the expression
                expression = expression[:match.start()] + str(result) + expression[match.end():]
            
        return expression
    
    def show_error(self, error_message):
        """Display the error message in a copyable message box."""
        error_box = QtWidgets.QMessageBox()
        error_box.setIcon(QtWidgets.QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        
        # Create a QWidget to hold the layout and add QTextEdit inside
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Create a QTextEdit widget to allow the error message to be copied
        text_edit = QtWidgets.QTextEdit()
        text_edit.setText(error_message)  # Set the error message as text
        text_edit.setReadOnly(True)  # Make it read-only but selectable
        text_edit.setStyleSheet("font-family: Courier New; font-size: 10pt;")  # Optional: Set font for better readability
        
        # Add the QTextEdit widget to the layout
        layout.addWidget(text_edit)
        
        # Set the custom widget as the central widget in the QMessageBox
        error_box.setCentralWidget(widget)
        
        # Display the message box
        error_box.exec()

    def apply_transformation(self, raw_dict, expression, crosssection, crosssection_dict):
        """Apply complex transformations with nested functions and operators using eval."""
        
        # Define supported functions dynamically (like log, exp, etc.)
        supported_functions = {
            "log": np.log,
            "exp": np.exp,
            "sqrt": np.sqrt,
            "abs": np.abs,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "lag": apply_lag,  # Add lag, lead, etc. if needed
            "lead": apply_lead,
            "adstock": adstock,
            "dimret_adstock": dimret_adstock,
            "n_adstock": n_adstock,
            "dimret": dimret,
            "n_dimret": n_dimret,
            "saep_transf": saep_transf,
        }

        # Preprocess expression for crosssection references
        matches = re.findall(r"\.(\w+)\.", expression)
        if matches:
            if matches[0] == 'crosssection':
                expression = re.sub(r"\.(\w+)\.", crosssection, expression)
                if "==" in expression or "!=" in expression:
                    expression = self.evaluate_xs_expression(expression)
            else:
                included_xs = crosssection_dict.get(matches[0], [])
                if crosssection in included_xs:
                    expression = re.sub(r"\.(\w+)\.", crosssection, expression)
                    if "==" in expression or "!=" in expression:
                        expression = self.evaluate_xs_expression(expression)

        # Create processing for obs
        if "(obs" in expression:
            # Regex pattern to capture the right-hand side of the operator
            operator_pattern = r"(>=|<=|>|<|==|!=)\s*'([^']+)'"
            # Replace the right-hand side of operators with datetime objects
            expression = re.sub(operator_pattern, self.replace_rhs, expression)

        # Replace column names in the expression with corresponding dictionary lookups
        # Identify keys present in the expression
        keys_in_expression = [key for key in raw_dict.keys() if key in expression]

        # Create a regex pattern for the relevant keys
        keys = map(re.escape, keys_in_expression)
        pattern = re.compile(r'\b(' + '|'.join(keys) + r')\b')

        # Replace only the relevant keys
        expression = pattern.sub(lambda match: f"raw_dict['{match.group(0)}']", expression)

        # Create a safe environment for eval
        safe_locals = {
            "np": np,
            **supported_functions,
            "raw_dict": raw_dict
        }

        # Use eval to evaluate the expression safely within the restricted environment
        try:
            result = eval(expression, {"__builtins__": None}, safe_locals)
        except Exception as e:
            print(f"Error evaluating expression '{expression}': {e}")
            self.show_error(f"Error evaluating expression '{expression}': {e}")
            return np.nan

        return result

    def update_transformed_data(self, model_details_input=None, variable_details_input_df=None):
        """Update the transformed data when new model or variable details are provided."""
        if model_details_input:
            self.model_details_input = model_details_input  # Update model details
        # if variable_details_input_df:
        if variable_details_input_df is not None and not variable_details_input_df.empty:
            self.variable_details_input = variable_details_input_df  # Update variable details
        
        # Re-transform data based on new inputs
        self.transformed_dict = self.transform_data(self.raw_df, self.model_details_input, self.variable_details_input_df)
        
        # Repopulate the table with the updated data
        self.populate_table()

class Contribution(QtWidgets.QWidget):
    def __init__(self, model_details_input, xs_details_input_df, variable_details_input_df, transformed_dict):
        super().__init__()
        self.model_details_input = model_details_input
        self.xs_details_input_df = xs_details_input_df
        self.variable_details_input_df = variable_details_input_df
        self.transformed_dict = transformed_dict
        self.model_results = None

        # Create widgets
        self.create_widgets()
        self.setLayout(self.layout)
        
    def create_widgets(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.table_widget = QtWidgets.QTableWidget(self)
        self.layout.addWidget(self.table_widget)
        
    def update_transformed_dict(self, transformed_dict=None):
        """Update the transformed data when new model or variable details are provided."""
        # if transformed_df is not None and isinstance(transformed_df, pd.DataFrame) and not transformed_df.empty:
        if transformed_dict:
            self.transformed_dict = transformed_dict  # Update model details
            # Populate the table
            # self.results,self.diagnostics,self.model_predictions = self.ols_regression()

            # if self.results:
                # self.populate_table(self.results)
    
    def update_variable_details_input_df(self,variable_details_input_df):
        """Update variable details input df with new data"""
        if variable_details_input_df is not None and variable_details_input_df.empty:
            self.variable_details_input_df = variable_details_input_df

    def update_model_results(self, model_results):
        # if model_results is not None:
        """Update the table with the regression results."""
        self.results = model_results
        self.populate_table(self.results)
    
    # def run_ols_for_dataset(self, dataset_key, transformed_dict, variable_details_input_df, failed_datasets):
    #     """Run OLS regression for a single dataset using scipy minimize with bounds."""
    #     try:
    #         # Extract data for the current dataset
    #         current_data = transformed_dict[dataset_key]
            
    #         # Extract dependent and independent variables
    #         dependent_var = list(current_data.keys())[1]
    #         independent_vars = list(current_data.keys())[2:]
            
    #         # Convert to NumPy arrays for fast computation
    #         dependent_values = np.asarray(current_data[dependent_var], dtype=np.float64)
    #         independent_values = np.asarray([current_data[var] for var in independent_vars], dtype=np.float64).T  # Transpose to align
            
    #         # Filter out invalid (NaN) rows
    #         valid_rows = (
    #             np.isfinite(dependent_values) & (dependent_values != 0) & ~np.isnan(dependent_values)
    #         )
    #         dependent_values = dependent_values[valid_rows]
    #         independent_values = independent_values[valid_rows]

    #         # Initialize bounds for coefficients (if any)
    #         bounds = []
    #         if 'coeff min' in variable_details_input_df and 'coeff max' in variable_details_input_df:
    #             coeff_min = pd.to_numeric(variable_details_input_df['coeff min'], errors='coerce')
    #             coeff_max = pd.to_numeric(variable_details_input_df['coeff max'], errors='coerce')

    #             # Check if all bounds are NaN
    #             if not (coeff_min.isna().all() and coeff_max.isna().all()):
    #                 for var in independent_vars:
    #                     min_bound = variable_details_input_df.loc[variable_details_input_df['variable'] == var, 'coeff min'].values
    #                     max_bound = variable_details_input_df.loc[variable_details_input_df['variable'] == var, 'coeff max'].values

    #                     # Handle missing bounds
    #                     min_bound = None if len(min_bound) == 0 or pd.isna(min_bound[0]) else min_bound[0]
    #                     max_bound = None if len(max_bound) == 0 or pd.isna(max_bound[0]) else max_bound[0]

    #                     bounds.append((min_bound, max_bound))
    #             else:
    #                 bounds = None  # Skip bounds if all entries are NaN
            
    #         # Define RSS function
    #         def rss(params, X, y):
    #             predictions = X @ params  # Linear combination of predictors
    #             residuals = y - predictions
    #             return np.sum(residuals**2)

    #         # Initial guess for parameters
    #         initial_guess = np.zeros(independent_values.shape[1])

    #         # Run optimization
    #         result = minimize(rss, x0=initial_guess, args=(independent_values, dependent_values), bounds=bounds)
            
    #         # If optimisation fails make a note
    #         if not result.success:
    #             # Add to failed datasets list
    #             failed_datasets.append(dataset_key)

    #         # Extract model coefficents if model fails return the best attempt if optimization fails
    #         coefficients = result.x
    #         # Predicted values
    #         predicted_values = independent_values @ coefficients
    #         # Extract parameters and other model results
    #         model_results_dict = self.individual_variable_statistics(result, dependent_values, independent_values, predicted_values, independent_vars)
    #         # Residuals
    #         residuals = dependent_values - predicted_values
    #         # Diagnostics
    #         diagnostics = self.model_diagnostics(dependent_values, independent_values, predicted_values)
            
    #         return model_results_dict, diagnostics, predicted_values, residuals

    #     except Exception as e:
    #         return {"dataset": dataset_key, "error": str(e)}

    # def ols_regression(self):
    #     """Run OLS regression sequentially across datasets with bounds."""
    #     results_dict = {}  # Use a dictionary to store results
    #     failed_datasets = [] # Track failed optimisations
    #     for dataset_key in self.transformed_dict.keys():
    #         result = self.run_ols_for_dataset(dataset_key, self.transformed_dict, self.variable_details_input_df, failed_datasets)
    #         results_dict[dataset_key] = result  # Store the result with the dataset_key as the dictionary key
    #     # Add a summary of failures
    #     if failed_datasets:
    #         # results_dict["failed_datasets_summary"] = f"Failed datasets: {', '.join(failed_datasets)}"
    #         failed_message = f"The following datasets failed to have an optimal solution: {failed_datasets}"
    #         self.show_failure_popup(failed_message)

    def run_ols_for_dataset(self, dataset_key, model_details, xs_details, transformed_dict, variable_details_input_df, failed_datasets):
        """Run OLS regression for a single dataset using scipy minimize with bounds."""
        # try:
        # Extract data for the current dataset
        current_data = transformed_dict[dataset_key]

        # Identify columns that represent dummy variables (e.g., constants)
        dummy_columns = [col for col in current_data.columns if col.startswith('constant_μ')]

        if len(dummy_columns) > 0:
            # Make the first dummy a complete constant with 1s all the way through
            current_data[dummy_columns[0]] = 1
        
        # If there are xs weights apply them
        _,_,_,xs_weights,_,_ = model_details
        if xs_weights is not None:
            current_data = self.apply_xs_weights(current_data, xs_weights, xs_details)
        
        # Create fixed effects dummy array
        xs_array = pd.factorize(current_data["xslist"])[0]
        
        # Define dependent and independent variables
        dependent_var = current_data.columns[2]  # Assuming the dependent variable is the second column
        independent_vars = list(current_data.columns[3:])  # Exclude the dependent variable and 'dataset_key'

        # Convert to NumPy arrays for fast computation
        dependent_values = np.asarray(current_data[dependent_var], dtype=np.float64)
        independent_values = np.asarray(current_data[independent_vars], dtype=np.float64)
        
        # Filter out invalid (NaN) rows
        valid_rows = (
            np.isfinite(dependent_values) & (dependent_values != 0) & ~np.isnan(dependent_values)
        )
        dependent_values = dependent_values[valid_rows]
        independent_values = independent_values[valid_rows]

        # Initialize bounds for coefficients (if any)
        bounds = []
        if 'coeff min' in variable_details_input_df and 'coeff max' in variable_details_input_df:
            coeff_min = pd.to_numeric(variable_details_input_df['coeff min'], errors='coerce')
            coeff_max = pd.to_numeric(variable_details_input_df['coeff max'], errors='coerce')

            # Check if all bounds are NaN
            if not (coeff_min.isna().all() and coeff_max.isna().all()):
                for var in independent_vars:
                    min_bound = variable_details_input_df.loc[variable_details_input_df['variable'] == var, 'coeff min'].values
                    max_bound = variable_details_input_df.loc[variable_details_input_df['variable'] == var, 'coeff max'].values

                    # Handle missing bounds
                    min_bound = None if len(min_bound) == 0 or pd.isna(min_bound[0]) else min_bound[0]
                    max_bound = None if len(max_bound) == 0 or pd.isna(max_bound[0]) else max_bound[0]

                    bounds.append((min_bound, max_bound))
            else:
                bounds = None  # Skip bounds if all entries are NaN
        
        # Define RSS function
        def rss(params, X, y):
            predictions = X @ params  # Linear combination of predictors
            residuals = y - predictions
            return np.sum(residuals**2)

        # Initial guess for parameters
        # initial_guess = np.zeros(independent_values.shape[1])
        initial_guess = np.linalg.lstsq(independent_values, dependent_values, rcond=None)[0]

        # Run optimization
        result = minimize(rss, x0=initial_guess, args=(independent_values, dependent_values), bounds=bounds, method='L-BFGS-B')
        # If optimisation fails make a note
        if not result.success:
            # Add to failed datasets list
            failed_datasets.append(dataset_key)

        # Extract model coefficents if model fails return the best attempt if optimization fails
        coefficients = result.x
        
        # Predicted values
        predicted_values = independent_values @ coefficients

        # Extract parameters and other model results
        model_results_dict = self.individual_variable_statistics(result, dependent_values, independent_values, predicted_values, independent_vars)

        # Residuals
        residuals = dependent_values - predicted_values

        # Diagnostics
        if np.any(xs_array > 0):
            diagnostics = self.model_diagnostics_panel(dependent_values, independent_values, predicted_values, xs_array)
        else:
            diagnostics = self.model_diagnostics_single(dependent_values, independent_values, predicted_values)
        
        # Reverse the weights applied after diagnostic tests
        if xs_weights is not None:
            predicted_values, residuals, avm_df = self.reverse_xs_weights(dependent_var, predicted_values, current_data, xs_weights, xs_details)

        return model_results_dict, diagnostics, predicted_values, residuals, avm_df

        # except Exception as e:
        #     return {"dataset": dataset_key, "error": str(e)}

    def ols_regression(self):
        """Run OLS regression sequentially across datasets with bounds."""
        results_dict = {}  # Use a dictionary to store results
        failed_datasets = [] # Track failed optimisations
        for dataset_key in self.transformed_dict.keys():
            result = self.run_ols_for_dataset(dataset_key, self.model_details_input, self.xs_details_input_df,self.transformed_dict, self.variable_details_input_df, failed_datasets)
            results_dict[dataset_key] = result  # Store the result with the dataset_key as the dictionary key
        # Add a summary of failures
        if failed_datasets:
            # results_dict["failed_datasets_summary"] = f"Failed datasets: {', '.join(failed_datasets)}"
            failed_message = f"The following datasets failed to have an optimal solution: {failed_datasets}"
            self.show_failure_popup(failed_message)
        
        return results_dict
    
    def show_failure_popup(self, message):
        """Display a pop-up message for failed datasets."""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle("Failed Datasets")
        msg_box.setText(message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec()
    
    def reverse_xs_weights(self,dep_var, pred_vals, df, xs_w_col, xs_df):
        """Reverse the applied selected xs weights to the predicted values and residuals."""
        
        # Convert xs_df to a dictionary mapping crosssection to its weight
        xs_weight_dict = ims.convert_2_df_cols_to_dict(xs_df, key_col='crosssection', value_col=xs_w_col)

        # Convert dictionary values to float (if they are strings)
        xs_weight_dict = {k: float(v) for k, v in xs_weight_dict.items()}

        # Create df of residuals and predicted values
        avm_df = df[['obs','xslist',dep_var]]
        avm_df = avm_df.copy()
        avm_df.loc[:,'pred_vals'] = pred_vals

        # Identify numeric columns to be scaled (exclude 'obs' and 'xslist')
        num_cols = avm_df.select_dtypes(include=['number']).columns.difference(['obs','xslist'])
    
        # Apply weights row-wise
        avm_df = avm_df.copy()
        avm_df[num_cols] = avm_df[num_cols].div(avm_df['xslist'].map(xs_weight_dict).fillna(1), axis=0)

        # Calculate residuals
        avm_df.loc[:,'residuals'] = avm_df[dep_var] - avm_df['pred_vals']
        
        # Rename
        avm_df = avm_df.rename(columns={dep_var: 'acc_vals'})
        
        # Extract values
        residuals = avm_df['residuals']
        predicted_values = avm_df['pred_vals']
        
        return predicted_values, residuals, avm_df
    
    def apply_xs_weights(self, df, xs_w_col, xs_df):
        """Apply the selected xs weights to the dataset."""
        
        # Convert xs_df to a dictionary mapping crosssection to its weight
        xs_weight_dict = ims.convert_2_df_cols_to_dict(xs_df, key_col='crosssection', value_col=xs_w_col)

        # Convert dictionary values to float (if they are strings)
        xs_weight_dict = {k: float(v) for k, v in xs_weight_dict.items()}

        # Identify numeric columns to be scaled (exclude 'obs' and 'xslist')
        num_cols = df.select_dtypes(include=['number']).columns.difference(['obs', 'xslist'])

        # Apply weights row-wise
        df[num_cols] = df.apply(lambda row: row[num_cols] * xs_weight_dict.get(row['xslist'], 1), axis=1)
                
        return df
    
    def model_diagnostics_single(self, y_true, X, y_pred):
        """Extract model diagnostics for time series data with single crosssection"""
        
        residuals = y_true - y_pred
        n = len(y_true)  # Number of observations
        k = X.shape[1]  # Number of independent variables (including constant)
        
        # Calculate Degrees of Freedom (DF)
        dof_model = k - 1  # Degrees of freedom for the model (excluding intercept)
        dof_residual = n - k  # Degrees of freedom for residuals

        # Residual Sum of Squares (RSS) and Total Sum of Squares (TSS)
        rss = np.sum(residuals**2)
        tss = np.sum((y_true - np.mean(y_true))**2)

        # R-squared and Adjusted R-squared
        r_squared = 1 - (rss / tss)
        adj_r_squared = 1 - ((1 - r_squared) * (n - 1) / dof_residual)

        # Model error variance (Residual Variance) and model standard error
        model_error_variance = (residuals**2).sum() / dof_residual  # Variance of residuals (error variance)
        model_standard_error = model_error_variance**0.5  # Standard deviation of residuals
        
        # Akaike Information Criterion (AIC) and Bayesian Information Criterion (BIC)
        aic = n * np.log(rss / n) + 2 * k
        bic = n * np.log(rss / n) + k * np.log(n)

        # Diagnostics from `statsmodels`
        dw_stat = durbin_watson(residuals)  # Durbin-Watson
        ljungbox_stat = acorr_ljungbox(residuals, lags=[10], return_df=True)  # Ljung-Box
        lb_stat = ljungbox_stat.iloc[0]["lb_stat"]
        lb_pvalue = ljungbox_stat.iloc[0]["lb_pvalue"]

        # Breusch-Godfrey for serial correlation
        bg_stat, bg_pvalue, _, _ = acorr_breusch_godfrey(sm.OLS(residuals, X).fit())

        # Breusch-Pagan for heteroscedasticity
        bp_stat, bp_pvalue, _, _ = het_breuschpagan(residuals, X)
        
        # White test for heteroscedasticity
        try:
            white_test_results = het_white(residuals, X)
            # If the results are valid, unpack the tuple
            white_stat, white_pvalue, _, _ = white_test_results
        except Exception as e:
            white_stat, white_pvalue, _, _ = (np.nan, np.nan, np.nan, np.nan)
            print("XTX design matrix is singular and cannot be inverted due to multicollinearity")

        # ARCH test for heteroscedasticity
        arch_stat, arch_pvalue, _, _ = het_arch(residuals)
        
        # Ramsey RESET test for functional form
        reset_stat = linear_reset(sm.OLS(y_true, X).fit(), power=2).statistic
        reset_pvalue = linear_reset(sm.OLS(y_true, X).fit(), power=2).pvalue

        # Jarque-Bera test for normality
        jb_stat, jb_pvalue, _, _ = jarque_bera(residuals)

        # Lilliefors test for normality
        lilliefors_stat, lilliefors_pvalue = lilliefors(residuals)

        diagnostics = [
            ("R-squared", "Model fit", r_squared, "N/A"),
            ("Adj R-squared", "Model fit", adj_r_squared, "N/A"),
            ("Variable Count", "Model fit", k, "N/A"),
            ("Observation Count", "Topline", n, "N/A"),
            ("Degrees of Freedom (Model)", "Topline", dof_model, "N/A"),
            ("Degrees of Freedom (Residuals)", "Topline", dof_residual, "N/A"),
            ("Model Error Variance", "Model fit", model_error_variance, "N/A"),
            ("Model Standard Error", "Model fit", model_standard_error, "N/A"),
            ("AIC", "Model fit", aic, "N/A"),
            ("BIC", "Model fit", bic, "N/A"),
            ("Durbin-Watson Statistic", "Serial correlation", dw_stat, "N/A"),
            ("Ljung-Box Stat", "Serial correlation", lb_stat, lb_pvalue),
            ("Breusch-Godfrey Stat", "Serial correlation", bg_stat, bg_pvalue),
            ("Breusch-Pagan Stat", "Heteroscedasticity", bp_stat, bp_pvalue),
            ("White Test Stat", "Heteroscedasticity", white_stat, white_pvalue),
            ("ARCH1 Stat", "Heteroscedasticity", arch_stat, arch_pvalue),
            ("Ramsey RESET Stat", "Functional form", reset_stat, reset_pvalue),
            ("Jarque-Bera Stat", "Normality of residual", jb_stat, jb_pvalue),
            ("Lilliefors Stat", "Normality of residual", lilliefors_stat, lilliefors_pvalue)
        ]

        return diagnostics
    
    def model_diagnostics_panel(self, y_true, X, y_pred, entity_ids):
        """Extract model diagnostics for panel data"""

        residuals = y_true - y_pred
        n = len(y_true)  # Number of observations
        k = X.shape[1]  # Number of independent variables (including constant)

        # Calculate Degrees of Freedom (DF)
        dof_model = k - 1  # Degrees of freedom for the model (excluding intercept)
        dof_residual = n - k  # Degrees of freedom for residuals

        # Residual Sum of Squares (RSS) and Total Sum of Squares (TSS)
        rss = np.sum(residuals**2)
        tss = np.sum((y_true - np.mean(y_true))**2)

        # R-squared and Adjusted R-squared
        r_squared = 1 - (rss / tss)
        adj_r_squared = 1 - ((1 - r_squared) * (n - 1) / dof_residual)

        # Model error variance (Residual Variance) and model standard error
        model_error_variance = (residuals**2).sum() / dof_residual  # Variance of residuals (error variance)
        model_standard_error = model_error_variance**0.5  # Standard deviation of residuals

        # Akaike Information Criterion (AIC) and Bayesian Information Criterion (BIC)
        aic = n * np.log(rss / n) + 2 * k
        bic = n * np.log(rss / n) + k * np.log(n)

        # Diagnostics
        # 1. Cross-sectional dependence test (Pesaran's CD test)
        try:
            cd_test_stat = compare.PesaranCD(residuals).stat
            cd_test_pvalue = compare.PesaranCD(residuals).pval
        except Exception:
            cd_test_stat,cd_test_pvalue = np.nan, np.nan

        # 2. Serial correlation (Wooldridge test for panel data)
        try:
            wooldridge_stat, wooldridge_pvalue = compare.WooldridgeTestSerialCorrelation(residuals, entity_ids)
        except Exception:
            wooldridge_stat, wooldridge_pvalue = np.nan, np.nan

        # 3. Heteroscedasticity (Modified Breusch-Pagan test for panel data)
        try:
            bp_stat, bp_pvalue = het_breuschpagan(residuals, X)
        except Exception:
            bp_stat, bp_pvalue = np.nan, np.nan

        # 4. Ramsey RESET test for functional form
        reset_stat = linear_reset(sm.OLS(y_true, X).fit(), power=2).statistic
        reset_pvalue = linear_reset(sm.OLS(y_true, X).fit(), power=2).pvalue

        # 5. Hausman test (Fixed vs Random Effects)
        try:
            hausman_test_stat, hausman_pvalue = compare.HausmanTest(entity_ids, X).statistic, compare.HausmanTest(entity_ids, X).pval
        except Exception:
            hausman_test_stat, hausman_pvalue = np.nan, np.nan

        # 6. Normality tests
        try:
            jb_stat, jb_pvalue = jarque_bera(residuals)
        except Exception:
            jb_stat, jb_pvalue = np.nan, np.nan

        diagnostics = [
            ("R-squared", "Model fit", r_squared, "N/A"),
            ("Adj R-squared", "Model fit", adj_r_squared, "N/A"),
            ("Variable Count", "Model fit", k, "N/A"),
            ("Observation Count", "Topline", n, "N/A"),
            ("Degrees of Freedom (Model)", "Topline", dof_model, "N/A"),
            ("Degrees of Freedom (Residuals)", "Topline", dof_residual, "N/A"),
            ("Model Error Variance", "Model fit", model_error_variance, "N/A"),
            ("Model Standard Error", "Model fit", model_standard_error, "N/A"),
            ("AIC", "Model fit", aic, "N/A"),
            ("BIC", "Model fit", bic, "N/A"),
            ("Pesaran's CD Test Stat", "Cross-sectional dependence", cd_test_stat, cd_test_pvalue),
            ("Wooldridge Stat", "Serial correlation", wooldridge_stat, wooldridge_pvalue),
            ("Breusch-Pagan Stat", "Heteroscedasticity", bp_stat, bp_pvalue),
            ("Ramsey RESET Stat", "Functional form", reset_stat, reset_pvalue),
            ("Hausman Test Stat", "Fixed vs Random Effects", hausman_test_stat, hausman_pvalue),
            ("Jarque-Bera Stat", "Normality of residual", jb_stat, jb_pvalue)
        ]

        return diagnostics
    
    def individual_variable_statistics(self, result, y_true, X, y_pred, independent_vars):
        """ Create a dictionary of coefficients, standard errors, t stats, p values, and confidence intervals"""
        if not result:
            return  # Return early if results are not available
        
        # Extract regression coefficients
        params = result.x  # Coefficients from minimize result (result.x is the optimal parameters)

        # Residuals
        residuals = y_true - y_pred

        # Degrees of freedom and number of observations
        n = len(y_true)
        k = X.shape[1]
        dof_residual = n - k

        # Calculate standard errors (using residuals and X matrix)
        residual_sum_of_squares = np.sum(residuals**2)
        
        # Debug: Check rank and shape of X^T * X
        xtx = np.dot(X.T, X)
        rank = np.linalg.matrix_rank(xtx)
        print("Rank of X^T * X:", rank)
        print("Shape of X^T * X:", xtx.shape)
        try:
            # Attempt to compute the inverse
            xtx_inv = np.linalg.inv(xtx)
            print("Inverse of X^T * X used")
        except np.linalg.LinAlgError:
            # Fall back to pseudo-inverse if singular
            xtx_inv = np.linalg.pinv(xtx)
            print("Pseudo-inverse of X^T * X used")
            
        var_beta = xtx_inv * residual_sum_of_squares / dof_residual
        standard_errors = np.sqrt(np.diagonal(var_beta))
        
        # Calculate t-statistics
        t_statistics = params / standard_errors
        
        # Calculate p-values (using two-tailed t-distribution)
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_statistics), dof_residual))  # Two-tailed p-values

        # Output a nested dictionary
        results_dict = {
            var: {
                "coefficient": params[idx],
                "standard_error": standard_errors[idx],
                "t_value": t_statistics[idx],
                "p_value": p_values[idx],
            }
            for idx, var in enumerate(independent_vars)
        }

        return results_dict
        
    def populate_table(self,model_results_dict,var_details_df):
        """"Choose how we want to populate the contribution tab"""
        if len(model_results_dict) == 1:
            self.populate_single_table(model_results_dict)
        else:
            self.populate_perm_table(model_results_dict,var_details_df)
    
    def populate_single_table(self,model_results):
        """Populate the table with regression coefficients and statistics."""
        
        # Choose only the first permutation to populate the table as there is only one
        model_results_dict, _, _, _, _ = model_results[1]
        
        # Prepare table data: Coefficients, P-values, and Confidence Intervals
        table_data = []
        for variable, stats in model_results_dict.items():
            row = [
                variable,  # Variable name
                round(stats["coefficient"], 5),  # Coefficient
                round(stats["standard_error"], 5),  # Standard Error
                round(stats["t_value"], 5),  # T-statistic
                round(stats["p_value"], 5),  # P-value (rounded to 4 decimal places for precision)
            ]
            table_data.append(row)

        # Set the row count and column headers
        self.table_widget.setRowCount(len(table_data))
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(['Variable', 'Coefficient', 'Standard Error', 'T-stat', 'P-value'])
        
        # Populate the table with data
        for row_idx, row_data in enumerate(table_data):
            for col_idx, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table_widget.setItem(row_idx, col_idx, item)
                
    def populate_perm_table(self, model_results, var_details_df):
        """Populate the table with regression coefficients and statistics for multiple regressions."""
        
        # Extract `¬n` placeholders from var_details_df
        perm_map = {}
        
        for variable in list(var_details_df['variable']):
            if "¬" in variable:  # Only process variables with placeholders
                # Recursively extract all placeholders from the variable string (even nested ones)
                placeholders = self.extract_placeholders(variable)
                
                for perm_number, model_results_dict in model_results.items():
                    model_results_dict, _, _, _ = model_results[perm_number]
                    
                    for var, _ in model_results_dict.items():
                        
                        # Check if the structure of the variable (function name) matches the model variable
                        if self.match_function_structure(variable, var):
                            
                            # Extract numeric values (e.g., coefficients, values for ¬n placeholders)
                            values = re.findall(r"[\d.]+", var)

                            # Create a nested dictionary for placeholder mappings
                            if perm_number not in perm_map:
                                perm_map[perm_number] = {}
                            
                            # Map each placeholder (e.g., ¬3) to its corresponding value
                            for idx, placeholder in enumerate(placeholders):
                                if idx < len(values):  # Ensure there are enough values
                                    perm_map[perm_number][placeholder] = float(values[idx])
        
        # Prepare table data
        table_data = []
        variable_names = []
        
        for perm_key, model_results_dict in model_results.items():
            model_results_dict, _, _, _ = model_results[perm_key]
            perm_row = []
            for variable, stats in model_results_dict.items():
                if perm_key == list(model_results.keys())[0]:  # Get variable names only from the first permutation
                    variable_names.append(variable)
                
                # Collect the values for each statistic
                perm_row.extend([
                    round(stats["coefficient"], 5),  # Coefficient
                    round(stats["standard_error"], 5),  # Standard Error
                    round(stats["t_value"], 5),  # T-statistic
                    round(stats["p_value"], 5),  # P-value
                ])

            # Add the permutation row to the table data
            table_data.append(perm_row)

        # Set row and column count
        num_variables = len(variable_names)
        num_permutations = len(model_results)
        
        # We need 6 columns for each variable (Coefficient, Standard Error, T-stat, P-value, CI Lower, CI Upper)
        self.table_widget.setRowCount(num_permutations)
        self.table_widget.setColumnCount(num_variables * 4)  # 6 columns for each variable

        # Multi-level Headers
        # Top-level headers: Statistics (e.g., Coefficient, Standard Error)
        top_level_headers = ['Coefficient', 'Standard Error', 'T-stat', 'P-value']

        # Bottom-level headers: Variable names under each statistic
        bottom_level_headers = []
        for stat in top_level_headers:
            for var in variable_names:
                bottom_level_headers.append(f"{stat} {var}")
        self.table_widget.setHorizontalHeaderLabels(bottom_level_headers)
        
        # Set Vertical Headers (Row Names) 
        perm_names = []
        for perm_number,value in perm_map.items():
            row_dict = perm_map[perm_number]
            # Convert the dictionary to a string
            row_string = ", ".join([f"{key} = {value}" for key, value in row_dict.items()])
            perm_names.append(row_string)
        self.table_widget.setVerticalHeaderLabels(perm_names)
        
        # --- Populate the table with data ---
        for row_idx, perm_row in enumerate(table_data):
            for col_idx, value in enumerate(perm_row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.table_widget.setItem(row_idx, col_idx, item)
        
        # Resize columns to fit the contents
        self.table_widget.resizeColumnsToContents()
        
    def extract_placeholders(self, expression):
        """Recursively extract all ¬n placeholders from a potentially nested expression."""
        # Match any ¬n placeholders (even within nested parentheses)
        return re.findall(r"¬\d+", expression)

    def match_function_structure(self, variable, model_var):
        """Check if the function structure (e.g., function name and argument structure) of the variable matches the model variable."""
        # Extract function name and arguments from both the variable and the model variable (ignore numeric placeholders)
        var_func_name = re.match(r"^\w+", variable).group()
        model_var_func_name = re.match(r"^\w+", model_var).group()
        
        # Check if the function names match (e.g., adstock or dimret_adstock)
        return var_func_name == model_var_func_name

class ModelStats(QtWidgets.QWidget):
    def __init__(self, model_stats, residuals):
        super().__init__()
        self.model_stats = model_stats if model_stats else {}
        self.residuals = residuals
        self.setWindowTitle("Model Diagnostics")

        # Create the main layout
        self.layout = QtWidgets.QVBoxLayout(self)

        # Create the tab widget and the tabs
        self.tabs = QtWidgets.QTabWidget(self)
        self.layout.addWidget(self.tabs)

        # Create the model diagnostics tab
        self.model_diagnostics_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.model_diagnostics_tab, "Model Diagnostics")
        
        # Create the residuals histogram tab
        self.residuals_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.residuals_tab, "Residuals Histogram")
        
        # Create layout for the model diagnostics tab
        self.diagnostics_layout = QtWidgets.QVBoxLayout(self.model_diagnostics_tab)
        
        # Create and configure the table widget for model diagnostics
        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(['Test Name', 'Category', 'Test Statistic', 'P-value'])
        self.diagnostics_layout.addWidget(self.table_widget)

        # Create layout for residuals histogram tab
        self.residuals_layout = QtWidgets.QVBoxLayout(self.residuals_tab)
        
        # Create QWebEngineView for displaying Plotly figures in the residuals tab
        self.web_view = QWebEngineView()
        self.residuals_layout.addWidget(self.web_view)
        
        # Plot the histogram of residuals
        self.plot_residuals_histogram(self.residuals)

    def populate_table(self, model_stats=None):
        """Populates the table with model diagnostics."""
        if model_stats is None:  # If no argument, use self.model_stats
            model_stats = self.model_stats
        
        if not model_stats:  # Handle empty model_stats
            self.table_widget.setRowCount(0)
            return

        self.table_widget.setRowCount(len(model_stats))
        for row, (test_name, category, test_stat, p_value) in enumerate(model_stats):
            test_name_item = QtWidgets.QTableWidgetItem(str(test_name))
            test_name_item.setFlags(test_name_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table_widget.setItem(row, 0, test_name_item)

            category_item = QtWidgets.QTableWidgetItem(str(category))
            category_item.setFlags(category_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table_widget.setItem(row, 1, category_item)

            test_stat_item = QtWidgets.QTableWidgetItem(
                f"{test_stat:.4f}" if isinstance(test_stat, (int, float)) else str(test_stat)
            )
            test_stat_item.setFlags(test_stat_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table_widget.setItem(row, 2, test_stat_item)

            p_value_item = QtWidgets.QTableWidgetItem(
                f"{p_value:.4f}" if isinstance(p_value, (int, float)) else str(p_value)
            )
            p_value_item.setFlags(p_value_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table_widget.setItem(row, 3, p_value_item)

        self.table_widget.resizeColumnsToContents()

    def update_model_diagnostics(self, model_stats):
        """Updates the table with new model diagnostics."""
        if model_stats:
            self.model_stats = model_stats
            self.populate_table(model_stats)  # Pass new stats explicitly

    def plot_residuals_histogram(self, residuals):
        """Creates a histogram of the residuals and displays it in the residuals tab."""
        
        # Standardize the residuals (mean = 0, std = 1)
        standardized_residuals = (residuals - np.mean(residuals)) / np.std(residuals)
        
        fig = go.Figure()

        # Create the histogram plot for the residuals
        fig.add_trace(go.Histogram(
            x=standardized_residuals,
            nbinsx=25,  # Set the number of bins
            marker_color='rgba(255, 100, 102, 0.7)',
            hovertemplate='<b>Residual:</b> %{x:.2f}<br><b>Count:</b> %{y}<extra></extra>'
        ))

        fig.update_layout(
            title="Histogram of Residuals",
            xaxis_title="Residuals",
            yaxis_title="Frequency",
            template="plotly_dark",
            plot_bgcolor="#1E1E1E",
            paper_bgcolor="#121212",
            font=dict(color="#FFFFFF")
        )

        # Convert to HTML and load into QWebEngineView
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        self.web_view.setHtml(plot_html)

class Decomp(QtWidgets.QWidget):
    def __init__(self,model_details_input,xs_details_input,variable_details_input_df,transformed_dict,model_results,model_stats,model_predictions):
        super().__init__()
        
        self.model_details_input = model_details_input
        self.xs_details_input = xs_details_input
        self.variable_details_input_df = variable_details_input_df
        self.transformed_dict = transformed_dict
        self.model_results = model_results
        self.model_stats = model_stats
        self.model_predictions = model_predictions
        
        # Create granular decomp
        decomp = self.create_decomposition(self.model_details_input, self.xs_details_input, self.variable_details_input_df, self.transformed_dict, self.model_results,self.model_predictions)
        self.current_decomp = decomp  # Save filtered data
        self.xslist_values = sorted(decomp['xslist'].unique())
        
        # Create category decomp
        category_decomp = self.create_category_decomposition(self.variable_details_input_df,decomp)
        self.current_category_decomp = category_decomp
        
        self.layout = QtWidgets.QVBoxLayout(self)

        # Create a QTabWidget to hold the graphs and tables
        self.tabs = QtWidgets.QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Create a QWidget for each tab
        self.decomp_graph_tab = QtWidgets.QWidget()
        self.category_decomp_graph_tab = QtWidgets.QWidget()
        self.decomp_table_tab = QtWidgets.QWidget()
        self.category_decomp_table_tab = QtWidgets.QWidget()

        # Set up the layout for each tab
        self.decomp_graph_layout = QtWidgets.QVBoxLayout(self.decomp_graph_tab)
        self.category_decomp_graph_layout = QtWidgets.QVBoxLayout(self.category_decomp_graph_tab)
        self.decomp_table_layout = QtWidgets.QVBoxLayout(self.decomp_table_tab)
        self.category_decomp_table_layout = QtWidgets.QVBoxLayout(self.category_decomp_table_tab)

        # Add dropdown to "Decomposition Graph" tab
        self.dropdown_decomp = QtWidgets.QComboBox()
        self.dropdown_decomp.addItems(self.xslist_values)
        self.decomp_graph_layout.addWidget(self.dropdown_decomp)

        # Add dropdown to "Category Decomposition Graph" tab
        self.dropdown_category_decomp = QtWidgets.QComboBox()
        self.dropdown_category_decomp.addItems(self.xslist_values)
        self.category_decomp_graph_layout.addWidget(self.dropdown_category_decomp)

        # Create QWebEngineViews for each graph tab
        self.web_view_decomp = QWebEngineView()
        self.web_view_category_decomp = QWebEngineView()

        # Add QWebEngineView to each graph tab's layout
        self.decomp_graph_layout.addWidget(self.web_view_decomp)
        self.category_decomp_graph_layout.addWidget(self.web_view_category_decomp)

        # Add the tabs for the graphs
        self.tabs.addTab(self.decomp_graph_tab, "Decomposition Graph")
        self.tabs.addTab(self.category_decomp_graph_tab, "Category Decomposition Graph")

        # Create QTableWidget for each table tab
        self.decomp_table = QtWidgets.QTableWidget()
        self.category_decomp_table = QtWidgets.QTableWidget()

        # Add QTableWidget to each table tab's layout
        self.decomp_table_layout.addWidget(self.decomp_table)
        self.category_decomp_table_layout.addWidget(self.category_decomp_table)

        # Add the tabs for the tables
        self.tabs.addTab(self.decomp_table_tab, "Decomposition Table")
        self.tabs.addTab(self.category_decomp_table_tab, "Category Decomposition Table")

        # Add Export Buttons
        self.export_decomp_button = QtWidgets.QPushButton("Export Decomposition to Excel")
        self.export_category_decomp_button = QtWidgets.QPushButton("Export Category Decomposition to Excel")
        self.decomp_table_layout.addWidget(self.export_decomp_button)
        self.category_decomp_table_layout.addWidget(self.export_category_decomp_button)

        # Connect export buttons to methods
        self.export_decomp_button.clicked.connect(lambda: self.export_to_excel(decomp))
        self.export_category_decomp_button.clicked.connect(lambda: self.export_to_excel(category_decomp))

        # Initial chart rendering
        self.plot_stacked_column(decomp.loc[decomp['xslist'] == self.xslist_values[0]], self.web_view_decomp)
        self.plot_stacked_column(category_decomp.loc[category_decomp['xslist'] == self.xslist_values[0]], self.web_view_category_decomp)
        
        # Connect dropdowns to chart updates
        self.dropdown_decomp.currentTextChanged.connect(self.update_decomp_chart)
        self.dropdown_category_decomp.currentTextChanged.connect(self.update_category_decomp_chart)

        # Set tables with corresponding data
        self.populate_table(self.decomp_table, decomp)
        self.populate_table(self.category_decomp_table, category_decomp)
    
    def update_decomp_chart(self, selected_xslist):
        """Update the decomposition chart based on dropdown selection."""
        filtered_decomp = self.current_decomp[self.current_decomp['xslist'] == selected_xslist]
        self.plot_stacked_column(filtered_decomp, self.web_view_decomp)

    def update_category_decomp_chart(self, selected_xslist):
        """Update the category decomposition chart based on dropdown selection."""
        filtered_category_decomp = self.current_category_decomp[self.current_category_decomp['xslist'] == selected_xslist]
        self.plot_stacked_column(filtered_category_decomp, self.web_view_category_decomp)
    
    def plot_stacked_column(self, final_decomp_df, web_view):
        """Create the decomp chart"""
        fig = go.Figure()
        
        # Define the maximum length for legend names
        MAX_LEGEND_NAME_LENGTH = 20  # Adjust as needed
        
        """Plot a stacked area chart using Plotly and embed in QWebEngineView."""
        # Check numeric columns
        numeric_columns = final_decomp_df.select_dtypes(include='number').columns
        if numeric_columns.empty:
            QtWidgets.QMessageBox.warning(self, "Error", "No numeric columns found in the dataframe.")
            return

        # Generate a large number of unique colors using a continuous color scale
        color_map = px.colors.qualitative.Set1

        # Truncate legend names
        truncated_column_names = [
            col if len(col) <= MAX_LEGEND_NAME_LENGTH else col[:MAX_LEGEND_NAME_LENGTH - 3] + "..."
            for col in numeric_columns
        ]

        # Map truncated names back to the original column names for tooltips
        legend_name_map = dict(zip(truncated_column_names, numeric_columns))

        for i, (truncated_col, original_col) in enumerate(legend_name_map.items()):
            fig.add_trace(go.Bar(
                x=final_decomp_df['obs'],
                y=final_decomp_df[original_col],
                name=truncated_col,  # Use the truncated name in the legend
                marker_color=color_map[i % len(color_map)],  # Assign colors in order
                hovertemplate=(
                    '<b>Observation:</b> %{x}<br>'
                    f'<b>Variable:</b> {original_col}<br>'  # Show full column name in hover tooltip
                    '<b>Value:</b> %{y:.2f}<extra></extra>'
                )
            ))

        # Update layout for visual enhancements
        fig.update_layout(
            barmode='relative',  # Enable stacking
            title=dict(
                text="Decomposition",
                font=dict(size=24, color="#FFFFFF"),
                x=0.5  # Center the title
            ),
            xaxis=dict(
                title="Observation",
                tickangle=-45,  # Rotate labels for readability
                gridcolor="rgba(255,255,255,0.2)"  # Light gridlines
            ),
            yaxis=dict(
                title="Value",
                gridcolor="rgba(255,255,255,0.2)"  # Light gridlines
            ),
            legend=dict(
                title="Variables",
                orientation="v",  # Vertical legend
                x=1,              # Positioned to the right
                y=1,              # Start from the top
                xanchor="left",
                yanchor="top",
                bgcolor="#1E1E1E",  # Match the chart background
                bordercolor="#FFFFFF",
                borderwidth=1,
                font=dict(size=10),
                itemsizing="constant",  # Maintain consistent sizing
                traceorder="normal",    # Maintain the order of traces
                valign="top",           # Align the legend items to the top
            ),
            plot_bgcolor="#1E1E1E",  # Dark background for contrast
            paper_bgcolor="#121212",  # Match the outer paper with dark theme
            font=dict(color="#FFFFFF"),  # White text for readability
            template='plotly_dark',
        )

        fig.update_layout(transition_duration=500)  # Smooth transitions

        # Convert to HTML and load into QWebEngineView
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        web_view.setHtml(plot_html)
    
    def populate_table(self, table_widget, data):
        """Populate QTableWidget with data."""
        table_widget.setRowCount(len(data))
        table_widget.setColumnCount(len(data.columns))

        # Set the headers
        table_widget.setHorizontalHeaderLabels(data.columns)

        # Set the data
        for row in range(len(data)):
            for col in range(len(data.columns)):
                table_widget.setItem(row, col, QtWidgets.QTableWidgetItem(str(data.iloc[row, col])))
        
        # Autofit column widths based on content
        table_widget.resizeColumnsToContents()

    def export_to_excel(self, data):
        """Export DataFrame to Excel with a file dialog."""
        # Show a file dialog to choose where to save the file
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setDefaultSuffix(".xlsx")
        file_path, _ = file_dialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")

        if file_path:
            data.to_excel(file_path, index=False)
            QtWidgets.QMessageBox.information(self, "Export Successful", f"Data exported to {file_path} successfully.")
    
    def create_decomposition(self, model_details_input, xs_details_input, variable_details_input_df, transformed_dict, model_results, model_predicted_values):
        """Perform all the decomposition creation steps"""

        # Transform certain columns to float in variable details
        variable_details_input_df.columns = variable_details_input_df.columns.str.lower()
        variable_details_input_df[['interval','coeff min','coeff max','importance']] = variable_details_input_df[['interval','coeff min','coeff max','importance']].astype(float)
        
        # Reverse the application of xs weightings if needed
        _,_,_,xs_weights,_,_ = model_details_input
        if xs_weights is not None:
            transformed_dict = self.reverse_xs_weights(transformed_dict, xs_weights, xs_details_input)
        
        # Create interval map if there panel variables with mulitple cofficients
        interval_map = self.create_interval_map(variable_details_input_df, transformed_dict)
        
        # Check if there are panel variables constants (fixed effects)
        parameters, transformed_dict = self.create_params(transformed_dict, model_results)

        # Create model prediced values by panel dict and if there are weights change the predictions
        panel_pred_vals_dict = self.create_predicted_values_by_panel_dict(model_details_input, transformed_dict, model_predicted_values)
        
        # Perform the decomp steps
        multiplied_dict = self.multiply_transformed_data_by_coefficients(transformed_dict, parameters)
        log_adjusted_multiplied_dict = self.log_transformation_bias(model_details_input, multiplied_dict, interval_map, panel_pred_vals_dict)
        interval_map = self.within_interval_checks(log_adjusted_multiplied_dict, interval_map)
        below_interval_cumsum_dict,below_and_including_interval_cumsum_dict = self.create_cumulative_intervals(log_adjusted_multiplied_dict,interval_map)
        post_exp_dict = self.post_exponential_transformation(model_details_input,below_interval_cumsum_dict,log_adjusted_multiplied_dict,interval_map)
        within_int_synergy_df = self.within_interval_synergy(interval_map,below_interval_cumsum_dict,below_and_including_interval_cumsum_dict,post_exp_dict)
        final_decomp_df = self.create_final_decomp(post_exp_dict,within_int_synergy_df,interval_map)

        # Change the var names to short var names
        final_decomp_df = map_short_var_names(final_decomp_df,variable_details_input_df)
        final_decomp_df.columns = final_decomp_df.columns.str.lower()
        
        return final_decomp_df
    
    def reverse_xs_weights(self, trans_dict, xs_w_col, xs_df):
        """Apply the selected xs weights to the dataset."""
        
        # Select first perm of transformed dict
        df = trans_dict[1]
        
        # Convert xs_df to a dictionary mapping crosssection to its weight
        xs_weight_dict = ims.convert_2_df_cols_to_dict(xs_df, key_col='crosssection', value_col=xs_w_col)

        # Convert dictionary values to float (if they are strings)
        xs_weight_dict = {k: float(v) for k, v in xs_weight_dict.items()}

        # Identify numeric columns to be scaled (exclude 'obs' and 'xslist')
        num_cols = df.select_dtypes(include=['number']).columns.difference(['obs', 'xslist'])

        # Apply weights row-wise
        # df[num_cols] = df.apply(lambda row: row[num_cols] / xs_weight_dict.get(row['xslist'], 1), axis=1)
        df[num_cols] = df[num_cols].div(df['xslist'].map(xs_weight_dict).fillna(1), axis=0)

        # Apply this trans dict
        trans_dict[1] = df
        
        return trans_dict
    
    def create_interval_map(self, variable_df, trans_dict):
        """ Create interval map"""

        columns_with_mu = [key for key in trans_dict[1].keys() if "μ" in key]
        interval_map = variable_df.set_index("variable")["interval"].to_dict()

        # Create interval map if there are panel variables with μ
        grouped_by_prefix = {}
        if len(columns_with_mu) != 0:

            # Group the `μ` columns by the substring before "μ"
            for col in columns_with_mu:
                prefix = col.split("μ")[0].strip("_")
                grouped_by_prefix.setdefault(prefix, []).append(col)
        
            # Replace keys in interval_map with grouped columns
            updated_interval_map = {}
            for key, value in interval_map.items():
                if key in grouped_by_prefix:
                    # Expand grouped columns and assign the same value
                    for expanded_col in grouped_by_prefix[key]:
                        updated_interval_map[expanded_col] = value
                else:
                    # Retain non-μ columns as is
                    updated_interval_map[key] = value
        else:
            # No μ columns, retain the original interval_map
            updated_interval_map = interval_map
        
        return updated_interval_map
    
    def create_params(self, trans_dict, results):
        """ Check if the panel constants need to be adjusted for"""
        constant_panel_cols = [col for col in trans_dict[1].keys() if "constant_μ" in col]
        # Extract regression coefficients checking if the panel constants need to be adjusted
        if len(constant_panel_cols) != 0:
            first_coefficient = None
            for key, value in results.items():
                if "constant_μ" in key:
                    # Check if this is the first occurrence
                    if first_coefficient is None:
                        first_key = key
                        first_coefficient = value['coefficient']  # Save the first coefficient
                    else:
                        # Adjust the coefficient for subsequent occurrences
                        results[key]['coefficient'] += first_coefficient

            # Adjust the first coefficient
            xs = first_key.split("constant_μ")[1].replace("_", "")
            unique_values, counts = np.unique(trans_dict[1]['xslist'], return_counts=True)
            xs_counts = dict(zip(unique_values, counts))
            trans_dict[1] = trans_dict[1].reset_index(drop=True)
            trans_dict[1].loc[xs_counts[xs]:,first_key] = 0
        
        # Extract params
        params = np.array([value['coefficient'] for key, value in results.items()]).astype(float)
        params = params.reshape(-1, 1)
        
        return params, trans_dict
    
    def create_category_decomposition(self, variable_details_input_df, final_decomp_df):
        """Create the category decomposition"""
        cols = final_decomp_df.columns.tolist()
        cols = [col for col in cols if col not in ['obs', 'xslist']]
        final_decomp_long_df = ims.convert_df_wide_2_long(final_decomp_df,cols,variable_col_name="variable",value_col_name='value')
        var_to_cat_dict = ims.convert_2_df_cols_to_dict(variable_details_input_df,'short variable name','category')
        var_to_cat_dict = {key.lower(): value.lower() if isinstance(value, str) else value for key, value in var_to_cat_dict.items()}
        final_decomp_long_df['category'] = final_decomp_long_df['variable'].map(var_to_cat_dict).fillna('obs')
        final_cat_decomp_df = final_decomp_long_df.pivot_table(
            index=["xslist","obs"],  # Use 'obs' and 'xslist' as indices
            columns="category",       # Categories become columns
            values="value",           # Values to aggregate
            aggfunc="sum",            # Aggregation function
        )
        
        # Reset the index to flatten the DataFrame
        final_cat_decomp_df = final_cat_decomp_df.reset_index()
        
        return final_cat_decomp_df
    
    def create_predicted_values_by_panel_dict(self, model_details, trans_dict, predicted_vals):
        """Create a nested dictionary of predicted and actual KPI values by panel."""
        
        # Extract actual KPI and panels
        actual_kpi = np.array(trans_dict[1][model_details[0]])  # Actual KPI values
        panels = trans_dict[1]['xslist']  # Panels
        
        # # Unpack model details and if there is weightings 
        # _, _, _, xs_weightings, _, _  = model_details
        
        # Initialize an empty dictionary
        panel_dict = {}

        # Populate the dictionary
        for panel, predicted, actual in zip(panels, predicted_vals, actual_kpi):
            if panel not in panel_dict:
                panel_dict[panel] = {'actual_kpi': [], 'predicted_kpi': []}
            
            # Append values to the corresponding keys in the nested dict
            panel_dict[panel]['actual_kpi'].append(actual)
            panel_dict[panel]['predicted_kpi'].append(predicted)
        
        # if xs_weightings is not None:
        #     xs_weightings_dict = ims.convert_2_df_cols_to_dict(xs_dets,key_col='crosssection',value_col=xs_weightings)
        #     # Apply weightings
        #     # Create dict
        #     panel_dict_new = {}
        #     for panel, nesteddict in panel_dict.items():
        #         for kpi_type in nesteddict.keys():
        #             if panel not in panel_dict_new:
        #                 panel_dict_new[panel] = {}  # <-- Ensure a dictionary exists for the panel
            
        #     # Fill dict
        #     for panel, nesteddict in panel_dict.items():
        #         for kpi_type in nesteddict.keys():
        #             if kpi_type == 'predicted_kpi':
        #                 panel_dict_new[panel][kpi_type] = np.array(panel_dict[panel][kpi_type], dtype=float)/float(xs_weightings_dict[panel])
        #             else:
        #                 panel_dict_new[panel][kpi_type] = np.array(panel_dict[panel][kpi_type], dtype=float)
        # else:
        #     panel_dict_new = panel_dict
        
        return panel_dict
    
    def multiply_transformed_data_by_coefficients(self, transformed_dict, params):
        """Multiplies the transformed dataframe by the coefficients of the regression."""
    
        # Convert the dictionary values (starting from the second key) to a NumPy array
        transformed_df = transformed_dict[1]
        transformed_dict = transformed_df.to_dict(orient="list")

        transformed_array = np.array(list(transformed_dict.values())[3:])
        
        # Perform element-wise multiplication
        result_values = transformed_array * params[:len(transformed_array)]

        # Update the dictionary starting from the second key
        multiplied_dict = dict(list(transformed_dict.items())[:3] + list(zip(list(transformed_dict.keys())[3:], result_values)))

        return multiplied_dict
    
    def log_transformation_bias(self, model_details_input, multiplied_dict, int_map, pred_vals_dict):
        """Adjust for log trans bias"""

        # # Unpack model details and find variables in interval 1
        _, _, _, _, log_trans_bias_adjustment, _ = model_details_input
        int_1_variables = [k for k, v in int_map.items() if v == 1.0]
        
        # Adjust for log transformation bias if applicable
        if log_trans_bias_adjustment.lower() == "yes":
            # Loop through the predictions by panel
            for key in pred_vals_dict.keys():
                modelled_kpi = np.array(pred_vals_dict[key]['predicted_kpi'], dtype=float)
                actual_kpi = np.array(pred_vals_dict[key]['actual_kpi'], dtype=float)
                # modelled_kpi = modelled_kpi.astype(float)
                # actual_kpi = actual_kpi.astype(float)

                # Ensure valid data (no NaN values)
                valid_indices = ~np.isnan(modelled_kpi) & ~np.isnan(actual_kpi)
                modelled_kpi = modelled_kpi[valid_indices]
                actual_kpi = actual_kpi[valid_indices]
                
                # Calculate adjustment value
                def objective_function(x):
                    return np.sum((np.exp(modelled_kpi + x) - np.exp(actual_kpi))**2)
                
                # # Initialize x as zero
                initial_guess = 0
                result = minimize(objective_function, initial_guess, method="L-BFGS-B", bounds=[(-1, 1)])
                adjustment_value = result.x[0]
                
                # Initialize x as zero
                # result = minimize_scalar(objective_function, method="Bounded", bounds=(-1, 1))
                # # result = minimize_scalar(objective_function)
                # adjustment_value = result.x

            
                # Check adjustment effectiveness
                difference = sum(modelled_kpi + np.repeat(adjustment_value, len(modelled_kpi))) - sum(actual_kpi)
                print(adjustment_value)
                print(f"Difference between adjusted modelled KPI and actual KPI for {key}: {difference}")
                # Find variables in interval 1 to adjust, and proporition out adjustment
                # adjustment_value = optimal_x/len(int_1_variables)
                # print(adjustment_value)
                # Only adjust values where xs_list matches the key
                xs_list = multiplied_dict['xslist']
                
                # Get the indices where xs_list == key
                matching_indices = [index for index, value in enumerate(xs_list) if value == key]

                # Loop through the matching indices and apply adjustment to the corresponding values
                for i in int_1_variables:
                    # Only adjust if the current variable exists in multiplied_dict
                    if f"constant_μ_{key}" == i:
                        if i in multiplied_dict:  # Ensure the key exists in multiplied_dict
                            # Apply adjustment to the values at the matching indices
                            for idx in matching_indices:
                                multiplied_dict[i][idx] += adjustment_value  # Adjust the value at the index
                                
        return multiplied_dict

    def within_interval_checks(self,multiplied_dict,int_map):
        """Split negatives and positives into their own intervals within intervals"""
        
        for key in list(multiplied_dict.keys())[3:]:
            if int_map[key] == 1:
                pass
            elif (multiplied_dict[key] <= 0).all():
                int_map[key] = int_map[key] + 0.1
            elif (multiplied_dict[key] >= 0).all():
                int_map[key] = int_map[key] + 0.2
            # else:
            #     interval_map[key] = interval_map[key] + 0.3
        
        def adjust_intervals(i_map):
            """Adsjust intervals to be integers"""
            # Sort the dictionary by intervals
            sorted_list = sorted(i_map.items(), key=lambda x: x[1])
            new_interval_map = {}

            for idx, (key, interval) in enumerate(sorted_list):
                if idx == 0:
                    # First element, no previous element to compare with
                    new_interval_map[key] = 1.0
                else:
                    # Compare with previous element
                    prev_key, prev_interval = sorted_list[idx - 1]
                    
                    if interval == prev_interval:
                        # If the interval is the same as the previous one, keep the same number
                        new_interval_map[key] = new_interval_map[prev_key]
                    else:
                        # Otherwise, increment the interval number
                        new_interval_map[key] = new_interval_map[prev_key] + 1

            return new_interval_map
            
        # Adjust the intervals
        int_map = adjust_intervals(int_map)
            
        return int_map

    def create_cumulative_intervals(self, multiplied_dict, interval_map):
        """Create cumulative sums of variables grouped by intervals."""

        # Count occurance of interval one assuming constant is in it's own interval
        interval_1_count = sum(1 for v in interval_map.values() if v == 1.0)
        unique_values = set(interval_map.values())
        unique_count = len(unique_values)
        
        # Count number of panels
        panel_count = len(set(multiplied_dict["xslist"]))
        
        if interval_1_count != 1.0 and panel_count == 1:
            QtWidgets.QMessageBox.warning(self, "Constant Interval Issues", "The constant must be on its own in interval 1 with time series data.")
            return
        elif unique_count < 2.0:
            QtWidgets.QMessageBox.warning(self, "Interval Issues", "There needs to be at least 2 intervals.")
            return
        else:
            # Filter for variables that exist in the DataFrame
            valid_variables = [var for var in interval_map.keys() if var in multiplied_dict.keys()]
            multiplied_dict_filtered = {key: multiplied_dict[key] for key in valid_variables if key in multiplied_dict}

        # Function to cumsum multiplied data by interval by combining the interval and multiplied dict dictionaries
        def combine_to_nested_dict(multiplied_dict, interval_map):
            """Function to Combine the interval and multiplied data dictionaries and then cumulatively sum the intervals"""
            # Initialize the nested dictionary
            interval_sums_dict = {}

            # Iterate through the variables dictionary
            for variable, values in multiplied_dict.items():
                # Use the variable to look up the interval
                interval = interval_map.get(variable)

                # Sum the values by interval
                if interval not in interval_sums_dict:
                    interval_sums_dict[interval] = np.array(values)  # Initialize with the current array
                else:
                    interval_sums_dict[interval] += np.array(values)  # Add the current array

            # Convert sums to lists for consistency and calculate cumulative sums
            interval_cumsum_dict = {}
            cumulative_sum = np.zeros_like(list(interval_sums_dict.values())[0])

            for interval, summed_values in interval_sums_dict.items():
                # Add the interval's summed values to the cumulative sum
                cumulative_sum += summed_values
                interval_cumsum_dict[interval] = cumulative_sum.tolist()

            return interval_cumsum_dict

        # Combine dictionaries with necessary variables
        interval_cumsum_dict = combine_to_nested_dict(multiplied_dict_filtered, interval_map)

        # Create the new dictionary which removes the interval value from the first interval
        new_interval_cumsum_dict = {}

        # Get the keys of the dictionary sorted
        sorted_keys = sorted(interval_cumsum_dict.keys())

        # Move values to the next key
        for i, key in enumerate(sorted_keys):
            if i == len(sorted_keys) - 1:
                # Last key is removed, no value assigned to it
                continue
            else:
                # Move the current key's value to the next key
                new_interval_cumsum_dict[sorted_keys[i + 1]] = interval_cumsum_dict[key]
        
        # Add back in interval 1 as 0s
        new_interval_cumsum_dict[1.0] = np.zeros_like(interval_cumsum_dict[1.0])
        new_interval_cumsum_dict = {key: new_interval_cumsum_dict[key] for key in sorted(new_interval_cumsum_dict.keys())}
        
        # Add back in the obs column
        below_interval_cumsum_dict = {list(multiplied_dict.items())[0][0]:list(multiplied_dict.items())[0][1]}
        below_interval_cumsum_dict.update(new_interval_cumsum_dict)
        below_and_including_interval_cumsum_dict = {list(interval_cumsum_dict.items())[0][0]:list(interval_cumsum_dict.items())[0][1]}
        below_and_including_interval_cumsum_dict.update(interval_cumsum_dict)
    
        return below_interval_cumsum_dict,below_and_including_interval_cumsum_dict
    
    def post_exponential_transformation(self, model_details_input, cumulative_intervals_dict, multiplied_dict, interval_map):
        """Apply the exponential transformation to the data, factoring in reference points and synergies."""

        # Check the take anti-logs at midpoints setting
        _, _, _, _, _, take_anti_logs_at_midpoints = model_details_input
        if take_anti_logs_at_midpoints == "Yes":
            param_1 = 0.5
            param_2 = -0.5
        else:
            param_1 = 1
            param_2 = 0
        
        # Find common keys
        common_keys = multiplied_dict.keys() & interval_map.keys()
        
        # Initialize the dictionary for the transformed values filtering out obs and kpi col
        post_exp_dict = {key: [] for key in multiplied_dict.keys() if key in common_keys}

        # Process the transformation for each key in multiplied_dict
        for key, value in multiplied_dict.items():
            # # Check if the key exists in interval_map
            if key in interval_map:
                interval = interval_map[key]
                
                # Ensure `value` is an array for consistent processing
                value = np.array(value, dtype=float) if not isinstance(value, np.ndarray) else np.array(value, dtype=float)

                if interval == 1.0:
                    # post_exp_dict[key] = np.exp(param_1 * value) - np.exp(param_2 * value)
                    transformed_value = np.exp(param_1 * value) - np.exp(param_2 * value)
                    # Add 1 only to non-zero elements
                    post_exp_dict[key] = transformed_value + np.where(value != 0, 1, 0)
                else:
                    # Assuming interval_below_cumulative is a reference from the original dataframe
                    interval_below_cumulative = cumulative_intervals_dict[interval]
                    post_exp_dict[key] = np.exp(interval_below_cumulative + (param_1 * value)) - np.exp(interval_below_cumulative + (param_2 * value))
        
        # Add back in the obs column and xslist column
        final_post_exp_dict = {}
        final_post_exp_dict['obs'] = multiplied_dict['obs']  # Add the 'obs' column
        final_post_exp_dict['xslist'] = multiplied_dict['xslist']  # Add the 'xslist' column
        final_post_exp_dict.update(post_exp_dict)  # Add transformed values
        
        return final_post_exp_dict

    def within_interval_synergy(self,interval_map,below_interval_cumsum_dict,below_and_including_interval_cumsum_dict,post_exp_dict):  
        """Find the within interval synergy accounting for the post exponential"""
        
        # Create and obs and xlslist dictionary and exclude them
        post_exp_dict = post_exp_dict.copy()
        below_interval_cumsum_dict = below_interval_cumsum_dict.copy()
        below_and_including_interval_cumsum_dict = below_and_including_interval_cumsum_dict.copy()
        obs_dict = {"obs": post_exp_dict["obs"]}
        xs_dict = {"xslist": post_exp_dict["xslist"]}
        for keys in (below_interval_cumsum_dict,below_and_including_interval_cumsum_dict,post_exp_dict):
            if "obs" in keys:
                del keys["obs"]
            if "xslist" in keys:
                del keys["xslist"]

        # Initialize the nested dictionary
        post_exp_interval_sums_dict = {}

        # Iterate through the variables dictionary
        for variable, values in post_exp_dict.items():
            # Use the variable to look up the interval
            interval = interval_map.get(variable)

            # Sum the values by interval
            if interval not in post_exp_interval_sums_dict:
                post_exp_interval_sums_dict[interval] = np.array(values)  # Initialize with the current array
            else:
                post_exp_interval_sums_dict[interval] += np.array(values)  # Add the current array

        # Sort the dictionary by interval
        post_exp_interval_sums_dict = dict(sorted(post_exp_interval_sums_dict.items()))

        # Calculate within interval synergy
        within_interval_synergy_dict = {key: np.exp(below_and_including_interval_cumsum_dict[key])
                                        -np.exp(below_interval_cumsum_dict[key])
                                        - post_exp_interval_sums_dict[key]
                                        for key in below_interval_cumsum_dict.keys()}
        
        # Add back in 'obs' and 'xslist' columns
        final_within_interval_synergy_dict = {}
        final_within_interval_synergy_dict["obs"] = obs_dict["obs"]
        final_within_interval_synergy_dict["xslist"] = xs_dict["xslist"]
        final_within_interval_synergy_dict.update(within_interval_synergy_dict)

        return final_within_interval_synergy_dict

    def create_final_decomp(self,post_exp_dict,within_interval_synergy_dict,interval_map):
        """Bring all the steps together"""
            
        # Initialize the nested dictionary
        decomp_dict = {}
        
        # Create and obs dictionary and exclude the obs column
        obs_dict = {"obs": post_exp_dict["obs"]}
        xs_dict = {"xslist": post_exp_dict["xslist"]}
        for keys in (post_exp_dict,within_interval_synergy_dict):
            if "obs" in keys:
                del keys["obs"]
            if "xslist" in keys:
                del keys["xslist"]
        
        # Combine the interval map and the post_exp_dict for the sumproduct
        sumproduct_dict = {interval: {variable: value for variable, 
                                        value in post_exp_dict.items() 
                                        if interval_map[variable] == interval} for interval in set(interval_map.values())}

        # Iterate through the variables dictionary
        for variable, values in post_exp_dict.items():
            # Use the variable to look up the interval
            interval = interval_map.get(variable)

            # Calculate the sumproduct of the interval
            arrays_for_sumproduct = [value for value in sumproduct_dict[interval].values()]
            interval_sumproduct_arrays = np.stack(arrays_for_sumproduct,axis=1)
            interval_sumproduct = np.sum(np.abs(interval_sumproduct_arrays),axis=1)

            # TO FIX IN FUTURE
            # Calculate the synergy ratio to be used in the final calculation
            synergy_ratio = np.where(
                (interval_sumproduct != 0) & (values != 0),
                np.abs(values) / interval_sumproduct,
                0.0
            )
            # synergy_ratio = np.abs(values) / interval_sumproduct  # Perform the division
            # synergy_ratio = np.nan_to_num(synergy_ratio, nan=0.0, posinf=0.0, neginf=0.0)  # Replace NaN and infinities with 0

            # Calculate the final values    
            final_values = []  # List to store the updated values
            for i in range(len(synergy_ratio)):
                # Check the condition for each value
                if synergy_ratio[i] == 0 or np.isnan(synergy_ratio[i]) or np.isinf(synergy_ratio[i]):
                    final_values.append(values[i] + within_interval_synergy_dict[interval][i] * 0)  # Set to zero if invalid
                else:
                    final_values.append(values[i] + within_interval_synergy_dict[interval][i] * synergy_ratio[i])

            # Update final_decomp_dict for the variable
            decomp_dict[variable] = final_values

        # Add back 'obs' and 'xslist' columns to the final dictionary
        final_decomp_dict = {
            "obs": obs_dict["obs"],
            "xslist": xs_dict["xslist"],
            **decomp_dict
        }

        # Output as dataframe
        final_decomp_df = pd.DataFrame(final_decomp_dict)
        final_decomp_df.columns = final_decomp_df.columns.str.lower()
        final_decomp_df['obs'] = pd.to_datetime(final_decomp_df['obs'])
            
        # Count number of panels
        panel_count = len(set(final_decomp_df["xslist"]))

        # If the dataset is panel
        if panel_count > 1:
            
            # Initialize a new DataFrame to store the aggregated results
            aggregated_df = pd.DataFrame()

            # Iterate over the unique prefixes of the columns which have been split out
            prefixes = set(col.split('_μ_')[0] for col in final_decomp_df.columns if '_μ_' in col)
            cols_without_mu = [col for col in final_decomp_df.columns if '_μ_' not in col]
            
            # Aggregate columns
            for prefix in prefixes:
                # Filter columns with the same prefix
                matching_columns = [col for col in final_decomp_df.columns if col.startswith(prefix)]
                # Multiply the appropriate columns by 1 or 0 based on xslist
                aggregated_values = sum(
                    final_decomp_df[col] * (final_decomp_df['xslist'] == col.split('_μ_')[-1]).astype(int)
                    for col in matching_columns
                )
                
                # Add the aggregated column to the new DataFrame
                aggregated_df[prefix] = aggregated_values
                
            # Reorder columns to place 'obs' and 'xslist' at the front
            aggregated_df[cols_without_mu] = final_decomp_df[cols_without_mu]
            column_order = ['xslist','obs'] + [col for col in aggregated_df.columns if col not in ['obs', 'xslist']]
            final_decomp_df = aggregated_df[column_order]
        
            # FOR NOW
            final_decomp_df['constant'] = final_decomp_df['constant']+1
        
        return final_decomp_df

    def update_variable_details_input_df(self,variable_details_input_df):
        """Updated the class with the variable_details_input_df"""
        if variable_details_input_df is not None and not variable_details_input_df.empty:
            self.variable_details_input_df = variable_details_input_df
            
    def update_transformed_df(self,transformed_df):
        """Updates the class with the transformed df."""
        if transformed_df is not None and not transformed_df.empty:
            self.transformed_df = transformed_df
            
    def update_model_results(self, model_results):
        """Updates the class with new model results."""
        if model_results:
            self.model_results = model_results
            
            # Recreate the decomposition with the updated model results
            decomp = self.create_decomposition(
                self.model_details_input, 
                self.variable_details_input_df, 
                self.transformed_df, 
                self.model_results, 
                self.model_predictions
            )
        
        # Update the chart
        # self.plot_stacked_column(decomp)
    
    def update_model_stats(self, model_stats):
        """Updates the class with new model results."""
        if model_stats:
            self.model_stats = model_stats

    def update_model_predictions(self, model_predictions):
        """Updates the class with new model predicted values."""
        if model_predictions:
            self.model_predictions = model_predictions

class AvM(QtWidgets.QWidget):
    def __init__(self, avm_df):
        super().__init__()

        self.avm_df = avm_df
        self.avm_df= self.avm_df.rename(columns={'acc_vals': 'Actual Logged','pred_vals': 'Model Logged',"residuals": "Residuals"})
        self.current_avm_df = self.avm_df
        
        # Create a list of unique xslist values
        self.xslist_values = sorted(self.avm_df['xslist'].unique())
        
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Create a QTabWidget to hold the graphs and tables
        self.tabs = QtWidgets.QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Create the tab widgets
        self.log_avm_graph_tab = QtWidgets.QTabWidget()
        self.avm_table_tab = QtWidgets.QTabWidget()

        # Set up the layout for each tab
        self.log_avm_graph_layout = QtWidgets.QVBoxLayout(self.log_avm_graph_tab)
        self.avm_table_layout = QtWidgets.QVBoxLayout(self.avm_table_tab)
        
        # Add dropdown to logged AvM tab
        self.dropdown_log_avm = QtWidgets.QComboBox()
        self.dropdown_log_avm.addItems(self.xslist_values)
        self.log_avm_graph_layout.addWidget(self.dropdown_log_avm)
        
        # Create QWebEngineViews for each graph tab
        self.web_view_log_avm = QWebEngineView()
        
        # Add QWebEngineView to each graph tab's layout
        self.log_avm_graph_layout.addWidget(self.web_view_log_avm)
        
        # Add the tabs for the graphs
        self.tabs.addTab(self.log_avm_graph_tab, "Logged AvM Graph")
        
        # Add the tabs for the table
        self.tabs.addTab(self.avm_table_tab, "AvM Table")
        
        # Set table with corresponding data
        self.populate_table()
        
        # Add Export Buttons
        self.export_avm_button = QtWidgets.QPushButton("Export Decomposition to Excel")
        self.avm_table_layout.addWidget(self.export_avm_button)

        # Connect export buttons to methods
        self.export_avm_button.clicked.connect(lambda: self.export_to_excel(self.avm_df))
        
        # Initial chart rendering
        self.plot_avm_graph(self.avm_df.loc[self.avm_df['xslist'] == self.xslist_values[0]], self.web_view_log_avm)
        
        # Connect dropdowns to chart updates
        self.dropdown_log_avm.currentTextChanged.connect(self.update_logged_avm_chart)

    def plot_avm_graph(self, final_avm_df, web_view):
        """Generates the Plotly graph and displays it in QWebEngineView."""
        fig = go.Figure()

        # Line plots for acc_vals and pred_vals
        fig.add_trace(go.Scatter(x=final_avm_df["obs"], y=final_avm_df["Actual Logged"], 
                                mode="lines",name="Actual Logged"))
        fig.add_trace(go.Scatter(x=final_avm_df["obs"], y=final_avm_df["Model Logged"],
                                mode="lines",name="Model Logged"))

        # Bar plot for residuals
        fig.add_trace(go.Bar(x=final_avm_df["obs"], y=final_avm_df["Residuals"],
                            opacity=0.5,name="Residuals"))
        
        # Update layout for visual enhancements
        fig.update_layout(
            barmode='relative',  # Enable stacking
            title=dict(
                text="Actual vs Model",
                font=dict(size=24, color="#FFFFFF"),
                x=0.5  # Center the title
            ),
            xaxis=dict(
                title="Observation",
                tickangle=-45,  # Rotate labels for readability
                gridcolor="rgba(255,255,255,0.2)"  # Light gridlines
            ),
            yaxis=dict(
                title="Value",
                gridcolor="rgba(255,255,255,0.2)"  # Light gridlines
            ),
            legend=dict(
                title="Variables",
                orientation="v",  # Vertical legend
                x=1,              # Positioned to the right
                y=1,              # Start from the top
                xanchor="left",
                yanchor="top",
                bgcolor="#1E1E1E",  # Match the chart background
                bordercolor="#FFFFFF",
                borderwidth=1,
                font=dict(size=10),
                itemsizing="constant",  # Maintain consistent sizing
                traceorder="normal",    # Maintain the order of traces
                valign="top",           # Align the legend items to the top
            ),
            plot_bgcolor="#1E1E1E",  # Dark background for contrast
            paper_bgcolor="#121212",  # Match the outer paper with dark theme
            font=dict(color="#FFFFFF"),  # White text for readability
            template='plotly_dark',
        )

        fig.update_layout(transition_duration=500)  # Smooth transitions

        # Convert to HTML and load into QWebEngineView
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        web_view.setHtml(plot_html)

    def populate_table(self):
        """Creates a QTableView displaying avm_df."""
        self.table_view = QtWidgets.QTableView()
        model = self.PandasTableModel(self.avm_df)
        self.table_view.setModel(model)
        self.avm_table_layout.addWidget(self.table_view)

    class PandasTableModel(QtCore.QAbstractTableModel):
        """Custom Table Model to load pandas DataFrame into QTableView."""
        def __init__(self, df=pd.DataFrame(), parent=None):
            super().__init__(parent)
            self.df = df

        def rowCount(self, parent=QtCore.QModelIndex()):
            return self.df.shape[0]

        def columnCount(self, parent=QtCore.QModelIndex()):
            return self.df.shape[1]

        def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
            if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
                return None
            return str(self.df.iloc[index.row(), index.column()])

        def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
            if role != QtCore.Qt.ItemDataRole.DisplayRole:
                return None
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self.df.columns[section]
            else:
                return str(section)
    
    def export_to_excel(self, data):
        """Export DataFrame to Excel with a file dialog."""
        # Show a file dialog to choose where to save the file
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setDefaultSuffix(".xlsx")
        file_path, _ = file_dialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx)")

        if file_path:
            data.to_excel(file_path, index=False)
            QtWidgets.QMessageBox.information(self, "Export Successful", f"Data exported to {file_path} successfully.")
            
    def update_logged_avm_chart(self, selected_xslist):
        """Update the logged avm chart based on dropdown selection."""
        filtered_decomp = self.current_avm_df[self.current_avm_df['xslist'] == selected_xslist]
        self.plot_avm_graph(filtered_decomp, self.web_view_log_avm)

# class ResidualCorrelation(QtWidgets.QWidget):
#     def __init__(self, raw_df, avm_df):
#         super().__init__()
#         self.raw_df = raw_df
#         self.avm_df = avm_df
#         self.create_resid_correlations()

#     def create_resid_correlations(self):
#         """Create residual correlation table with Total correlation column."""
        
#         self.raw_df = column_to_datetime(self.raw_df, 'obs')
#         self.avm_df = column_to_datetime(self.avm_df, 'obs')

#         # Merge avm_df (residuals) with raw_df on 'obs'
#         new_avm_df = self.avm_df[['obs', 'xslist', 'residuals']]
#         merged_df = new_avm_df.merge(self.raw_df, how='left', on='obs')

#         # Get unique xslist values
#         xslist_values = merged_df['xslist'].unique()

#         # Step 1: Calculate "Total" correlation
#         stacked_data = []
#         stacked_residuals = []

#         for xs in xslist_values:
#             filtered_df = merged_df[merged_df['xslist'] == xs]
#             stacked_data.append(filtered_df.drop(columns=['obs', 'xslist', 'residuals']))
#             stacked_residuals.append(filtered_df['residuals'])

#         # Stack the raw data & residuals as in R
#         total_stacked_df = pd.concat(stacked_data, ignore_index=True)
#         total_stacked_residuals = pd.concat(stacked_residuals, ignore_index=True)

#         # Compute total correlation
#         total_correlation = total_stacked_df.corrwith(total_stacked_residuals, axis=0)
#         total_correlation = total_correlation.dropna().drop(['obs', 'xslist', 'residuals'], errors='ignore')

#         # Step 2: Calculate correlation for each `xslist`
#         correlation_dict = {'Total': total_correlation}  # Store total correlation first

#         for xs in xslist_values:
#             filtered_df = merged_df[merged_df['xslist'] == xs]

#             # Drop non-numeric and unnecessary columns
#             correlation_matrix = filtered_df.drop(columns=['obs', 'xslist']).corr()

#             # Extract correlation of residuals with other variables
#             correlation_dict[xs] = correlation_matrix['residuals'].drop('residuals', errors='ignore')

#         # Convert dictionary to DataFrame
#         correlation_df = pd.DataFrame(correlation_dict)

#         # Sort by total correlation
#         correlation_df = correlation_df.sort_values(by="Total", ascending=False)

#         print("\nUpdated Correlation Table:\n", correlation_df)  # Debugging

#         # Display in PySide6 Table
#         self.display_table(correlation_df)

#     def display_table(self, correlation_df):
#         """Displays the correlation DataFrame in a QTableView."""
#         self.table_view = QtWidgets.QTableView()
#         self.table_view.setItemDelegate(self.CorrelationColorDelegate(self.table_view))
#         model = self.PandasTableModel(correlation_df)
#         self.table_view.setModel(model)

#         # Layout
#         layout = QtWidgets.QVBoxLayout(self)
#         layout.addWidget(self.table_view)
#         self.setLayout(layout)

#     class PandasTableModel(QtCore.QAbstractTableModel):
#         """Custom model to display DataFrame in QTableView."""
#         def __init__(self, df=pd.DataFrame(), parent=None):
#             super().__init__(parent)
#             self.df = df

#         def rowCount(self, parent=QtCore.QModelIndex()):
#             return self.df.shape[0]

#         def columnCount(self, parent=QtCore.QModelIndex()):
#             return self.df.shape[1]

#         def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
#             if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
#                 return None
#             return str(round(self.df.iloc[index.row(), index.column()], 3))

#         def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
#             if role != QtCore.Qt.ItemDataRole.DisplayRole:
#                 return None
#             if orientation == QtCore.Qt.Orientation.Horizontal:
#                 return str(self.df.columns[section])  # Column headers are xslist values
#             else:
#                 return self.df.index[section]  # Row headers are variable names
    
#     class CorrelationColorDelegate(QtWidgets.QStyledItemDelegate):
#         """Custom delegate to color code correlation values."""
        
#         def paint(self, painter, option, index):
#             if not index.isValid():
#                 return

#             value = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
#             try:
#                 value = float(value)
#             except ValueError:
#                 QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
#                 return

#             # Define color gradients based on value
#             if value >= 0:
#                 # Green shades for positive correlation
#                 r = int(255 * (1 - value))  # More positive → less red
#                 g = 255                      # Always full green
#                 b = int(255 * (1 - value))  # More positive → less blue
#             else:
#                 # Red shades for negative correlation
#                 r = 255                      # Always full red
#                 g = int(255 * (1 + value))  # More negative → less green
#                 b = int(255 * (1 + value))  # More negative → less blue

#             painter.fillRect(option.rect, QtGui.QColor(r, g, b))

#             # Draw text
#             painter.setPen(QtGui.QColor(0, 0, 0))  # Black text
#             painter.drawText(option.rect, QtCore.Qt.AlignmentFlag.AlignCenter, index.data())

#         def displayText(self, value, locale):
#             return f"{float(value):.2f}" if isinstance(value, (float, int)) else value

class ResidualCorrelation(QtWidgets.QWidget):
    def __init__(self, raw_df, avm_df):
        super().__init__()
        self.raw_df = raw_df
        self.avm_df = avm_df
        self.create_resid_correlations()

    def create_resid_correlations(self):
        """Create residual correlation table with Total correlation column."""
        self.raw_df = column_to_datetime(self.raw_df, 'obs')
        self.avm_df = column_to_datetime(self.avm_df, 'obs')

        # Merge avm_df (residuals) with raw_df on 'obs'
        new_avm_df = self.avm_df[['obs', 'xslist', 'residuals']]
        merged_df = new_avm_df.merge(self.raw_df, how='left', on='obs')

        # Get unique xslist values
        xslist_values = merged_df['xslist'].unique()

        # Calculate "Total" correlation
        stacked_data = []
        stacked_residuals = []

        for xs in xslist_values:
            filtered_df = merged_df[merged_df['xslist'] == xs]
            stacked_data.append(filtered_df.drop(columns=['obs', 'xslist', 'residuals']))
            stacked_residuals.append(filtered_df['residuals'])

        total_stacked_df = pd.concat(stacked_data, ignore_index=True)
        total_stacked_residuals = pd.concat(stacked_residuals, ignore_index=True)

        total_correlation = total_stacked_df.corrwith(total_stacked_residuals, axis=0)
        total_correlation = total_correlation.dropna().drop(['obs', 'xslist', 'residuals'], errors='ignore')

        # Calculate correlation for each xslist
        correlation_dict = {'Total': total_correlation}
        for xs in xslist_values:
            filtered_df = merged_df[merged_df['xslist'] == xs]
            correlation_matrix = filtered_df.drop(columns=['obs', 'xslist']).corr()
            correlation_dict[xs] = correlation_matrix['residuals'].drop('residuals', errors='ignore')

        correlation_df = pd.DataFrame(correlation_dict)
        correlation_df = correlation_df.sort_values(by="Total", ascending=False)

        # Display in PySide6 Table with row label filter
        self.display_table(correlation_df)

    def display_table(self, correlation_df):
        """Displays the correlation DataFrame in a QTableView with both row label and column filtering."""
        self.table_view = QtWidgets.QTableView()
        self.table_view.setItemDelegate(self.CorrelationColorDelegate(self.table_view))
        model = self.FilterablePandasTableModel(correlation_df)
        self.table_view.setModel(model)

        # Create a search bar for filtering row labels and connect it to the filtering function
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setPlaceholderText("Search row labels...")
        self.search_bar.textChanged.connect(self.filter_by_row_label)

        # Connect right-click context menu for column filtering
        self.table_view.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_view.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

    def filter_by_row_label(self):
        """Filters the table based on the row label search input."""
        search_text = self.search_bar.text().strip().lower()
        model = self.table_view.model()

        # Apply filter to the row labels based on search text
        model.apply_row_label_filter(search_text)

    def show_header_context_menu(self, position):
        """Shows the context menu when right-clicking on the header."""
        context_menu = QtWidgets.QMenu(self)

        # Get the index of the column being right-clicked
        header_index = self.table_view.horizontalHeader().logicalIndexAt(position)
        column_name = self.table_view.model().headerData(header_index, QtCore.Qt.Orientation.Horizontal)

        # Create the filter options for this column
        filter_action = context_menu.addAction(f"Filter column: {column_name}")
        filter_action.triggered.connect(lambda: self.apply_column_filter(header_index))

        context_menu.exec_(self.table_view.viewport().mapToGlobal(position))

    def apply_column_filter(self, column_index):
        """Apply filter for the selected column."""
        column_name = self.table_view.model().headerData(column_index, QtCore.Qt.Orientation.Horizontal)

        # Get min and max correlation values from input dialog
        min_value, max_value = self.get_column_range_input(column_name)

        if min_value is None or max_value is None:
            return  # Cancel filter if invalid input is given

        # Get the model from the QTableView
        model = self.table_view.model()

        # Apply filter based on the selected column's range using the model's update_filter method
        model.update_filter(column_name, min_value, max_value)

        # Check if filtering resulted in an empty table and reset if necessary
        if model.filtered_df.empty:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data matches the filter criteria.")
            model.filtered_df = model.original_df.copy()  # Reset to original data
            model.layoutChanged.emit()  # Refresh the table to show original data

    def get_column_range_input(self, column_name):
        """Create a dialog to get min and max values for the filter."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Set Range for {column_name}")

        # Create input fields for min and max values
        layout = QtWidgets.QFormLayout()

        min_label = QtWidgets.QLabel(f"Min value for {column_name}:")
        max_label = QtWidgets.QLabel(f"Max value for {column_name}:")
        
        min_input = QtWidgets.QLineEdit()
        max_input = QtWidgets.QLineEdit()
        
        layout.addRow(min_label, min_input)
        layout.addRow(max_label, max_input)

        # OK and Cancel buttons
        ok_button = QtWidgets.QPushButton("OK")
        cancel_button = QtWidgets.QPushButton("Cancel")
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        layout.addRow(buttons_layout)

        dialog.setLayout(layout)

        # Connect buttons
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        result = dialog.exec()
        if result == QtWidgets.QDialog.Accepted:
            min_value = min_input.text().strip()
            max_value = max_input.text().strip()

            # Handle empty values by assigning appropriate min/max based on the column
            if not min_value:
                min_value = self.table_view.model().get_column_min(column_name)
            if not max_value:
                max_value = self.table_view.model().get_column_max(column_name)

            # Convert to float and return
            try:
                return float(min_value), float(max_value)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values.")
                return None, None

        return float('-inf'), float('inf')  # Default range if canceled
    
    class FilterablePandasTableModel(QtCore.QAbstractTableModel):
        """Custom Table Model with row label filtering support."""

        def apply_row_label_filter(self, search_text):
            """Filter the rows based on row label search text."""
            if not search_text:
                self.filtered_df = self.original_df.copy()  # Reset to original if search is empty
            else:
                # Filter rows based on whether the row index (row labels) contains the search text
                self.filtered_df = self.original_df[self.original_df.index.str.contains(search_text, case=False)]
            self.layoutChanged.emit()  # Refresh the table

        def update_filter(self, column_name, min_corr, max_corr):
            """Update the table data based on filter criteria."""
            filtered_df = self.original_df.copy()

            if min_corr is not None and max_corr is not None:
                filtered_df = filtered_df[(filtered_df[column_name] >= min_corr) & (filtered_df[column_name] <= max_corr)]
            else:
                if min_corr is not None:
                    filtered_df = filtered_df[filtered_df[column_name] >= min_corr]
                if max_corr is not None:
                    filtered_df = filtered_df[filtered_df[column_name] <= max_corr]

            filtered_df = filtered_df.dropna(how='all')

            if filtered_df.empty:
                filtered_df = self.original_df.copy()

            self.filtered_df = filtered_df
            self.layoutChanged.emit()  # Refresh the table

        def __init__(self, df=pd.DataFrame(), parent=None):
            super().__init__(parent)
            self.original_df = df
            self.filtered_df = df.copy()

        def rowCount(self, parent=QtCore.QModelIndex()):
            return self.filtered_df.shape[0]

        def columnCount(self, parent=QtCore.QModelIndex()):
            return self.filtered_df.shape[1]

        def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
            if not index.isValid() or role != QtCore.Qt.ItemDataRole.DisplayRole:
                return None
            return str(round(self.filtered_df.iloc[index.row(), index.column()], 3))

        def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
            if role != QtCore.Qt.ItemDataRole.DisplayRole:
                return None
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self.filtered_df.columns[section])
            else:
                return self.filtered_df.index[section]

        def get_column_min(self, column_name):
            """Get the minimum value for a column."""
            return self.original_df[column_name].min()

        def get_column_max(self, column_name):
            """Get the maximum value for a column."""
            return self.original_df[column_name].max()

    class CorrelationColorDelegate(QtWidgets.QStyledItemDelegate):
        """Custom delegate to color code correlation values."""

        def paint(self, painter, option, index):
            if not index.isValid():
                return

            value = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
            try:
                value = float(value)
            except ValueError:
                QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
                return

            # Define color gradients
            if value >= 0:
                r = int(255 * (1 - value))  # More positive → less red
                g = 255  # Full green
                b = int(255 * (1 - value))  # More positive → less blue
            else:
                r = 255  # Full red
                g = int(255 * (1 + value))  # More negative → less green
                b = int(255 * (1 + value))  # More negative → less blue

            painter.fillRect(option.rect, QtGui.QColor(r, g, b))

            # Draw text
            painter.setPen(QtGui.QColor(0, 0, 0))  # Black text
            painter.drawText(option.rect, QtCore.Qt.AlignmentFlag.AlignCenter, index.data())

        def displayText(self, value, locale):
            return f"{float(value):.2f}" if isinstance(value, (float, int)) else value