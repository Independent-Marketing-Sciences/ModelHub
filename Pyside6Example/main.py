import sys
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QListWidget, QListWidgetItem, QStackedWidget, QLabel, QHBoxLayout, QWidget, 
                                QVBoxLayout, QLineEdit, QSizePolicy, QPushButton, QMessageBox, QFileDialog, QDialog)
from PySide6.QtGui import QIcon, QFont, QFontDatabase, QPixmap
from PySide6.QtCore import QSize, Qt, Signal
from class_modules.data_vis.data_visualisation import CorrelationAnalysis, ChartingTool, ProphetSeasonality
from class_modules.company_reaserch.stocks import GetCompanyOverview, Superinvestors, AnnualFundamentalAnalysis, QuarterlyFundamentalAnalysis, TechnicalAnalysis
from class_modules.modelling.modelling import ModelDetails, RawData, VariableDetails, XSDetails, TransformedData, Contribution, ModelStats, Decomp, AvM, ResidualCorrelation
import time

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(400, 300, 300, 200)
        layout = QVBoxLayout()
        self.username_input = QLineEdit()
        
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)
        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username == "a" and password == "a":
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")

class MainWindow(QMainWindow):
    def __init__(self, df=None):
        super().__init__()
        self.df = df
        self.user_logged_in = True
        self.correlation_analysis = None
        self.charting_tool = None
        self.prophet_seasonality = None
        self.data_view = None
        self.companyoverview = None
        self.superinvestors = None
        self.anual = None
        self.quaterly = None
        self.ta = None
        self.modeldetails = None
        self.rawdata = None
        self.variabledetails = None
        self.xsdetails = None
        self.transformeddata = None
        self.contribution = None
        self.regression_run = False
        self.modelstats = None
        self.decomp = None
        self.avm = None
        self.residcorr = None
        self.cached_model_details_input = None
        self.cached_variable_details_input = None

        QFontDatabase.addApplicationFont("Raleway/Raleway-Regular.ttf")
        custom_font = QFont("Raleway", 12)
        self.setFont(custom_font)
        self.setWindowTitle("IMS MMM TOOL")
        self.setGeometry(200, 200, 1000, 600)
        """
        topBarLayout = QHBoxLayout()    
        pixmap = QPixmap("static/IMS_logo.png")
        max_logo_width = 50
        pixmap = pixmap.scaledToWidth(max_logo_width, Qt.SmoothTransformation)
        logoLabel = QLabel()
        logoLabel.setPixmap(pixmap)
        logoLabel.setStyleSheet("background-color: transparent;") 
        
        searchBox = QLineEdit()
        searchBox.setPlaceholderText("Search...")
        searchBox.setStyleSheet("background-color: white; border-radius: 30px;")
        searchBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        searchBox.setAlignment(Qt.AlignCenter)
        searchBox.setMinimumWidth(500)
        searchBox.setFixedHeight(20)
        
        topBarLayout.addWidget(logoLabel)
        topBarLayout.addStretch(1)
        topBarLayout.addWidget(searchBox)
        topBarLayout.addStretch(1)
        topBarWidget = QWidget()
        topBarWidget.setLayout(topBarLayout)
        gradient_style = 
        QWidget { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
            stop:0 rgba(12, 24, 123, 255), stop:1 rgba(3, 8, 67, 255)); 
            border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-right-radius: 10px;}
        
        topBarWidget.setStyleSheet(gradient_style)
        """
        self.sideMenu = QListWidget()
        self.sideMenu.setStyleSheet("""
            QListWidget { 
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, 
                stop:0 rgba(12, 24, 123, 255), stop:1 rgba(3, 8, 67, 255)); 
                border: none; 
                color: white; 
                border-bottom-left-radius: 10px; 
            }
            QListWidget::item { 
                margin: 5px; 
                padding: 5px; 
            }
            QListWidget::item:selected { 
                background-color: rgb(64, 64, 64); 
                border-radius: 10px; 
                color: white; 
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        
        self.sideMenu.setFocusPolicy(Qt.NoFocus)
        self.sideMenu.setIconSize(QSize(48, 48))
        self.add_items(self.sideMenu, [
            ("Data Visualisation", "sideimages/data_vis.png"),
            ("Company Research", "sideimages/stocks.png"),
            ("Modelling", "sideimages/model.png"),
            ("Consolidator", "sideimages/consolidate.png"),
            ("Simulator", "sideimages/simulate.png"),
            ("Response Curves", "sideimages/response.png"),
            ("Optimiser", "sideimages/optimise.png"),
            ("IMA", "sideimages/ai.png"),
        ])
        self.adjustListWidgetWidth(self.sideMenu)
        
        self.subMenu = QListWidget()
        self.subMenu.setStyleSheet("""
            QListWidget { 
                background-color: rgb(232, 232, 247); 
                color: black; 
                border: none; 
                margin-left: 0; 
                border-bottom-right-radius: 10px; 
            }
            QListWidget::item { 
                padding: 5px; 
                margin: 5px; 
            }
            QListWidget::item:selected { 
                background-color: rgb(12, 24, 123); 
                border-radius: 10px; 
                color: white; 
            }
            QListWidget::item:focus {
                outline: none;
                border: none;
            }
        """)
        self.subMenu.setFocusPolicy(Qt.NoFocus)
        self.subMenu.setFixedWidth(200)
        
        self.contentArea = QStackedWidget()
        layout = QVBoxLayout()
        #layout.addWidget(topBarWidget)
        layout.setSpacing(0)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.sideMenu)
        h_layout.addWidget(self.subMenu)
        h_layout.addWidget(self.contentArea, 1)
        layout.addLayout(h_layout)
        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)
        self.sideMenu.currentRowChanged.connect(self.updateSubMenu)
        self.subMenu.currentItemChanged.connect(self.updateContentAreaFromSubMenu)

    def add_items(self, list_widget, items):
        for text, icon_path in items:
            item = QListWidgetItem(QIcon(icon_path), text)
            list_widget.addItem(item)

    def adjustListWidgetWidth(self, list_widget):
        max_width = 0
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            font_metrics = self.fontMetrics()
            text_width = font_metrics.horizontalAdvance(item.text()) + 70
            max_width = max(max_width, text_width)
        list_widget.setFixedWidth(max_width + 10)

    def updateContentAreaFromSubMenu(self, current):
        if current and current.text() == "Correlation Analysis":
            if self.correlation_analysis is None or self.df is None:
                self.correlation_analysis = CorrelationAnalysis(self.df)
                self.contentArea.addWidget(self.correlation_analysis)
            self.contentArea.setCurrentWidget(self.correlation_analysis)
        elif current and current.text() == "Charting Tool":
            if self.charting_tool is None or self.df is None:
                self.charting_tool = ChartingTool(self.df)
                self.contentArea.addWidget(self.charting_tool)
            self.contentArea.setCurrentWidget(self.charting_tool)
        elif current and current.text() == "Prophet Seasonality":
            if self.prophet_seasonality is None or self.df is None:
                self.prophet_seasonality = ProphetSeasonality(self.df)
                self.contentArea.addWidget(self.prophet_seasonality)
            self.contentArea.setCurrentWidget(self.prophet_seasonality)
        elif current and current.text() == "Data View":
            if self.prophet_seasonality is None or self.df is None:
                self.prophet_seasonality = ProphetSeasonality(self.df)
                self.contentArea.addWidget(self.prophet_seasonality)
            self.contentArea.setCurrentWidget(self.prophet_seasonality)

        elif current and current.text() == "Company Overview":
            if self.companyoverview is None or self.df is None:
                self.companyoverview = GetCompanyOverview(self)
                self.contentArea.addWidget(self.companyoverview)
            self.contentArea.setCurrentWidget(self.companyoverview)
        elif current and current.text() == "Technical Analysis":
            if self.ta is None or self.df is None:
                self.ta = TechnicalAnalysis(self)
                self.contentArea.addWidget(self.ta)
            self.contentArea.setCurrentWidget(self.ta)
        elif current and current.text() == "Annual Fundemental Analysis":
            if self.anual is None or self.df is None:
                self.anual = AnnualFundamentalAnalysis(self)
                self.contentArea.addWidget(self.anual)
            self.contentArea.setCurrentWidget(self.anual)
        elif current and current.text() == "Quaterly Fundemental Analysis":
            if self.quaterly is None or self.df is None:
                self.quaterly = QuarterlyFundamentalAnalysis(self)
                self.contentArea.addWidget(self.quaterly)
            self.contentArea.setCurrentWidget(self.quaterly)
        elif current and current.text() == "Superinvestors":
            if self.superinvestors is None or self.df is None:
                self.superinvestors = Superinvestors(self)
                self.contentArea.addWidget(self.superinvestors)
            self.contentArea.setCurrentWidget(self.superinvestors)

        # Model Details Tab
        elif current and current.text() == "Model Details":
            self.initialize_model_details()
            # Ensure the signal is connected only once
            self.contentArea.setCurrentWidget(self.modeldetails)

        # Raw Data Tab
        elif current and current.text() == "Raw Data":
            if self.rawdata is None or self.df is None:
                self.rawdata = RawData(self.df)
                self.contentArea.addWidget(self.rawdata)
            self.contentArea.setCurrentWidget(self.rawdata)

        # XS Details Tab
        elif current and current.text() == "XS Details":
            if self.modeldetails is None:
                self.initialize_model_details()
            self.initialize_xsdetails()
            # Ensure xsdetails has been added to contentArea
            if self.contentArea.indexOf(self.xsdetails) == -1:
                self.contentArea.addWidget(self.xsdetails)
            self.contentArea.setCurrentWidget(self.xsdetails)
        
        
        # Variable Details Tab
        elif current and current.text() == "Variable Details":
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.xsdetails is None:
                self.initialize_xsdetails()
            self.initialize_variabledetails()
            self.contentArea.setCurrentWidget(self.variabledetails)

        # Transformed Data Tab
        elif current and current.text() == "Transformed Data":
            if not self.regression_run:
                QMessageBox.warning(self, "Run Regression First", "You must run the regression before accessing the Transformed Data tab.")
                return
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.variabledetails is None:    
                self.initialize_variabledetails()
            self.initialize_transformeddata()
            self.contentArea.setCurrentWidget(self.transformeddata)
    
        # Contribution Tab
        elif current and current.text() == "Contribution":
            if not self.regression_run:
                QMessageBox.warning(self, "Run Regression First", "You must run the regression before accessing the Contribution tab.")
                return
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.variabledetails is None:    
                self.initialize_variabledetails()
            if self.transformeddata is None:
                self.initialize_transformeddata()
            self.initialize_contribution()
            self.contentArea.setCurrentWidget(self.contribution)
        
        # Model Stats Tab
        elif current and current.text() == "Model Stats":
            if not self.regression_run:
                QMessageBox.warning(self, "Run Regression First", "You must run the regression before accessing the Model Stats tab.")
                return
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.variabledetails is None:    
                self.initialize_variabledetails()
            if self.transformeddata is None:
                self.initialize_transformeddata()
            if self.contribution is None:
                self.initialize_contribution()
            self.initialize_modelstats()
            self.contentArea.setCurrentWidget(self.modelstats)
            
        # Decomp Tab
        elif current and current.text() == "Decomp":
            if not self.regression_run:
                QMessageBox.warning(self, "Run Regression First", "You must run the regression before accessing the Decomp tab.")
                return
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.variabledetails is None:    
                self.initialize_variabledetails()
            if self.transformeddata is None:
                self.initialize_transformeddata()
            if self.contribution is None:
                self.initialize_contribution()
            if self.modelstats is None:
                self.initialize_modelstats()
            self.initialize_decomp()
            self.contentArea.setCurrentWidget(self.decomp)
            
        # AvM Tab
        elif current and current.text() == "AvM":
            if not self.regression_run:
                QMessageBox.warning(self, "Run Regression First", "You must run the regression before accessing the AvM tab.")
                return
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.variabledetails is None:    
                self.initialize_variabledetails()
            if self.transformeddata is None:
                self.initialize_transformeddata()
            if self.contribution is None:
                self.initialize_contribution()
            if self.modelstats is None:
                self.initialize_modelstats()
            if self.decomp is None:
                self.initialize_decomp()
            self.initialize_avm()
            self.contentArea.setCurrentWidget(self.avm)
    
        # Residual Correlation Tab
        elif current and current.text() == "Residual Correlation":
            if not self.regression_run:
                QMessageBox.warning(self, "Run Regression First", "You must run the regression before accessing the Residual Correlation tab.")
                return
            if self.modeldetails is None:
                self.initialize_model_details()
            if self.variabledetails is None:    
                self.initialize_variabledetails()
            if self.transformeddata is None:
                self.initialize_transformeddata()
            if self.contribution is None:
                self.initialize_contribution()
            if self.modelstats is None:
                self.initialize_modelstats()
            if self.decomp is None:
                self.initialize_decomp()
            if self.avm is None:
                self.initialize_avm()
            self.initialize_residcorrelation()
            self.contentArea.setCurrentWidget(self.residcorr)

    def get_cached_model_details_input(self):
        """
        Check if the cached model details are initialized and up-to-date.
        Update and return the cached details if necessary.
        """
        model_details_input = (
            self.modeldetails.current_kpi, 
            self.modeldetails.current_start_date, 
            self.modeldetails.current_end_date,
            self.modeldetails.xs_weights,
            self.modeldetails.current_log_trans_bias,
            self.modeldetails.current_take_anti_logs_at_midpoints
        )

        # Initialize the cache if it does not exist
        if not hasattr(self, 'cached_model_details_input') or not self.cached_model_details_input:
            self.cached_model_details_input = model_details_input

        # Update the cache if the details have changed
        if self.cached_model_details_input != model_details_input:
            self.cached_model_details_input = model_details_input

        return self.cached_model_details_input
    
    def get_cached_variable_details_input(self, model_details_input=None,xs_details_input=None):
        """
        Check if cached variable details are initialized and up-to-date.
        Update and return the cached details if necessary.
        """
        # Ensure model_details_input is provided
        if model_details_input is None:
            model_details_input = self.get_cached_model_details_input()
        
        # Ensure xs_details_input is provided
        if xs_details_input is None:
            _,xs_details_input = self.get_cached_xs_details_input()
        
        variable_details = VariableDetails(self.df, model_details_input, xs_details_input)
        variable_details_input = variable_details.get_variable_details()
        # Initialize or update the cache if necessary
        if not hasattr(self, "cached_variable_details_input") or self.cached_variable_details_input is None:
            self.cached_variable_details_input = variable_details_input
        # Update the cache if the details have changed
        if not self.cached_variable_details_input.equals(variable_details_input):
            self.cached_variable_details_input = variable_details_input

        return variable_details,self.cached_variable_details_input
    
    def get_cached_xs_details_input(self, model_details_input=None):
        """
        Check if cached xs details are initialized and up-to-date.
        Update and return the cached details if necessary.
        """
        # Ensure model_details_input is provided
        if model_details_input is None:
            model_details_input = self.get_cached_model_details_input()
        
        xs_details = XSDetails(self.df, model_details_input)
        xs_details_input = xs_details.get_xs_details()
        
        # Initialize or update the cache if necessary
        if not hasattr(self, "cached_xs_details_input") or self.cached_xs_details_input is None:
            self.cached_xs_details_input = xs_details_input
        
        # Update the cache if the details have changed
        if not self.cached_xs_details_input.equals(xs_details_input):
            self.cached_xs_details_input = xs_details_input

        return xs_details, self.cached_xs_details_input
    
    def initialize_model_details(self):
        """Ensure ModelDetails is initialized and added only once."""
        if self.modeldetails is None or self.df is None:
            self.modeldetails = ModelDetails(self.df)
            self.contentArea.addWidget(self.modeldetails)

    def initialize_variabledetails(self):
        """Ensure VariableDetails is initialized and added only once."""
        if self.variabledetails is None or self.df is None:
            self.cached_model_details = self.get_cached_model_details_input()
            self.xsdetails,self.cached_xs_details_input = self.get_cached_xs_details_input(self.cached_model_details)
            self.variabledetails,self.variabledetails_input = self.get_cached_variable_details_input(self.cached_model_details,self.cached_xs_details_input)
            # Connect signals
            self.variabledetails.regression_requested.connect(self.run_variable_details_regression)
            self.variabledetails.request_model_details.connect(self.modeldetails.emit_current_model_details)
            self.variabledetails.request_xs_details.connect(self.xsdetails.emit_current_xs_details)
            self.modeldetails.model_details_updated.connect(self.variabledetails.receive_model_details)
            self.variabledetails.regression_complete.connect(self.set_regression_run)
            self.contentArea.addWidget(self.variabledetails)
    
    def initialize_xsdetails(self):
        """Ensure VariableDetails is initialized and added only once."""
        if self.xsdetails is None or self.df is None:
            self.cached_model_details = self.get_cached_model_details_input()
            self.xsdetails,_ = self.get_cached_xs_details_input(self.cached_model_details)
            # self.xsdetails = XSDetails(self.df,self.cached_model_details)
            self.contentArea.addWidget(self.xsdetails)
    
    def run_variable_details_regression(self):
        """Run the regression for VariableDetails and cache the results."""
        if self.variabledetails is not None:
            self.variabledetails_input = self.get_cached_variable_details_input()
            # self.variable_details_input_df,self.transformed_dict,self.model_results,self.model_diagnostics,self.predicted_values,self.residuals = self.variabledetails.run_regression(self.variabledetails_input)
            start_time = time.time()
            self.variable_details_input_df,self.transformed_dict, self.model_results_dict = self.variabledetails.run_regression(self.variabledetails_input)
            QMessageBox.information(self, "Regression Complete", f"Total time for regression: {time.time() - start_time:.2f} seconds")

    def set_regression_run(self):
        """Set the regression_run flag to True."""
        self.regression_run = True

    def initialize_transformeddata(self):
        """Ensure TransformedData is initialized and added only once."""
        if self.transformeddata is None or self.df is None:
            self.cached_model_details = self.get_cached_model_details_input()
            _,self.cached_variable_details_input_df = self.get_cached_variable_details_input()
            self.xsdetails,self.cached_xs_details_input_df = self.get_cached_xs_details_input(self.cached_model_details)
            self.transformeddata = TransformedData(self.df, self.cached_model_details, self.cached_variable_details_input_df,self.cached_xs_details_input_df)
            # Connect signals
            self.modeldetails.model_details_updated.connect(lambda data: self.transformeddata.update_transformed_data(model_details_input=data))
            self.variabledetails.variable_details_updated.connect(lambda data: self.transformeddata.update_transformed_data(variable_details_input_df=data))
            self.contentArea.addWidget(self.transformeddata)

    def initialize_contribution(self):
        """Ensure Contribution is initialized with the transformed DataFrame."""
        if self.contribution is None or self.df is None:
            self.cached_model_details = self.get_cached_model_details_input()
            _,self.cached_variable_details_input_df = self.get_cached_variable_details_input()
            _,self.cached_xs_details_input_df = self.get_cached_xs_details_input(self.cached_model_details)
            self.contribution = Contribution(self.cached_model_details, self.cached_xs_details_input_df, self.cached_variable_details_input_df,self.transformed_dict)  # Pass it to the Contribution widget
            # Connect the method to update transformed_df if necessary
            # self.variabledetails.transformed_dict_updated.connect(lambda data: self.contribution.update_transformed_dict(transformed_dict=data))
            # self.variabledetails.variable_details_updated.connect(lambda data: self.contribution.update_variable_details_input_df(variable_details_input_df=data))
            # Connect the model_results_updated signal to a method that updates the table in Contribution
            # self.contribution.populate_table(self.model_results)
            self.contribution.populate_table(self.model_results_dict,self.cached_variable_details_input_df)
            # self.contribution.update_transformed_dict(self.transformed_dict)
            # self.contribution.update_variable_details_input_df(self.cached_variable_details_input_df)
            self.contentArea.addWidget(self.contribution)
    
    def initialize_modelstats(self):
        """Ensure Model Stats is initialized with the up to date model."""
        if self.modelstats is None or self.df is None:
            self.cached_model_details = self.get_cached_model_details_input()
            _,self.cached_variable_details_input_df = self.get_cached_variable_details_input()
            # self.modelstats = ModelStats(self.model_diagnostics, self.residuals)
            self.modelstats = ModelStats(self.model_results_dict[1][1], self.model_results_dict[1][3])
            # Connect the method to update transformed_df if necessary
            # self.variabledetails.model_diagnostics_updated.connect(lambda data: self.modelstats.update_model_diagnostics(model_stats=data))
            self.modelstats.populate_table(self.model_results_dict[1][1])
            # self.modelstats.update_model_diagnostics(self.modelstats)
            self.contentArea.addWidget(self.modelstats)

    def initialize_decomp(self):
        """Ensure Decomp is initialized with the up to date model."""
        if self.decomp is None or self.df is None:
            self.cached_model_details = self.get_cached_model_details_input()
            _ ,self.cache_xs_details_input = self.get_cached_xs_details_input(self.cached_model_details)
            _,self.cached_variable_details_input_df = self.get_cached_variable_details_input()
            self.decomp = Decomp(self.cached_model_details, self.cache_xs_details_input, self.cached_variable_details_input_df, self.transformed_dict, self.model_results_dict[1][0], self.model_results_dict[1][1], self.model_results_dict[1][2])
            # Connect the method to update transformed_df if necessary
            # self.variabledetails.model_diagnostics_updated.connect(lambda data: self.modelstats.update_model_diagnostics(model_stats=data))
            # self.modelstats.populate_table(self.model_diagnostics)
            # self.modelstats.update_model_diagnostics(self.modelstats)
            self.contentArea.addWidget(self.decomp)
    
    def initialize_avm(self):
        """Ensure AvM is initialized with the up to date model."""
        if self.avm is None or self.df is None:
            self.avm = AvM(self.model_results_dict[1][4])
            self.contentArea.addWidget(self.avm)
            
    def initialize_residcorrelation(self):
        """Ensure AvM is initialized with the up to date model."""
        if self.residcorr is None or self.df is None:
            self.residcorr = ResidualCorrelation(self.df, self.model_results_dict[1][4])
            self.contentArea.addWidget(self.residcorr)
    
    def updateSubMenu(self, index):
        sub_items = {
            0: ["Data Summary View", "Charting Tool", "Correlation Analysis", "Prophet Seasonality", "Data Validation Export"],
            1: ["Company Overview", "Technical Analysis", "Annual Fundemental Analysis", "Quaterly Fundemental Analysis", "News", "Superinvestors", "Sentiment Analysis", "Macroeconomic Charts"],
            2: ["Model Details", "Variable Details", "XS Details", "Contribution", "Model Stats","Decomp", "Raw Data", "Transformed Data", "AvM", "Residual Correlation"],
            3: ["Prenested Models", "Nesting Options", "Postnested Models"],
            4: ["Varible Options", "Spend Varibles", "Manual Varibles", "Combined Models", "Raw Data", "Individual Models", "ML Simulation"], 
            5: ["Response Curves", "Recalibrate", "Global", "Bell Curve", "N Curves"],
            6: ["Revenue Maximisation", "Cost Minimsation", "CAPM"],
            7: ["Code Generater"]
        }.get(index, [])

        self.subMenu.clear()
        for item in sub_items:
            self.subMenu.addItem(item)

    def upload_dataframe(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("CSV files (*.csv)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            try:
                df = pd.read_csv(file_path)
                return df
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load dataframe: {e}")
                return None

# def main():
#     app = QApplication(sys.argv)
#     file_path = "C:/Users/Tom Gray/im-sciences.com/FileShare - MasterDrive/Dev/04 - Python Modelling Toolkit/02 - Code, Implementation & Testing/V0.1 - A sample outlook on UX/DataSet.csv"
#     df = pd.read_csv(file_path)
#     window = MainWindow(df)
#     window.show()
#     sys.exit(app.exec())
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_path = "C:/Users/Tom Gray/im-sciences.com/FileShare - MasterDrive/Dev/04 - Python Modelling Toolkit/02 - Code, Implementation & Testing/V0.2 - A sample outlook on UX/Bensons Dataset Feb24 v2.csv"
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.lower()
    window = MainWindow(df)
    window.show()
    sys.exit(app.exec())
    # py_hot_reload.run_with_reloader(main)
    # login_window = LoginWindow()
    # if login_window.exec() == QDialog.Accepted:
    # file_dialog = QFileDialog()
    # file_dialog.setFileMode(QFileDialog.ExistingFile)
    # file_dialog.setNameFilter("CSV files (*.csv)")
    # if file_dialog.exec():
    #     file_path = file_dialog.selectedFiles()[0]
    #     try:
    #         df = pd.read_csv(file_path)
    #         window = MainWindow(df)
    #         window.show()
    #         sys.exit(app.exec())
    #     except Exception as e:
    #         QMessageBox.warning(None, "Error", f"Failed to load dataframe: {e}")
    # else:
    #     QMessageBox.warning(None, "Error", "Data upload cancelled")
else:
    sys.exit(0)