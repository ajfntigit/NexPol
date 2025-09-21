import json
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QProgressBar,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QFileDialog, QGroupBox, QFormLayout, QSpinBox, QSplitter, QInputDialog, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import self

# Importar sua classe existente
from main import RedditDataProcessor  # Assumindo que seu arquivo se chama reddit_analyzer.py

class AnalysisThread(QThread):
    """Thread para executar a análise em segundo plano"""
    progress_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal(bool, dict, pd.DataFrame)
    error_signal = pyqtSignal(str)
    
    def __init__(self, processor, subreddit, sample_size):
        super().__init__()
        self.processor = processor
        self.subreddit = subreddit
        self.sample_size = sample_size
    
    def run(self):
        try:
            self.progress_signal.emit("Iniciando análise...", 10)
            
            # Processar dados
            success = self.processor.process_data(self.subreddit, self.sample_size)
            
            if success:
                self.progress_signal.emit("Gerando visualizações...", 70)
                self.processor.generate_visualizations("visualizations/")
                
                self.progress_signal.emit("Gerando relatório...", 90)
                report_file = f"report_{self.subreddit}.txt"
                self.processor.generate_report(report_file)
                
                self.progress_signal.emit("Análise concluída!", 100)
                self.finished_signal.emit(True, self.processor.stats, self.processor.processed_data)
            else:
                self.error_signal.emit("Falha no processamento dos dados")
                
        except Exception as e:
            self.error_signal.emit(f"Erro durante a análise: {str(e)}")

class MplCanvas(FigureCanvas):
    """Widget para exibir gráficos matplotlib"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

class WelcomeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        from PyQt5.QtWidgets import QSizePolicy
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setAlignment(Qt.AlignCenter)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        label = QLabel('Bem-vindo ao NexPol')
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont('Arial', 14, QFont.Bold))
        label.setStyleSheet('color: #1976D2; background: transparent;')
        overlay_layout.addStretch(1)
        overlay_layout.addWidget(label, alignment=Qt.AlignCenter)
        overlay_layout.addStretch(1)
        self.setMinimumSize(400, 120)
        self.resize(400, 120)
        self.center_on_parent()
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            x = parent_geom.x() + (parent_geom.width() - self.width()) // 2
            y = parent_geom.y() + (parent_geom.height() - self.height()) // 2
            self.move(x, y)

class AuthWindow(QDialog):
    def load_users(self):
        users_file = os.path.join(os.path.dirname(__file__), 'users.json')
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except Exception:
                    return {}
        return {}
    def show_register(self):
        self.clear()
        self.show_logo()
        label = QLabel('Cadastro')
        label.setFont(QFont('Arial', 16, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)
        self.user = QLineEdit()
        self.user.setPlaceholderText('nome.sobrenome')
        self.layout.addWidget(self.user)
        self.pwd = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.Password)
        self.pwd.setPlaceholderText('senha')
        self.layout.addWidget(self.pwd)
        btn_reg = QPushButton('Registrar')
        btn_reg.clicked.connect(self.register)
        self.layout.addWidget(btn_reg)
        btn_back = QPushButton('Voltar')
        btn_back.clicked.connect(self.show_login)
        self.layout.addWidget(btn_back)
    def login(self):
        user = self.user.text()
        pwd = self.pwd.text()
        users = self.load_users()
        if user in users and users[user]['password'] == pwd:
            self.accepted = True
            self.close()
        else:
            QMessageBox.critical(self, 'Erro', 'Usuário ou senha inválidos')
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Acesso NEXPOL')
        self.setFixedSize(340, 420)
        self.layout = QVBoxLayout(self)
        self.show_login()

    def clear(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget: widget.setParent(None)

    def show_logo(self):
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.jpg')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaledToWidth(180, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            logo_label.setText('NEXPOL')
            logo_label.setFont(QFont('Arial', 24, QFont.Bold))
            logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(logo_label)

    def show_login(self):
        self.clear()
        self.show_logo()
        label = QLabel('Login')
        label.setFont(QFont('Arial', 16, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)
        self.user = QLineEdit()
        self.user.setPlaceholderText('nome.sobrenome')
        self.layout.addWidget(self.user)
        self.pwd = QLineEdit()
        self.pwd.setEchoMode(QLineEdit.Password)
        self.pwd.setPlaceholderText('senha')
        self.layout.addWidget(self.pwd)
        btn_login = QPushButton('Entrar')
        btn_login.clicked.connect(self.login)
        self.layout.addWidget(btn_login)
        btn_reg = QPushButton('Cadastrar')
        btn_reg.clicked.connect(self.show_register)
        self.layout.addWidget(btn_reg)

    def register(self):
        user, pwd = self.user.text(), self.pwd.text()
        if '.' not in user or not pwd:
            QMessageBox.critical(self, 'Erro', 'Formato: nome.sobrenome e senha obrigatória')
            return
        users = self.load_users()
        if user in users:
            QMessageBox.critical(self, 'Erro', 'Usuário já existe')
            return
        users[user] = {'password': pwd}
        self.save_users(users)
        QMessageBox.information(self, 'Sucesso', 'Cadastro realizado!')
        self.show_login()

    def recover(self):
        user, ok = QInputDialog.getText(self, 'Recuperar', 'Digite nome.sobrenome:')
        if not ok: return
        users = self.load_users()
        if user in users:
            QMessageBox.information(self, 'Recuperação', f'Sua senha: {users[user]["password"]}')
        else:
            QMessageBox.critical(self, 'Erro', 'Usuário não encontrado')
    def save_users(self, users):
        users_file = os.path.join(os.path.dirname(__file__), 'users.json')
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

class RedditAnalyzerGUI(QMainWindow):
    def display_results(self):
        # Atualiza a aba de estatísticas e a tabela de dados com os resultados atuais
        # Atualiza o label de polarização
        if self.current_stats:
            score = self.current_stats.get('polarization_score', None)
            if score is not None:
                self.polarization_label.setText(f"Polarização: {score:.4f}")
            else:
                self.polarization_label.setText("Polarização: N/A")
        else:
            self.polarization_label.setText("Polarização: N/A")

        # Preenche a aba de estatísticas
        if hasattr(self, 'stats_widget'):
            # Limpa o layout anterior
            layout = self.stats_widget.layout()
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
            if self.current_stats:
                stats_text = (
                    f"<b>Subreddit:</b> {self.current_stats.get('subreddit', '')}<br>"
                    f"<b>Total de posts:</b> {self.current_stats.get('total_posts', '')}<br>"
                    f"<b>Média de score:</b> {self.current_stats.get('avg_score', ''):.2f}<br>"
                    f"<b>Média de comentários:</b> {self.current_stats.get('avg_comments', ''):.2f}<br>"
                    f"<b>Média de sentimento:</b> {self.current_stats.get('avg_sentiment', ''):.4f}<br>"
                    f"<b>Posts positivos:</b> {self.current_stats.get('positive_posts', '')}<br>"
                    f"<b>Posts negativos:</b> {self.current_stats.get('negative_posts', '')}<br>"
                    f"<b>Posts neutros:</b> {self.current_stats.get('neutral_posts', '')}<br>"
                )
                label = QLabel(stats_text)
                label.setTextFormat(Qt.RichText)
                layout.addWidget(label)
            else:
                layout.addWidget(QLabel("Nenhuma estatística disponível."))

        # Preenche a tabela de dados apenas com as colunas desejadas e traduzidas
        columns_to_show = ['id', 'title', 'author', 'score', 'created_utc', 'sentiment', 'sentimento']
        if hasattr(self, 'data_table') and self.current_data is not None and not self.current_data.empty:
            df = self.current_data.copy()
            idioma = self.language_combo.currentText() if hasattr(self, 'language_combo') else 'Português'
            t = self.get_translations()[idioma]
            # Adiciona coluna 'sentimento' textual baseada em 'sentiment_compound' se existir
            if 'sentiment_compound' in df.columns:
                def sentimento_label(val, t=t):
                    if val > 0.05:
                        return t.get('positive', 'Positivo')
                    elif val < -0.05:
                        return t.get('negative', 'Negativo')
                    else:
                        return t.get('neutral', 'Neutro')
                df['sentimento'] = df['sentiment_compound'].apply(sentimento_label)
            df = df[[col for col in columns_to_show if col in df.columns]]
            self.data_table.setRowCount(len(df))
            self.data_table.setColumnCount(len(df.columns))
            header_map = {
                'id': t.get('id', 'id'),
                'title': t.get('title', 'title'),
                'author': t.get('author', 'author'),
                'score': t.get('score', 'score'),
                'created_utc': t.get('created_utc', 'created_utc'),
                'sentiment': t.get('sentiment', 'sentiment'),
                'sentimento': t.get('sentimento', 'Sentimento')
            }
            headers = [header_map.get(col, col) for col in df.columns]
            self.data_table.setHorizontalHeaderLabels(headers)
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    self.data_table.setItem(i, j, QTableWidgetItem(str(value)))
        else:
            if hasattr(self, 'data_table'):
                self.data_table.setRowCount(0)
                self.data_table.setColumnCount(0)
        # Atualiza o gráfico
        if hasattr(self, 'graph_canvas'):
            self.display_graph()
    def clear_all(self):
        """Limpa todos os campos, estatísticas, dados e gráficos da interface, resetando a visualização."""
        self.subreddit_input.clear()
        self.update_graph_section_visibility()
        self.current_stats = None
        self.current_data = pd.DataFrame()
        self.stats_text.setPlainText("Bem-vindo ao NEXPOL!\n\nClique em 'Iniciar Análise' ou aguarde a análise automática do subreddit padrão.")
        self.polarization_label.setText("")
        self.data_table.setRowCount(0)
        self.graph_canvas.axes.clear()
        self.graph_canvas.draw()
        self.export_btn.setEnabled(False)
    def get_translations(self):
        return {
            'Português': {
                'polarization': 'Polarização',
                'config_section': 'Configuração de Análise',
                'subreddit': 'Subreddit',
                'sample_size': 'Tamanho da Amostra',
                'analyze': 'Iniciar Análise',
                'clear': 'Limpar',
                'export': 'Exportar Dados',
                'statistics': 'Estatísticas',
                'data_table': 'Dados',
                'language': 'Idioma da Interface',
                'status_ready': 'Pronto para analisar',
                'status_done': 'Análise concluída!',
                'status_fail': 'Falha na análise.',
                'no_posts': 'Nenhum post encontrado no idioma selecionado.',
                'comments': 'Comentários',
                'sentiment': 'Sentimento',
                'date': 'Data',
                'title': 'Título',
                'author': 'Autor',
                'score': 'Score'
            },
            'Inglês': {
                'polarization': 'Polarization',
                'config_section': 'Analysis Configuration',
                'subreddit': 'Subreddit',
                'sample_size': 'Sample Size',
                'analyze': 'Start Analysis',
                'clear': 'Clear',
                'export': 'Export Data',
                'statistics': 'Statistics',
                'data_table': 'Data',
                'language': 'Interface Language',
                'status_ready': 'Ready for analysis',
                'status_done': 'Analysis completed!',
                'status_fail': 'Analysis failed.',
                'no_posts': 'No posts found in the selected language.',
                'comments': 'Comments',
                'sentiment': 'Sentiment',
                'date': 'Date',
                'title': 'Title',
                'author': 'Author',
                'score': 'Score'
            },
            'Espanhol': {
                'polarization': 'Polarización',
                'config_section': 'Configuración de Análisis',
                'subreddit': 'Subreddit',
                'sample_size': 'Tamaño de Muestra',
                'analyze': 'Iniciar Análisis',
                'clear': 'Limpiar',
                'export': 'Exportar Datos',
                'statistics': 'Estadísticas',
                'data_table': 'Datos',
                'language': 'Idioma de la Interfaz',
                'status_ready': 'Listo para analizar',
                'status_done': '¡Análisis completado!',
                'status_fail': 'Error en el análisis.',
                'no_posts': 'No se encontraron publicaciones en el idioma seleccionado.',
                'comments': 'Comentarios',
                'sentiment': 'Sentimiento',
                'date': 'Fecha',
                'title': 'Título',
                'author': 'Autor',
                'score': 'Score'
            }
        }

    def update_interface_language(self):
        idioma = self.language_combo.currentText()
        t = self.get_translations()[idioma]
        self.polarization_label.setText(t['polarization'])
        self.config_group.setTitle(t['config_section'])
        self.subreddit_label.setText(t['subreddit'])
        self.sample_size_label.setText(t['sample_size'])
        self.analyze_btn.setText(t['analyze'])
        self.clear_btn.setText(t['clear'])
        self.export_btn.setText(t['export'])
        # Atualizar títulos das abas
        self.tabs.setTabText(0, t['statistics'])
        self.tabs.setTabText(1, t['data_table'])
        self.language_label.setText(t['language'])
        self.statusBar().showMessage(t['status_ready'])
        # Atualizar headers da tabela se necessário
        columns_to_show = ['id', 'title', 'author', 'score', 'created_utc', 'sentiment', 'sentimento']
        if self.data_table.columnCount() > 0:
            idioma = self.language_combo.currentText() if hasattr(self, 'language_combo') else 'Português'
            t = self.get_translations()[idioma]
            header_map = {
                'id': t.get('id', 'id'),
                'title': t.get('title', 'title'),
                'author': t.get('author', 'author'),
                'score': t.get('score', 'score'),
                'created_utc': t.get('created_utc', 'created_utc'),
                'sentiment': t.get('sentiment', 'sentiment'),
                'sentimento': t.get('sentimento', 'Sentimento')
            }
            headers = [header_map.get(col, col) for col in columns_to_show if col in self.current_data.columns]
            self.data_table.setHorizontalHeaderLabels(headers)

    def update_graph_section_visibility(self):
        # Exibe a seção de gráfico apenas se o campo subreddit não estiver vazio
        if hasattr(self, 'graph_type_group'):
            visible = bool(self.subreddit_input.text().strip())
            self.graph_type_group.setVisible(visible)

    def __init__(self):
        super().__init__()
        self.processor = RedditDataProcessor()
        self.current_stats = None
        self.current_data = pd.DataFrame()
        self.initUI()
        # Executar análise padrão automática ao abrir a tela principal
        self.subreddit_input.setText("politics")
        self.start_analysis()

    def start_analysis(self):
        subreddit = self.subreddit_input.text().strip()
        sample_size = self.sample_size_spin.value()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        # Obter idioma selecionado
        idioma = self.language_combo.currentText()
        lang_map = {"Português": "pt", "Inglês": "en", "Espanhol": "es"}
        lang_code = lang_map.get(idioma, "en")

        # Thread para buscar/processar dados normalmente
        self.analysis_thread = AnalysisThread(self.processor, subreddit, sample_size)
        self.analysis_thread.progress_signal.connect(self.update_progress)
        self.analysis_thread.finished_signal.connect(lambda success, stats, data: self.analysis_finished_with_lang(success, stats, data, lang_code))
        self.analysis_thread.error_signal.connect(self.analysis_error)
        self.analysis_thread.start()

    def analysis_finished_with_lang(self, success, stats, data, lang_code):
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        if success:
            # Filtrar DataFrame pelo idioma, se possível
            if 'lang' in data.columns:
                filtered_data = data[data['lang'] == lang_code]
                if filtered_data.empty:
                    QMessageBox.warning(self, "Aviso", "Nenhum post encontrado no idioma selecionado.")
                    self.current_stats = None
                    self.current_data = pd.DataFrame()
                    self.export_btn.setEnabled(False)
                    self.display_results()
                    return
                self.current_data = filtered_data
                # Atualizar stats para refletir apenas os dados filtrados
                self.current_stats = stats.copy()
                self.current_stats['total_posts'] = len(filtered_data)
                self.current_stats['avg_score'] = filtered_data['score'].mean()
                self.current_stats['avg_comments'] = filtered_data['num_comments'].mean()
                self.current_stats['avg_sentiment'] = filtered_data['sentiment_compound'].mean()
                self.current_stats['positive_posts'] = len(filtered_data[filtered_data['sentiment_compound'] > 0.05])
                self.current_stats['negative_posts'] = len(filtered_data[filtered_data['sentiment_compound'] < -0.05])
                self.current_stats['neutral_posts'] = len(filtered_data[(filtered_data['sentiment_compound'] >= -0.05) & (filtered_data['sentiment_compound'] <= 0.05)])
            else:
                self.current_stats = stats
                self.current_data = data
            self.export_btn.setEnabled(True)
            self.display_results()
            self.statusBar().showMessage('Análise concluída!')
        else:
            self.statusBar().showMessage('Falha na análise.')

    def update_progress(self, message, value):
        self.statusBar().showMessage(message)
        self.progress_bar.setValue(value)

    def analysis_finished(self, success, stats, data):
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        if success:
            self.current_stats = stats
            self.current_data = data
            self.export_btn.setEnabled(True)
            self.display_results()
            self.statusBar().showMessage('Análise concluída!')
        else:
            self.statusBar().showMessage('Falha na análise.')

    def analysis_error(self, message):
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.statusBar().showMessage(message)

        # Grupo de entrada/configuração de análise


    def initUI(self):
        self.setWindowTitle('NEXPOL - Analisador de Polarização do Reddit')
        self.setGeometry(100, 100, 1200, 800)

        # Widget central e layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ...existing code...
        # Layout do formulário de configuração
        input_layout = QFormLayout()
        subreddit_layout = QHBoxLayout()
        self.subreddit_label = QLabel("Subreddit:")
        self.subreddit_input = QLineEdit("politics")
        self.clear_btn = QPushButton("Limpar")
        self.clear_btn.setToolTip("Limpar campo subreddit")
        self.clear_btn.clicked.connect(self.clear_all)
        subreddit_layout.addWidget(self.subreddit_input)
        subreddit_layout.addWidget(self.clear_btn)
        input_layout.addRow(self.subreddit_label, subreddit_layout)
        self.sample_size_label = QLabel("Tamanho da Amostra:")
        self.sample_size_spin = QSpinBox()
        self.sample_size_spin.setRange(10, 500)
        self.sample_size_spin.setValue(50)
        input_layout.addRow(self.sample_size_label, self.sample_size_spin)
        self.language_label = QLabel("Idioma da Interface:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Português", "Inglês", "Espanhol"])
        self.language_combo.setCurrentIndex(0)
        self.language_combo.currentIndexChanged.connect(self.update_interface_language)
        input_layout.addRow(self.language_label, self.language_combo)
        # Seção de seleção do tipo de gráfico (logo após idioma)
        self.graph_type_group = QGroupBox("Tipo de Gráfico")
        graph_type_layout = QHBoxLayout()
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems([
            "Setores (Pizza)",
            "Colunas",
            "Barras",
            "Áreas"
        ])
        self.graph_type_combo.setCurrentIndex(0)
        self.graph_type_combo.currentIndexChanged.connect(lambda: self.display_graph())
        graph_type_layout.addWidget(QLabel("Escolha o tipo de gráfico:"))
        graph_type_layout.addWidget(self.graph_type_combo)
        self.graph_type_group.setLayout(graph_type_layout)
        self.graph_type_group.setVisible(False)
        input_layout.addRow(self.graph_type_group)

        # --- LOGO ---
        logo_label = QLabel()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, 'logo.jpg')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaledToWidth(180, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            logo_label.setText('NEXPOL')
            logo_label.setFont(QFont('Arial', 24, QFont.Bold))
            logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        # Layout horizontal para polarização e progresso
        top_info_layout = QHBoxLayout()
        # Label de polarização no canto superior esquerdo
        self.polarization_label = QLabel()
        self.polarization_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.polarization_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.polarization_label.setStyleSheet('color: #1976D2; margin-bottom: 10px;')
        top_info_layout.addWidget(self.polarization_label, alignment=Qt.AlignLeft)
        # Barra de progresso à direita
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        top_info_layout.addWidget(self.progress_bar, alignment=Qt.AlignRight)
        main_layout.addLayout(top_info_layout)

        # Grupo de entrada/configuração de análise acima das abas
        self.config_group = QGroupBox("Configuração da Análise")
        input_layout = QFormLayout()
        subreddit_layout = QHBoxLayout()
        self.subreddit_label = QLabel("Subreddit:")
        self.subreddit_input = QLineEdit("politics")
        self.clear_btn = QPushButton("Limpar")
        self.clear_btn.setToolTip("Limpar campo subreddit")
        self.clear_btn.clicked.connect(self.clear_all)
        subreddit_layout.addWidget(self.subreddit_input)
        subreddit_layout.addWidget(self.clear_btn)
        input_layout.addRow(self.subreddit_label, subreddit_layout)
        self.sample_size_label = QLabel("Tamanho da Amostra:")
        self.sample_size_spin = QSpinBox()
        self.sample_size_spin.setRange(10, 500)
        self.sample_size_spin.setValue(50)
        input_layout.addRow(self.sample_size_label, self.sample_size_spin)
        self.language_label = QLabel("Idioma da Interface:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Português", "Inglês", "Espanhol"])
        self.language_combo.setCurrentIndex(0)
        self.language_combo.currentIndexChanged.connect(self.update_interface_language)
        input_layout.addRow(self.language_label, self.language_combo)
        self.config_group.setLayout(input_layout)
        main_layout.addWidget(self.config_group)
        main_layout.addWidget(self.graph_type_group)

        # Botão de análise
        self.analyze_btn = QPushButton("Iniciar Análise")
        self.analyze_btn.clicked.connect(self.start_analysis)
        # Botão de exportação
        self.export_btn = QPushButton("Exportar Dados")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        # Layout para botões
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addWidget(self.export_btn)
        main_layout.addLayout(btn_layout)

        # Abas de resultados, tabela de dados e gráfico
        self.tabs = QTabWidget()
        # Aba de estatísticas
        self.stats_widget = QWidget()
        stats_layout = QVBoxLayout(self.stats_widget)
        self.tabs.addTab(self.stats_widget, "Estatísticas")
        # Aba de tabela de dados
        self.data_table = QTableWidget()
        self.tabs.addTab(self.data_table, "Dados")
        # Aba de gráfico
        self.graph_widget = QWidget()
        graph_layout = QVBoxLayout(self.graph_widget)
        self.graph_canvas = MplCanvas(self, width=6, height=4, dpi=100)
        graph_layout.addWidget(self.graph_canvas)
        self.tabs.addTab(self.graph_widget, "Gráfico")
        main_layout.addWidget(self.tabs)

        # Só agora todos os widgets existem
        self.update_interface_language()
        self.subreddit_input.textChanged.connect(lambda: self.update_graph_section_visibility())
        self.update_graph_section_visibility()
    
    def display_graph(self):
        # Limpar gráfico anterior
        self.graph_canvas.axes.clear()

        if self.current_data.empty:
            self.graph_canvas.draw()
            return

        sentiment_counts = [
            self.current_stats['positive_posts'],
            self.current_stats['neutral_posts'],
            self.current_stats['negative_posts']
        ]
        labels = ['Positivo', 'Neutro', 'Negativo']
        colors = ['#4CAF50', '#FFC107', '#F44336']

        graph_type = self.graph_type_combo.currentText() if hasattr(self, 'graph_type_combo') else 'Setores (Pizza)'

        if graph_type == 'Setores (Pizza)':
            self.graph_canvas.axes.pie(sentiment_counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            self.graph_canvas.axes.set_title(f'Distribuição de Sentimentos - r/{self.current_stats["subreddit"]}')
        elif graph_type == 'Colunas':
            self.graph_canvas.axes.bar(labels, sentiment_counts, color=colors)
            self.graph_canvas.axes.set_ylabel('Quantidade')
            self.graph_canvas.axes.set_title(f'Distribuição de Sentimentos (Colunas) - r/{self.current_stats["subreddit"]}')
        elif graph_type == 'Barras':
            self.graph_canvas.axes.barh(labels, sentiment_counts, color=colors)
            self.graph_canvas.axes.set_xlabel('Quantidade')
            self.graph_canvas.axes.set_title(f'Distribuição de Sentimentos (Barras) - r/{self.current_stats["subreddit"]}')
        elif graph_type == 'Linhas':
            self.graph_canvas.axes.plot(labels, sentiment_counts, marker='o', color='#1976D2')
            self.graph_canvas.axes.set_ylabel('Quantidade')
            self.graph_canvas.axes.set_title(f'Distribuição de Sentimentos (Linhas) - r/{self.current_stats["subreddit"]}')
        elif graph_type == 'Áreas':
            self.graph_canvas.axes.fill_between(labels, sentiment_counts, color='#1976D2', alpha=0.5)
            self.graph_canvas.axes.set_ylabel('Quantidade')
            self.graph_canvas.axes.set_title(f'Distribuição de Sentimentos (Áreas) - r/{self.current_stats["subreddit"]}')
        elif graph_type == 'Histograma':
            # Histograma dos scores de sentimento
            if 'sentiment_compound' in self.current_data:
                self.graph_canvas.axes.hist(self.current_data['sentiment_compound'], bins=20, color='#1976D2', alpha=0.7)
                self.graph_canvas.axes.set_xlabel('Score de Sentimento')
                self.graph_canvas.axes.set_ylabel('Frequência')
                self.graph_canvas.axes.set_title(f'Histograma dos Scores de Sentimento - r/{self.current_stats["subreddit"]}')
            else:
                self.graph_canvas.axes.text(0.5, 0.5, 'Sem dados para histograma', ha='center')

        self.graph_canvas.draw()
    
    def export_data(self):
        if self.current_data.empty:
            QMessageBox.warning(self, "Erro", "Nenhum dado para exportar")
            return
        
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Dados", "reddit_analysis.csv", 
            "CSV Files (*.csv);;Excel Files (*.xlsx)", options=options
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.current_data.to_csv(file_path, index=False, encoding='utf-8')
                else:
                    self.current_data.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Sucesso", f"Dados exportados para: {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar dados: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # --- Autenticação ---
    auth = AuthWindow()
    auth.accepted = False
    if auth.exec_() == QDialog.Accepted or getattr(auth, 'accepted', False):
        window = RedditAnalyzerGUI()
        window.subreddit_input.clear()
        window.sample_size_spin.setValue(10)
        window.language_combo.setCurrentIndex(0)
        window.update_graph_section_visibility()
        window.current_stats = None
        window.current_data = pd.DataFrame()
        window.polarization_label.setText("")
        window.data_table.setRowCount(0)
        window.graph_canvas.axes.clear()
        window.graph_canvas.draw()
        window.export_btn.setEnabled(False)
        window.show()
        overlay = WelcomeOverlay(window)
        overlay.show()
        QTimer.singleShot(2000, overlay.close)
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == '__main__':
    main()
