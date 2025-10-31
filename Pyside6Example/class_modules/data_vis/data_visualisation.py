from PySide6 import QtWidgets, QtGui, QtCore
import pandas as pd
import numpy as np
import pandas as pd
from PySide6 import QtWidgets, QtCore, QtGui
from prophet import Prophet
import numpy as np
import pandas as pd
from PySide6 import QtWidgets, QtCore
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objs import FigureWidget as PlotlyWidget
import pandas as pd
from PySide6 import QtWidgets, QtCore, QtWebEngineWidgets
from prophet import Prophet
import plotly.graph_objects as go
import plotly.offline as py_off

class CorrelationAnalysis(QtWidgets.QWidget):
    def __init__(self, data_frame):
        super().__init__()
        data_frame.iloc[:, 0] = pd.to_datetime(data_frame.iloc[:, 0], dayfirst=True)
        self.data = data_frame
        self.variable = None
        self.current_correlations = pd.Series()

        # Create Widgets
        self.create_widgets()
        self.setLayout(self.layout)

    def create_widgets(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        # Date range selection
        date_layout = QtWidgets.QHBoxLayout()
        self.start_date_edit = QtWidgets.QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        min_date = self.data.iloc[:, 0].min().to_pydatetime().date()
        max_date = self.data.iloc[:, 0].max().to_pydatetime().date()
        self.start_date_edit.setDate(QtCore.QDate(min_date))
        self.start_date_edit.dateChanged.connect(self.update_correlations_based_on_date)
        self.end_date_edit = QtWidgets.QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QtCore.QDate(max_date))
        self.end_date_edit.dateChanged.connect(self.update_correlations_based_on_date)

        date_layout.addWidget(QtWidgets.QLabel("Start Date:"))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QtWidgets.QLabel("End Date:"))
        date_layout.addWidget(self.end_date_edit)
        self.layout.addLayout(date_layout)

        # Dropdown for selecting the variable
        variable_label = QtWidgets.QLabel("Select Variable:")
        self.layout.addWidget(variable_label)

        self.variable_dropdown = QtWidgets.QComboBox()
        self.variable_dropdown.setEditable(True)
        self.all_variables = self.data.columns.tolist()[1:]
        self.variable_dropdown.addItems(self.all_variables)
        self.variable_dropdown.currentIndexChanged.connect(self.update_correlations)

        # Set up the completer for filtering
        completer = QtWidgets.QCompleter(self.all_variables)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.variable_dropdown.setCompleter(completer)
        self.layout.addWidget(self.variable_dropdown)

        # Line edit for filtering results in the tree view
        self.tree_filter_edit = QtWidgets.QLineEdit()
        self.tree_filter_edit.setPlaceholderText("Filter results in table...")
        self.tree_filter_edit.textChanged.connect(self.apply_tree_filter)
        self.layout.addWidget(self.tree_filter_edit)

        # Tree view setup
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['Variable', 'Correlation'])
        self.layout.addWidget(self.tree)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        self.tree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    def update_correlations_based_on_date(self):
        self.update_correlations()

    def update_correlations(self):
        self.variable = self.variable_dropdown.currentText()
        filtered_data = self.filter_data_by_date_range()
        self.current_correlations = self.get_correlations(self.variable, filtered_data)
        self.apply_tree_filter(self.tree_filter_edit.text())

    def filter_data_by_date_range(self):
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        mask = (self.data.iloc[:, 0] >= start_date) & (self.data.iloc[:, 0] <= end_date)
        return self.data.loc[mask]

    def get_correlations(self, selected_variable, data):
        numeric_data = data.select_dtypes(include=[np.number])
        if selected_variable not in numeric_data.columns:
            return pd.Series()
        return numeric_data.corr()[selected_variable].drop(selected_variable, errors='ignore').sort_values(ascending=False)

    def open_context_menu(self, position):
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("Copy Variable Name")
        selected_action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        if selected_action == copy_action:
            selected_item = self.tree.currentItem()
            if selected_item:
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(selected_item.text(0))

    def apply_tree_filter(self, filter_text):
        self.tree.clear()
        for variable, corr in self.current_correlations.items():
            if filter_text.lower() in variable.lower():
                color = self.get_color_for_correlation(corr)
                item = QtWidgets.QTreeWidgetItem([variable, f'{corr:.2f}' if not pd.isna(corr) else 'NaN'])
                item.setBackground(1, QtGui.QBrush(QtGui.QColor(color)))
                self.tree.addTopLevelItem(item)

    def get_color_for_correlation(self, corr):
        if pd.isna(corr):
            return QtGui.QColor(128, 128, 128).name()  # Gray for NaN
        color_positive = (0, 100, 0)   # Dark green
        color_negative = (139, 0, 0)   # Dark red
        color_neutral = (128, 128, 128)  # Gray
        if corr > 0:
            r = color_neutral[0] + (color_positive[0] - color_neutral[0]) * corr
            g = color_neutral[1] + (color_positive[1] - color_neutral[1]) * corr
            b = color_neutral[2] + (color_positive[2] - color_neutral[2]) * corr
        else:
            r = color_neutral[0] + (color_negative[0] - color_neutral[0]) * -corr
            g = color_neutral[1] + (color_negative[1] - color_neutral[1]) * -corr
            b = color_neutral[2] + (color_negative[2] - color_neutral[2]) * -corr
        return QtGui.QColor(int(r), int(g), int(b)).name()

class ChartingTool(QtWidgets.QWidget):
    def __init__(self, data_frame):
        super().__init__()
        self.data = data_frame
        self.data.iloc[:, 0] = pd.to_datetime(self.data.iloc[:, 0], dayfirst=True)

        self.transformation_options = [
            {'label': 'Log', 'value': 'log'},
            {'label': 'Lag & Lead', 'value': 'lag & lead'},
            {'label': 'Adstock', 'value': 'adstock'},
            {'label': 'Diminishing Returns Absolute', 'value': 'diminishing_returns_absolute'},
            {'label': 'Diminishing Returns Exponential', 'value': 'diminishing_returns_exponential'},
            {'label': 'Simple Moving Average', 'value': 'sma'},
        ]

        self.create_widgets()
        self.setLayout(self.layout)

    def create_widgets(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        # Date range selection
        date_layout = QtWidgets.QHBoxLayout()
        self.start_date_edit = QtWidgets.QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        min_date = self.data.iloc[:, 0].min().to_pydatetime().date()
        max_date = self.data.iloc[:, 0].max().to_pydatetime().date()
        self.start_date_edit.setDate(QtCore.QDate(min_date))
        self.start_date_edit.setMaximumDate(QtCore.QDate(max_date))
        self.end_date_edit = QtWidgets.QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QtCore.QDate(max_date))
        self.end_date_edit.setMaximumDate(QtCore.QDate(max_date))
        date_layout.addWidget(QtWidgets.QLabel("Start Date:"))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QtWidgets.QLabel("End Date:"))
        date_layout.addWidget(self.end_date_edit)
        self.layout.addLayout(date_layout)

        # Variable dropdowns and transformation settings
        self.variable_dropdown1 = self.create_variable_dropdown()
        self.transformation_table1 = self.create_transformation_table()
        self.variable_dropdown2 = self.create_variable_dropdown()
        self.transformation_table2 = self.create_transformation_table()

        # Button to trigger the transformation and plot
        self.plot_button = QtWidgets.QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot_data)
        self.layout.addWidget(self.plot_button)

        # Placeholder for graph (could use QChart, QCustomPlot for actual graphing)
        self.graph_placeholder = QtWidgets.QLabel("Graph will be displayed here.")
        self.layout.addWidget(self.graph_placeholder)

    def create_variable_dropdown(self):
        dropdown = QtWidgets.QComboBox()
        dropdown.addItems([var for var in self.data.columns if var != 'Date'])
        self.layout.addWidget(dropdown)
        return dropdown

    def create_transformation_table(self):
        table = QtWidgets.QTableWidget()
        table.setRowCount(len(self.transformation_options))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Transformation Type", "Amount"])
        for i, option in enumerate(self.transformation_options):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(option['label']))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem("0"))
        self.layout.addWidget(table)
        return table

    def plot_data(self):
        # Extract data based on date range and apply transformations
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        filtered_data = self.data[(self.data['OBS'] >= start_date) & (self.data['OBS'] <= end_date)]

        variable1 = self.variable_dropdown1.currentText()
        variable2 = self.variable_dropdown2.currentText()

        transformed_data1 = self.apply_transformations(filtered_data, variable1, self.transformation_table1)
        transformed_data2 = self.apply_transformations(filtered_data, variable2, self.transformation_table2)

        # For now, we will just update the placeholder text to indicate data has been plotted.
        # You could replace this with actual graphing logic using QCustomPlot, QChart, or a similar tool.
        self.graph_placeholder.setText(f"Data plotted for {variable1} and {variable2}.")

    def apply_transformations(self, data, variable_name, transformation_table):
        transformed_variable = data[variable_name].copy()
        for i in range(transformation_table.rowCount()):
            transformation_type = transformation_table.item(i, 0).text()
            amount = float(transformation_table.item(i, 1).text())
            if amount == 0:
                continue
            # Apply transformations here similarly to the original code
            # This is simplified and needs to be adjusted based on your exact needs
        return transformed_variable

class ProphetSeasonality(QtWidgets.QWidget):
    def __init__(self, data_frame):
        super().__init__()
        self.data = data_frame
        self.selected_kpi = self.data.columns[1]

        # Create Widgets
        self.create_widgets()
        self.setLayout(self.layout)

    def create_widgets(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        # KPI Dropdown
        self.kpi_dropdown = QtWidgets.QComboBox()
        self.kpi_options = [var for var in self.data.columns if var != 'Date']
        self.kpi_dropdown.addItems(self.kpi_options)
        self.kpi_dropdown.setCurrentIndex(1)
        self.kpi_dropdown.currentIndexChanged.connect(self.update_graph)
        self.layout.addWidget(self.kpi_dropdown)

        # Plotly Web Engine Views
        self.fig1_view = QtWebEngineWidgets.QWebEngineView()
        self.layout.addWidget(self.fig1_view)

        self.fig2_view = QtWebEngineWidgets.QWebEngineView()
        self.layout.addWidget(self.fig2_view)

        self.fig3_view = QtWebEngineWidgets.QWebEngineView()
        self.layout.addWidget(self.fig3_view)

    def update_graph(self):
        selected_kpi = self.kpi_dropdown.currentText()
        prophet_df = self.data[['OBS', selected_kpi]].rename(columns={'OBS': 'ds', selected_kpi: 'y'})

        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=0)
        forecast = model.predict(future)

        # Update Plotly Views
        self.update_plotly_view(self.fig1_view, forecast, 'yhat', 'Prophet Prediction', selected_kpi)
        self.update_plotly_view(self.fig2_view, forecast, 'trend', 'Trend', 'Trend')
        if 'yearly' in forecast.columns:
            self.update_plotly_view(self.fig3_view, forecast, 'yearly', 'Yearly Seasonality', 'Yearly Seasonality')

    def update_plotly_view(self, web_view, forecast, y_column, title, ylabel):
        fig = go.Figure(go.Scatter(x=forecast['ds'], y=forecast[y_column], name=y_column))
        fig.update_layout(title=title, xaxis_title='OBS', yaxis_title=ylabel)
        div = py_off.plot(fig, include_plotlyjs='cdn', output_type='div')
        html_content = f"<html><head><meta charset='utf-8' /></head><body>{div}</body></html>"
        web_view.setHtml(html_content)
"""

class Dataview(QtWidgets.QWidget):

    class PandasModel(QAbstractTableModel):
        def __init__(self, data):
            super().__init__()
            self._data = data

        def rowCount(self, parent=None):
            return self._data.shape[0]

        def columnCount(self, parent=None):
            return self._data.shape[1]

        def data(self, index, role=Qt.DisplayRole):
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
            return None

        def headerData(self, section, orientation, role):
            if role == Qt.DisplayRole:
                if orientation == Qt.Horizontal:
                    return self._data.columns[section]
                if orientation == Qt.Vertical:
                    return str(self._data.index[section])
            return None

        def update_data(self, new_data):
            self.beginResetModel()
            self._data = new_data
            self.endResetModel()

class TwoTablesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.df = df  # Initialize the dataframe as an instance variable
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Summary type dropdown
        self.summary_type_dropdown = QComboBox(self)
        self.summary_type_dropdown.addItems(["Yearly", "Last 52 Weeks"])
        self.summary_type_dropdown.currentTextChanged.connect(self.update_summary_table)
        self.summary_type_dropdown.setStyleSheet("color: white; background-color: #2b2b2b;")

        # Aggregation type dropdown
        self.aggregation_type_dropdown = QComboBox(self)
        self.aggregation_type_dropdown.addItems(["Sum", "Average"])
        self.aggregation_type_dropdown.currentTextChanged.connect(self.update_summary_table)
        self.aggregation_type_dropdown.setStyleSheet("color: white; background-color: #2b2b2b;")

        # Page selector for raw data table
        self.raw_page_selector = QSpinBox(self)
        self.raw_page_selector.setRange(1, (num_columns + columns_per_page - 1) // columns_per_page)
        self.raw_page_selector.valueChanged.connect(self.update_raw_table)
        self.raw_page_selector.setStyleSheet("color: white; background-color: #2b2b2b;")

        # Page selector for summary data table
        self.summary_page_selector = QSpinBox(self)
        self.summary_page_selector.setRange(1, (num_columns + columns_per_page - 1) // columns_per_page)
        self.summary_page_selector.valueChanged.connect(self.update_summary_table)
        self.summary_page_selector.setStyleSheet("color: white; background-color: #2b2b2b;")

        # Export button
        self.export_button = QPushButton("Export to Excel", self)
        self.export_button.setStyleSheet("color: white; background-color: #2b2b2b;")
        self.export_button.clicked.connect(self.export_to_excel)  

        # Add controls to layout
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.summary_type_dropdown)
        control_layout.addWidget(self.aggregation_type_dropdown)
        control_layout.addWidget(QLabel("Raw Table Page:"))
        control_layout.addWidget(self.raw_page_selector)
        control_layout.addWidget(QLabel("Summary Table Page:"))
        control_layout.addWidget(self.summary_page_selector)
        control_layout.addWidget(self.export_button)
        layout.addLayout(control_layout)

        # Summary data table
        self.summary_data_table = QTableView(self)
        self.summary_data_table.setStyleSheet("color: white;")
        self.summary_data_model = PandasModel(pd.DataFrame())
        self.summary_data_table.setModel(self.summary_data_model)
        self.summary_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.create_card("Data Summary", self.summary_data_table))

        # Raw data table
        self.raw_data_table = QTableView(self)
        self.raw_data_table.setStyleSheet("color: white;")
        self.raw_data_model = PandasModel(self.df.iloc[:, :columns_per_page])  # Display initial 10 columns
        self.raw_data_table.setModel(self.raw_data_model)
        self.raw_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.create_card("Raw Data", self.raw_data_table))

        self.setLayout(layout)
        self.setWindowTitle("Raw Data and Summary Example")
        self.update_tables()

    def create_card(self, title, table):
        card_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white;")
        card_layout.addWidget(title_label)
        card_layout.addWidget(table)
        card_widget = QWidget()
        card_widget.setLayout(card_layout)
        return card_widget

    def update_tables(self):
        self.update_summary_table()
        self.update_raw_table()

    def update_summary_table(self):
        df = self.df.copy()
        summary_type = self.summary_type_dropdown.currentText().lower()
        aggregation_type = self.aggregation_type_dropdown.currentText().lower()
        selected_page = self.summary_page_selector.value()

        if summary_type == 'yearly':
            df['Period'] = pd.to_datetime(df['obs']).dt.year
        else:
            df_sorted = df.sort_values(by='obs', ascending=False)
            df_sorted['Period'] = (df_sorted.index // 52) + 1
            df = df_sorted

        grouped_data = df.groupby('Period')

        if aggregation_type == 'sum':
            aggregated_data = grouped_data.sum(numeric_only=True)
        else:
            aggregated_data = grouped_data.mean(numeric_only=True)

        summary_df = aggregated_data
        summary_df['Period'] = summary_df.index

        start_col = (selected_page - 1) * columns_per_page
        end_col = min(selected_page * columns_per_page, num_columns)

        page_summary_data = summary_df.iloc[:, start_col:end_col]
        self.summary_data_model.update_data(page_summary_data.reset_index(drop=True))

    def update_raw_table(self):
        selected_page = self.raw_page_selector.value()

        start_col = (selected_page - 1) * columns_per_page
        end_col = min(selected_page * columns_per_page, num_columns)

        page_raw_data = self.df.iloc[:, start_col:end_col]
        self.raw_data_model.update_data(page_raw_data)

    def export_to_excel(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx)", options=options)
        if file_path:
            raw_data_df = self.raw_data_model._data
            summary_data_df = self.summary_data_model._data
            with pd.ExcelWriter(file_path) as writer:
                raw_data_df.to_excel(writer, sheet_name='Raw Data', index=False)
                summary_data_df.to_excel(writer, sheet_name='Data Summary', index=False)
"""