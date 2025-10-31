from PySide6 import QtWidgets
import yfinance as yf
import requests
import pandas as pd
from PySide6 import QtWidgets, QtGui, QtCore
import requests
import requests
import os
import certifi
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from PySide6.QtWebEngineWidgets import QWebEngineView
import yfinance as yf
import plotly.graph_objects as go
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
from plotly.offline import plot
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QApplication, QVBoxLayout, QLineEdit, QPushButton, QDateEdit, QCheckBox
from PySide6.QtWebEngineWidgets import QWebEngineView


class GetCompanyOverview(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        
        self.stock_ticker_input = QtWidgets.QLineEdit(self)
        self.stock_ticker_input.setPlaceholderText("Enter Stock Ticker")
        self.submit_button = QtWidgets.QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.update_company_info)
        
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.stock_ticker_input)
        input_layout.addWidget(self.submit_button)
        
        self.company_info_display = QtWidgets.QTextBrowser(self)
        self.company_info_display.setOpenLinks(False)
        self.company_info_display.anchorClicked.connect(self.open_link_in_browser)
        
        layout.addLayout(input_layout)
        layout.addWidget(self.company_info_display)
        
        self.setLayout(layout)
        self.setWindowTitle("Stock Info")
        
    def open_link_in_browser(self, url):
        QtGui.QDesktopServices.openUrl(url)
        
    def update_company_info(self):
        ticker = self.stock_ticker_input.text()
        
        if not ticker:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a stock ticker.")
            return
        
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info
            
            if not info:
                QtWidgets.QMessageBox.warning(self, "Ticker Error", "Could not retrieve data for the entered ticker.")
                return
            
            def format_number(value):
                try:
                    if value is None:
                        return 'N/A'
                    return f"{int(value):,}"
                except (ValueError, TypeError):
                    return 'N/A'
            
            def format_percentage(value):
                try:
                    if value is None:
                        return 'N/A'
                    return f"{float(value) * 100:.2f}%"
                except (ValueError, TypeError):
                    return 'N/A'
            
            def format_value(value):
                try:
                    if value is None:
                        return 'N/A'
                    return f"{float(value):.2f}"
                except (ValueError, TypeError):
                    return 'N/A'
            
            logo_url = f"https://logo.clearbit.com/{info.get('website', '').split('//')[-1]}"
            response = requests.get(logo_url)
            logo_path = None
            if response.status_code == 200:
                if not os.path.exists('company_images'):
                    os.makedirs('company_images')
                logo_path = os.path.join('company_images', f"{ticker}_logo.png")
                with open(logo_path, 'wb') as file:
                    file.write(response.content)
            
            five_year_avg_dividend_yield = info.get('fiveYearAvgDividendYield', None)
            if five_year_avg_dividend_yield is not None:
                five_year_avg_dividend_yield /= 100
            
            company_info_text = f"""
            <div style="position: relative;">
                <div style="position: absolute; top: 0; right: 0;">
                    {f'<img src="{logo_path}" style="height: 50px; width: 50px;">' if logo_path else ''}
                </div>
                <h3>{info.get('longName', 'Unknown Company')} ({ticker.upper()})</h3>
                <p><b>Address:</b> {info.get('address1', 'N/A')}, {info.get('city', 'N/A')}, {info.get('state', 'N/A')}, {info.get('zip', 'N/A')}, {info.get('country', 'N/A')}</p>
                <p><b>Phone:</b> {info.get('phone', 'N/A')}</p>
                <p><b>Website:</b> <a href="{info.get('website', '#')}" target="_blank">{info.get('website', 'N/A')}</a></p>
                <p><b>Industry:</b> {info.get('industry', 'N/A')}</p>
                <p><b>Sector:</b> {info.get('sector', 'N/A')}</p>
                <p><b>Business Summary:</b> {info.get('longBusinessSummary', 'N/A')}</p>
                <p><b>Full-time Employees:</b> {format_number(info.get('fullTimeEmployees', 'N/A'))}</p>
                <p><b>Company Officers:</b></p>
                <ul>
                {"".join([f"<li>{officer.get('name', 'N/A')} - {officer.get('title', 'N/A')}</li>" for officer in info.get('companyOfficers', [])])}
                </ul>
                <p><b>Dividend Yield:</b> {format_percentage(info.get('dividendYield', None))}</p>
                <p><b>5-Year Avg Dividend Yield:</b> {format_percentage(five_year_avg_dividend_yield)}</p>
                <p><b>Forward P/E:</b> {format_value(info.get('forwardPE', None))}</p>
                <p><b>Payout Ratio:</b> {format_percentage(info.get('payoutRatio', None))}</p>
                <p><b>Analyst Recommendation:</b> {format_value(info.get('recommendationMean', None))} ({info.get('recommendationKey', 'N/A')})</p>
                <p><b>Number of Analyst Opinions:</b> {format_number(info.get('numberOfAnalystOpinions', 'N/A'))}</p>
                <p><b>Gross Margins:</b> {format_percentage(info.get('grossMargins', None))}</p>
                <p><b>Previous Close:</b> {format_value(info.get('previousClose', 'N/A'))}</p>
                <p><b>Open:</b> {format_value(info.get('open', 'N/A'))}</p>
                <p><b>Day Low:</b> {format_value(info.get('dayLow', 'N/A'))}</p>
                <p><b>Day High:</b> {format_value(info.get('dayHigh', 'N/A'))}</p>
                <p><b>Market Cap:</b> {format_number(info.get('marketCap', 'N/A'))}</p>
                <p><b>52 Week Low:</b> {format_value(info.get('fiftyTwoWeekLow', 'N/A'))}</p>
                <p><b>52 Week High:</b> {format_value(info.get('fiftyTwoWeekHigh', 'N/A'))}</p>
                <p><b>Volume:</b> {format_number(info.get('volume', 'N/A'))}</p>
                <p><b>Average Volume:</b> {format_number(info.get('averageVolume', 'N/A'))}</p>
                <p><b>Beta:</b> {format_value(info.get('beta', 'N/A'))}</p>
                <p><b>Trailing P/E:</b> {format_value(info.get('trailingPE', 'N/A'))}</p>
                <p><b>Forward P/E:</b> {format_value(info.get('forwardPE', 'N/A'))}</p>
                <p><b>Dividend Rate:</b> {format_value(info.get('dividendRate', 'N/A'))}</p>
                <p><b>Enterprise Value:</b> {format_number(info.get('enterpriseValue', 'N/A'))}</p>
                <p><b>Profit Margins:</b> {format_percentage(info.get('profitMargins', None))}</p>
                <p><b>Float Shares:</b> {format_number(info.get('floatShares', 'N/A'))}</p>
                <p><b>Shares Outstanding:</b> {format_number(info.get('sharesOutstanding', 'N/A'))}</p>
                <p><b>Short Ratio:</b> {format_value(info.get('shortRatio', 'N/A'))}</p>
                <p><b>Book Value:</b> {format_value(info.get('bookValue', 'N/A'))}</p>
                <p><b>Price to Book:</b> {format_value(info.get('priceToBook', 'N/A'))}</p>
                <p><b>Earnings Growth:</b> {format_percentage(info.get('earningsGrowth', None))}</p>
                <p><b>Revenue Growth:</b> {format_percentage(info.get('revenueGrowth', None))}</p>
                <p><b>Gross Margins:</b> {format_percentage(info.get('grossMargins', None))}</p>
                <p><b>Operating Margins:</b> {format_percentage(info.get('operatingMargins', None))}</p>
            """
            
            self.company_info_display.setHtml(company_info_text)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

class Superinvestors(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Input field for stock ticker
        self.stock_input = QtWidgets.QLineEdit(self)
        self.stock_input.setPlaceholderText("Enter Stock Tickers")
        self.stock_input.returnPressed.connect(self.update_link)
        
        # Link to DataRoma
        self.stock_link = QtWidgets.QLabel(self)
        self.stock_link.setText('<a href="https://www.dataroma.com/m/home.php" target="_blank">Visit DataRoma for Superinvestor Activity</a>')
        self.stock_link.setOpenExternalLinks(True)
        
        # Titles for tables
        self.major_holders_title = QtWidgets.QLabel("Major Holders")
        self.institutional_holders_title = QtWidgets.QLabel("Institutional Holders")
        self.mutualfund_holders_title = QtWidgets.QLabel("Mutual Fund Holders")
        self.insider_transactions_title = QtWidgets.QLabel("Insider Transactions")
        self.insider_purchases_title = QtWidgets.QLabel("Insider Purchases")
        
        # Tables for displaying data
        self.major_holders_table = QtWidgets.QTableWidget(self)
        self.institutional_holders_table = QtWidgets.QTableWidget(self)
        self.mutualfund_holders_table = QtWidgets.QTableWidget(self)
        self.insider_transactions_table = QtWidgets.QTableWidget(self)
        self.insider_purchases_table = QtWidgets.QTableWidget(self)
        
        # Layout setup
        layout.addWidget(self.stock_input)
        layout.addWidget(self.stock_link)
        layout.addWidget(self.major_holders_title)
        layout.addWidget(self.major_holders_table)
        layout.addWidget(self.institutional_holders_title)
        layout.addWidget(self.institutional_holders_table)
        layout.addWidget(self.mutualfund_holders_title)
        layout.addWidget(self.mutualfund_holders_table)
        layout.addWidget(self.insider_transactions_title)
        layout.addWidget(self.insider_transactions_table)
        layout.addWidget(self.insider_purchases_title)
        layout.addWidget(self.insider_purchases_table)
        
        self.setLayout(layout)
        self.setWindowTitle("Superinvestors")
        
    def update_link(self):
        ticker = self.stock_input.text()
        if ticker:
            link = f'https://www.dataroma.com/m/stock.php?sym={ticker}'
        else:
            link = 'https://www.dataroma.com/m/home.php'
        
        self.stock_link.setText(f'<a href="{link}" target="_blank">Visit DataRoma for Superinvestor Activity</a>')
        
        self.update_tables()
    
    def update_tables(self):
        self.update_major_holders_table()
        self.update_institutional_holders_table()
        self.update_mutualfund_holders_table()
        self.update_insider_transactions_table()
        self.update_insider_purchases_table()
    
    def update_major_holders_table(self):
        ticker = self.stock_input.text()
        try:
            stock = yf.Ticker(ticker)
            major_holders = stock.major_holders
            if major_holders is not None:
                self.populate_table(self.major_holders_table, major_holders)
        except Exception as e:
            print(f"Failed to fetch major holders for {ticker}: {e}")
            self.major_holders_table.clear()
    
    def update_institutional_holders_table(self):
        ticker = self.stock_input.text()
        try:
            stock = yf.Ticker(ticker)
            institutional_holders = stock.institutional_holders
            if institutional_holders is not None:
                if '% Out' in institutional_holders.columns:
                    institutional_holders['% Out'] = institutional_holders['% Out'].apply(
                        lambda x: '{:.2f}%'.format(x * 100) if pd.notnull(x) else x
                    )
                if 'Date Reported' in institutional_holders.columns:
                    institutional_holders = institutional_holders.drop(columns=['Date Reported'])
                self.populate_table(self.institutional_holders_table, institutional_holders)
        except Exception as e:
            print(f"Failed to fetch institutional holders for {ticker}: {e}")
            self.institutional_holders_table.clear()
    
    def update_mutualfund_holders_table(self):
        ticker = self.stock_input.text()
        try:
            stock = yf.Ticker(ticker)
            mutualfund_holders = stock.mutualfund_holders
            if mutualfund_holders is not None:
                self.populate_table(self.mutualfund_holders_table, mutualfund_holders)
        except Exception as e:
            print(f"Failed to fetch mutual fund holders for {ticker}: {e}")
            self.mutualfund_holders_table.clear()
    
    def update_insider_transactions_table(self):
        ticker = self.stock_input.text()
        try:
            stock = yf.Ticker(ticker)
            insider_transactions = stock.insider_transactions
            if insider_transactions is not None:
                self.populate_table(self.insider_transactions_table, insider_transactions)
        except Exception as e:
            print(f"Failed to fetch insider transactions for {ticker}: {e}")
            self.insider_transactions_table.clear()
    
    def update_insider_purchases_table(self):
        ticker = self.stock_input.text()
        try:
            stock = yf.Ticker(ticker)
            insider_purchases = stock.insider_purchases
            if insider_purchases is not None:
                self.populate_table(self.insider_purchases_table, insider_purchases)
        except Exception as e:
            print(f"Failed to fetch insider purchases for {ticker}: {e}")
            self.insider_purchases_table.clear()
    
    def populate_table(self, table_widget, data):
        if not data.empty:
            table_widget.setColumnCount(len(data.columns))
            table_widget.setRowCount(len(data.index))
            table_widget.setHorizontalHeaderLabels(data.columns)
            table_widget.verticalHeader().setVisible(False)
            for i in range(len(data.index)):
                for j in range(len(data.columns)):
                    table_widget.setItem(i, j, QtWidgets.QTableWidgetItem(str(data.iat[i, j])))
            table_widget.resizeColumnsToContents()
        else:
            table_widget.clear()
            
API_KEY = "Hg9EG5ZmyUaZWLba3uXe2vyAefxx5gDa"

class AnnualFundamentalAnalysis(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Create tab widget
        self.tabs = QtWidgets.QTabWidget()
        
        # Create tabs
        self.income_statement_tab = QtWidgets.QWidget()
        self.balance_sheet_tab = QtWidgets.QWidget()
        self.cash_flow_tab = QtWidgets.QWidget()
        
        # Add tabs to tab widget
        self.tabs.addTab(self.income_statement_tab, "Income Statement")
        self.tabs.addTab(self.balance_sheet_tab, "Balance Sheet")
        self.tabs.addTab(self.cash_flow_tab, "Cash Flow")
        
        # Setup Cash Flow tab layout (with existing content)
        cash_flow_layout = QtWidgets.QVBoxLayout()
        
        # Input field for stock tickers
        self.ticker_input = QtWidgets.QLineEdit(self)
        self.ticker_input.setPlaceholderText("Enter Stock Tickers separated by ','")
        
        # Submit button
        self.submit_button = QtWidgets.QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.update_chart)
        
        # Layout setup
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.ticker_input)
        input_layout.addWidget(self.submit_button)
        
        cash_flow_layout.addLayout(input_layout)
        
        # Plotly chart display
        self.plotly_graph = QWebEngineView(self)
        cash_flow_layout.addWidget(self.plotly_graph)
        
        self.cash_flow_tab.setLayout(cash_flow_layout)
        
        # Add tab widget to main layout
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.setWindowTitle("Annual Fundamental Analysis")
        
    def get_jsonparsed_data(self, url):
        response = requests.get(url, verify=certifi.where())
        data = response.json()
        return data

    def update_chart(self):
        tickers = [ticker.strip() for ticker in self.ticker_input.text().split(',')]
        fig = make_subplots(rows=1, cols=1)

        for ticker in tickers:
            if ticker:
                if self.is_us_stock(ticker):
                    data = self.get_us_stock_data(ticker)
                else:
                    data = self.get_non_us_stock_data(ticker)
                
                if data:
                    years = [item['date'][:4] for item in data][::-1]
                    revenue = [item['revenue'] for item in data][::-1]
                    gross_profit = [item['grossProfit'] for item in data][::-1]
                    ebitda = [item['ebitda'] for item in data][::-1]

                    self.add_trace(fig, ticker, years, revenue, gross_profit, ebitda)
        
        fig.update_layout(
            barmode='group', 
            xaxis_title='Year', 
            yaxis_title='Values in USD', 
            title='Annual Fundamental Analysis',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        self.update_figure(fig)
    
    def add_trace(self, fig, ticker, years, revenue, gross_profit, ebitda):
        fig.add_trace(go.Bar(
            x=years, 
            y=revenue, 
            name=f'{ticker} Revenue',
            text=[self.calculate_yoy(revenue, i) for i in range(len(revenue))],
            textposition='auto'
        ))
        fig.add_trace(go.Bar(
            x=years, 
            y=gross_profit, 
            name=f'{ticker} Gross Profit',
            text=[self.calculate_yoy(gross_profit, i) for i in range(len(gross_profit))],
            textposition='auto'
        ))
        fig.add_trace(go.Bar(
            x=years, 
            y=ebitda, 
            name=f'{ticker} EBITDA',
            text=[self.calculate_yoy(ebitda, i) for i in range(len(ebitda))],
            textposition='auto'
        ))

    def calculate_yoy(self, values, index):
        if index == 0 or values[index - 1] <= 0 or values[index] <= 0:
            return ''
        return f'{((values[index] - values[index - 1]) / values[index - 1]) * 100:.2f}%'

    def update_figure(self, figure):
        self.plotly_graph.setHtml(figure.to_html(include_plotlyjs='cdn'))

    def is_us_stock(self, ticker):
        # If the ticker does not have a period, consider it as a US-listed stock
        return '.' not in ticker

    def get_us_stock_data(self, ticker):
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=annual&apikey={API_KEY}"
        data = self.get_jsonparsed_data(url)
        if data:
            return [{'date': item['date'], 'revenue': item['revenue'], 'grossProfit': item['grossProfit'], 'ebitda': item['ebitda']} for item in data]
        return None

    def get_non_us_stock_data(self, ticker):
        stock = yf.Ticker(ticker)
        financials = stock.financials.T
        if not financials.empty:
            # Handling different column names
            revenue_col = 'Total Revenue' if 'Total Revenue' in financials.columns else 'Revenue'
            gross_profit_col = 'Gross Profit' if 'Gross Profit' in financials.columns else 'Gross Profit'
            ebitda_col = 'Ebitda' if 'Ebitda' in financials.columns else 'EBITDA'
            
            return [{'date': date.strftime('%Y-%m-%d'), 
                     'revenue': financials.loc[date, revenue_col], 
                     'grossProfit': financials.loc[date, gross_profit_col], 
                     'ebitda': financials.loc[date, ebitda_col]} for date in financials.index]
        return None
    
class QuarterlyFundamentalAnalysis(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Quarterly Fundamental Analysis")
        layout = QtWidgets.QVBoxLayout()

        self.ticker_input = QtWidgets.QLineEdit(self)
        self.ticker_input.setPlaceholderText("Enter ticker symbols separated by commas (e.g., MSFT,AAPL,GOOGL)")
        layout.addWidget(self.ticker_input)

        self.plot_button = QtWidgets.QPushButton("Plot Data", self)
        self.plot_button.clicked.connect(self.plot_data)
        layout.addWidget(self.plot_button)

        self.plot_widget = QWebEngineView(self)
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)

    def plot_data(self):
        tickers = self.ticker_input.text().split(',')

        for ticker in tickers:
            ticker = ticker.strip()
            if ticker:
                self.fetch_and_plot_ticker_data(ticker)

    def fetch_and_plot_ticker_data(self, ticker):
        api_key_primary = "W1GUQFLXKU8Z1AQS"
        api_key_secondary = "BQEPPIEOOZNUV8U2"
        
        data = self.fetch_data(ticker, api_key_primary)
        if not data:
            data = self.fetch_data(ticker, api_key_secondary)
        
        if not data:
            print(f"Failed to retrieve data for {ticker} using both API keys.")
            return

        quarterly_reports = data.get("quarterlyReports", [])

        if not quarterly_reports:
            print(f"No data found for {ticker}")
            return

        quarters = []
        revenue = []
        gross_profit = []
        ebitda = []

        for entry in quarterly_reports:
            quarters.append(entry["fiscalDateEnding"])
            revenue.append(self.safe_float(entry["totalRevenue"]))
            gross_profit.append(self.safe_float(entry.get("grossProfit", 0)))
            ebitda.append(self.safe_float(entry.get("ebitda", 0)))

        quarters.reverse()
        revenue.reverse()
        gross_profit.reverse()
        ebitda.reverse()

        revenue_qoq = self.calculate_qoq(revenue)
        revenue_yoy = self.calculate_yoy(revenue)

        gross_profit_qoq = self.calculate_qoq(gross_profit)
        gross_profit_yoy = self.calculate_yoy(gross_profit)

        ebitda_qoq = self.calculate_qoq(ebitda)
        ebitda_yoy = self.calculate_yoy(ebitda)

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            subplot_titles=("Revenue, Gross Profit, and EBITDA", "QoQ Growth/Decline", "YoY Growth/Decline"))

        fig.add_trace(go.Bar(x=quarters, y=revenue, name="Revenue"), row=1, col=1)
        fig.add_trace(go.Bar(x=quarters, y=gross_profit, name="Gross Profit"), row=1, col=1)
        fig.add_trace(go.Bar(x=quarters, y=ebitda, name="EBITDA"), row=1, col=1)

        fig.add_trace(go.Scatter(x=quarters, y=revenue_qoq, mode='lines+markers', name="Revenue QoQ"), row=2, col=1)
        fig.add_trace(go.Scatter(x=quarters, y=gross_profit_qoq, mode='lines+markers', name="Gross Profit QoQ"), row=2, col=1)
        fig.add_trace(go.Scatter(x=quarters, y=ebitda_qoq, mode='lines+markers', name="EBITDA QoQ"), row=2, col=1)

        fig.add_trace(go.Scatter(x=quarters, y=revenue_yoy, mode='lines+markers', name="Revenue YoY"), row=3, col=1)
        fig.add_trace(go.Scatter(x=quarters, y=gross_profit_yoy, mode='lines+markers', name="Gross Profit YoY"), row=3, col=1)
        fig.add_trace(go.Scatter(x=quarters, y=ebitda_yoy, mode='lines+markers', name="EBITDA YoY"), row=3, col=1)

        fig.update_layout(
            title_text=f'Quarterly Financials for {ticker}', 
            height=1200,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        plot_html = fig.to_html(include_plotlyjs='cdn')
                
        self.plot_widget.setHtml(plot_html)

    def fetch_data(self, ticker, api_key):
        url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()

        if "quarterlyReports" in data:
            return data
        return None

    def safe_float(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def calculate_qoq(self, data):
        return [(data[i] - data[i-1]) / data[i-1] * 100 if data[i-1] != 0 else 0 for i in range(len(data))]

    def calculate_yoy(self, data):
        return [(data[i] - data[i-4]) / data[i-4] * 100 if i >= 4 and data[i-4] != 0 else 0 for i in range(len(data))]

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QCheckBox, QDateEdit
from PySide6.QtCore import QDate
from PySide6.QtWebEngineWidgets import QWebEngineView  # Correct import for QWebEngineView

class TechnicalAnalysis(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Technical Analysis")
        self.layout = QVBoxLayout()

        self.ticker_input = QLineEdit(self)
        self.ticker_input.setPlaceholderText("Enter ticker symbols separated by commas")
        self.layout.addWidget(self.ticker_input)

        self.date_picker = QDateEdit(self)
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate(2019, 1, 1))
        self.layout.addWidget(self.date_picker)

        self.checkbox_layout = QHBoxLayout()

        self.sma_200_checkbox = QCheckBox("200-day SMA", self)
        self.sma_200_checkbox.stateChanged.connect(self.plot_stock_data)
        self.checkbox_layout.addWidget(self.sma_200_checkbox)

        self.sma_50_checkbox = QCheckBox("50-day SMA", self)
        self.sma_50_checkbox.stateChanged.connect(self.plot_stock_data)
        self.checkbox_layout.addWidget(self.sma_50_checkbox)

        self.rsi_checkbox = QCheckBox("RSI", self)
        self.rsi_checkbox.stateChanged.connect(self.plot_stock_data)
        self.checkbox_layout.addWidget(self.rsi_checkbox)

        self.volume_checkbox = QCheckBox("Volume", self)
        self.volume_checkbox.stateChanged.connect(self.plot_stock_data)
        self.checkbox_layout.addWidget(self.volume_checkbox)

        self.layout.addLayout(self.checkbox_layout)

        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.plot_stock_data)
        self.layout.addWidget(self.submit_button)

        self.yield_on_cost_date_picker = QDateEdit(self)
        self.yield_on_cost_date_picker.setCalendarPopup(True)
        self.yield_on_cost_date_picker.setDate(QDate.currentDate())
        self.layout.addWidget(self.yield_on_cost_date_picker)

        self.calculate_yield_on_cost_button = QPushButton("Calculate Yield on Cost", self)
        self.calculate_yield_on_cost_button.clicked.connect(self.calculate_yield_on_cost)
        self.layout.addWidget(self.calculate_yield_on_cost_button)

        self.web_view = QWebEngineView(self)
        self.layout.addWidget(self.web_view)

        self.setLayout(self.layout)

    def download_stock_data(self, ticker, start_date):
        try:
            print(f"Downloading data for {ticker} from {start_date}...")
            stock_data = yf.download(ticker, start=start_date)
            if stock_data.empty:
                print(f"No data found for {ticker}")
                return None
            return stock_data
        except Exception as e:
            print(f"Error downloading data for {ticker}: {e}")
            return None

    def download_dividends_data(self, ticker, start_date):
        try:
            print(f"Downloading dividends data for {ticker} from {start_date}...")
            stock_info = yf.Ticker(ticker)
            dividends_data = stock_info.dividends[start_date:]
            if dividends_data.empty:
                print(f"No dividends data found for {ticker}")
                return None
            return dividends_data
        except Exception as e:
            print(f"Error downloading dividends data for {ticker}: {e}")
            return None

    def calculate_sma(self, data, window):
        return data['Close'].rolling(window=window).mean()

    def calculate_rsi(self, data, window=14):
        delta = data['Close'].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate the rolling mean of gains and losses
        avg_gain = gain.rolling(window=window, min_periods=window).mean()
        avg_loss = loss.rolling(window=window, min_periods=window).mean()

        # Calculate the relative strength (RS)
        rs = avg_gain / avg_loss

        # Calculate the RSI
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_dividend_yield(self, stock_data, dividends_data):
        stock_data.index = stock_data.index.tz_localize(None)
        dividends_data.index = dividends_data.index.tz_localize(None)

        quarterly_dividends = dividends_data.resample('Q').sum()
        dividend_yield = pd.Series(index=stock_data.index, dtype='float64')

        start_date = stock_data.index[0] + pd.DateOffset(years=1)
        stock_data = stock_data[start_date:]

        for i in range(len(stock_data)):
            date = stock_data.index[i]
            dividends_sum = quarterly_dividends[quarterly_dividends.index <= date].iloc[-4:].sum()
            if stock_data['Close'][i] != 0:
                dividend_yield[i + len(dividend_yield) - len(stock_data)] = (dividends_sum / stock_data['Close'][i]) * 100
            else:
                dividend_yield[i + len(dividend_yield) - len(stock_data)] = 0

        return dividend_yield

    def calculate_yoy_dividend_change(self, dividends_data):
        yearly_dividends = dividends_data.resample('Y').sum()
        yoy_change = yearly_dividends.pct_change() * 100
        return yoy_change

    def calculate_yield_on_cost(self):
        tickers = [ticker.strip() for ticker in self.ticker_input.text().split(',') if ticker.strip()]
        calculation_date = self.yield_on_cost_date_picker.date().toString("yyyy-MM-dd")
        
        yield_on_cost_data = []

        for ticker in tickers:
            stock_data = self.download_stock_data(ticker, calculation_date)
            dividends_data = self.download_dividends_data(ticker, calculation_date)

            if stock_data is not None and dividends_data is not None:
                try:
                    close_price_on_date = stock_data.loc[calculation_date]['Close']
                    recent_dividend = dividends_data[-1] * 4  # Annualize the most recent dividend
                    yield_on_cost = (recent_dividend / close_price_on_date) * 100
                    yield_on_cost_data.append([ticker, calculation_date, close_price_on_date, recent_dividend, yield_on_cost])
                except Exception as e:
                    print(f"Error calculating yield on cost for {ticker}: {e}")

        # Create Plotly table
        table_fig = go.Figure(data=[go.Table(
            header=dict(values=['Ticker', 'Date', 'Close Price', 'Annualized Dividend', 'Dividend Yield on Cost (%)'],
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[list(row) for row in zip(*yield_on_cost_data)],
                       fill_color='lavender',
                       align='left'))
        ])

        table_fig.update_layout(
            title="Dividend Yield on Cost",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        table_plot_div = plot(table_fig, output_type='div', include_plotlyjs=False)
        
        complete_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            {table_plot_div}
        </body>
        </html>
        """

        self.web_view.setHtml(complete_html)

    def plot_stock_data(self):
        tickers = [ticker.strip() for ticker in self.ticker_input.text().split(',') if ticker.strip()]
        start_date = self.date_picker.date().toString("yyyy-MM-dd")
        stock_data_list = []
        dividends_data_list = []

        for ticker in tickers:
            stock_data = self.download_stock_data(ticker, start_date)
            dividends_data = self.download_dividends_data(ticker, start_date)
            if stock_data is not None:
                stock_data_list.append((ticker, stock_data))
            if dividends_data is not None:
                dividends_data_list.append((ticker, dividends_data))

        if not stock_data_list:
            print("No data to display in the chart.")
            return

        stock_fig = go.Figure()
        volume_fig = go.Figure()
        rsi_fig = go.Figure()

        if len(stock_data_list) == 1:
            ticker, stock_data = stock_data_list[0]
            stock_fig.add_trace(go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name=ticker
            ))
        else:
            for ticker, stock_data in stock_data_list:
                stock_fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data['Close'],
                    mode='lines',
                    name=ticker
                ))

        if self.volume_checkbox.isChecked():
            for ticker, stock_data in stock_data_list:
                volume_fig.add_trace(go.Bar(
                    x=stock_data.index,
                    y=stock_data['Volume'],
                    name=ticker
                ))

        for ticker, stock_data in stock_data_list:
            if self.sma_200_checkbox.isChecked():
                sma_200 = self.calculate_sma(stock_data, 200)
                stock_fig.add_trace(go.Scatter(
                    x=sma_200.index,
                    y=sma_200,
                    mode='lines',
                    name=f"{ticker} 200-day SMA"
                ))

            if self.sma_50_checkbox.isChecked():
                sma_50 = self.calculate_sma(stock_data, 50)
                stock_fig.add_trace(go.Scatter(
                    x=sma_50.index,
                    y=sma_50,
                    mode='lines',
                    name=f"{ticker} 50-day SMA"
                ))

            if self.rsi_checkbox.isChecked():
                rsi = self.calculate_rsi(stock_data)
                rsi_fig.add_trace(go.Scatter(
                    x=rsi.index,
                    y=rsi,
                    mode='lines',
                    name=f"{ticker} RSI"
                ))

        stock_fig.update_layout(
            title="Stock Prices",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        volume_fig.update_layout(
            title="Volume",
            xaxis_title="Date",
            yaxis_title="Volume",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        rsi_fig.update_layout(
            title="Relative Strength Index (RSI)",
            xaxis_title="Date",
            yaxis_title="RSI",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        dividends_fig = go.Figure()
        yearly_dividends_fig = go.Figure()
        yield_fig = go.Figure()
        yoy_dividends_fig = go.Figure()

        for ticker, dividends_data in dividends_data_list:
            quarterly_dividends = dividends_data.resample('Q').sum()
            dividends_fig.add_trace(go.Bar(
                x=quarterly_dividends.index,
                y=quarterly_dividends.values,
                name=ticker
            ))
            yearly_dividends = dividends_data.resample('Y').sum()
            yearly_dividends_fig.add_trace(go.Bar(
                x=yearly_dividends.index,
                y=yearly_dividends.values,
                name=ticker
            ))

            yoy_dividend_change = self.calculate_yoy_dividend_change(dividends_data)
            yoy_dividend_change = yoy_dividend_change[:-1]
            yoy_dividends_fig.add_trace(go.Scatter(
                x=yoy_dividend_change.index,
                y=yoy_dividend_change,
                mode='lines+markers',
                name=ticker
            ))

            if not yoy_dividend_change.empty:
                next_year = yoy_dividend_change.index[-1] + pd.DateOffset(years=1)
                yoy_dividends_fig.add_trace(go.Scatter(
                    x=[next_year],
                    y=[None],
                    mode='lines+markers',
                    showlegend=False
                ))

            dividend_yield = self.calculate_dividend_yield(stock_data, dividends_data)
            yield_fig.add_trace(go.Scatter(
                x=dividend_yield.index,
                y=dividend_yield,
                mode='lines',
                name=f"{ticker} Dividend Yield"
            ))

        dividends_fig.update_layout(
            title="Quarterly Dividends",
            xaxis_title="Date",
            yaxis_title="Dividends",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        yearly_dividends_fig.update_layout(
            title="Yearly Dividends",
            xaxis_title="Date",
            yaxis_title="Dividends",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        yoy_dividends_fig.update_layout(
            title="Year-over-Year Change in Dividends",
            xaxis_title="Date",
            yaxis_title="YoY Change (%)",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        yield_fig.update_layout(
            title="Dividend Yield",
            xaxis_title="Date",
            yaxis_title="Dividend Yield (%)",
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        stock_plot_div = plot(stock_fig, output_type='div', include_plotlyjs=False)
        volume_plot_div = plot(volume_fig, output_type='div', include_plotlyjs=False) if self.volume_checkbox.isChecked() else ""
        rsi_plot_div = plot(rsi_fig, output_type='div', include_plotlyjs=False) if self.rsi_checkbox.isChecked() else ""
        dividends_plot_div = plot(dividends_fig, output_type='div', include_plotlyjs=False)
        yearly_dividends_plot_div = plot(yearly_dividends_fig, output_type='div', include_plotlyjs=False)
        yoy_dividends_plot_div = plot(yoy_dividends_fig, output_type='div', include_plotlyjs=False)
        yield_plot_div = plot(yield_fig, output_type='div', include_plotlyjs=False)

        complete_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            {stock_plot_div}
            <br>
            {volume_plot_div}
            <br>
            {rsi_plot_div}
            <br>
            {dividends_plot_div}
            <br>
            {yearly_dividends_plot_div}
            <br>
            {yoy_dividends_plot_div}
            <br>
            {yield_plot_div}
        </body>
        </html>
        """

        self.web_view.setHtml(complete_html)
