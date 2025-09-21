import pandas as pd
import numpy as np
import praw # Importa a biblioteca praw
import json
import re
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import logging
from typing import List, Dict, Any, Optional
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download de recursos do NLTK (executar apenas na primeira vez)
try:
    nltk.download('vader_lexicon', quiet=True)
except:
    logger.warning("Não foi possível baixar recursos do NLTK")

# Use as chaves da API que você obteve
# A autenticação com o PRAW deve ser feita uma única vez no escopo global
try:
    # CLIENT_ID e CLIENT_SECRET foram atualizados com base no seu último envio
    reddit = praw.Reddit(
        client_id="cPcl1c0DgWZUXBekpmPAxw",
        client_secret="ptfKKHYBe9n5DQRyPPy2AGMmXWrj1g",
        user_agent="nexpol"
    )
    logger.info("Conexão com a API do Reddit estabelecida com sucesso usando PRAW.")
except Exception as e:
    logger.error(f"Erro na conexão com a API do Reddit: {e}")
    reddit = None

class RedditDataProcessor:
    """Classe para processamento de dados do Reddit"""
    
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.processed_data = pd.DataFrame()
        
    def fetch_reddit_data(self, subreddit: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Busca dados do Reddit usando a biblioteca PRAW para autenticação
        """
        if not reddit:
            logger.error("Objeto Reddit não inicializado. Não é possível buscar dados.")
            return None
        
        try:
            logger.info(f"Buscando posts de r/{subreddit}...")
            processed_posts = []
            
            # Pega os posts quentes do subreddit
            for submission in reddit.subreddit(subreddit).hot(limit=limit):
                processed_posts.append({
                    'id': submission.id,
                    'title': submission.title,
                    'author': submission.author.name if submission.author else '[deleted]',
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'created_utc': datetime.fromtimestamp(submission.created_utc),
                    'url': submission.url,
                    'selftext': submission.selftext if submission.selftext else '',
                    'subreddit': submission.subreddit.display_name
                })
            
            return pd.DataFrame(processed_posts)
            
        except Exception as e:
            logger.error(f"Erro ao buscar posts de r/{subreddit}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Limpa e pré-processa texto"""
        if not isinstance(text, str):
            return ""
        
        # Remove URLs, caracteres especiais e normaliza texto
        text = re.sub(r'http\S+', '', text)  # Remove URLs
        text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', text)  # Remove caracteres especiais
        text = text.lower().strip()  # Lowercase e remove espaços extras
        return text
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analisa sentimento do texto usando VADER"""
        try:
            cleaned_text = self.clean_text(text)
            if not cleaned_text or len(cleaned_text.split()) < 3:
                return {'compound': 0, 'pos': 0, 'neg': 0, 'neu': 0}
            
            scores = self.sia.polarity_scores(cleaned_text)
            return scores
            
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            return {'compound': 0, 'pos': 0, 'neg': 0, 'neu': 0}
    
    def calculate_polarization_score(self, sentiment_scores: List[Dict]) -> float:
        """Calcula score de polarização baseado na variância dos sentimentos"""
        try:
            compounds = [score['compound'] for score in sentiment_scores]
            if not compounds:
                return 0
            
            polarization = np.var(compounds)  # Variância como medida de polarização
            return float(polarization)
            
        except Exception as e:
            logger.error(f"Erro no cálculo de polarização: {e}")
            return 0
    
    def process_data(self, subreddit: str, sample_size: int = 50) -> bool:
        """Processa dados do Reddit e calcula métricas de polarização"""
        try:
            logger.info(f"Iniciando processamento para r/{subreddit}")
            
            # Buscar dados
            df = self.fetch_reddit_data(subreddit, sample_size)
            if df is None or df.empty:
                logger.warning("Nenhum dado encontrado ou erro na busca")
                return False
            
            # Análise de sentimento
            logger.info("Realizando análise de sentimento...")
            df['sentiment_scores'] = df['title'].apply(
                lambda x: self.analyze_sentiment(str(x))
            )
            
            # Extrair métricas de sentimento
            df['sentiment_compound'] = df['sentiment_scores'].apply(lambda x: x['compound'])
            df['sentiment_positive'] = df['sentiment_scores'].apply(lambda x: x['pos'])
            df['sentiment_negative'] = df['sentiment_scores'].apply(lambda x: x['neg'])
            df['sentiment_neutral'] = df['sentiment_scores'].apply(lambda x: x['neu'])
            
            # Calcular polarização geral
            polarization_score = self.calculate_polarization_score(df['sentiment_scores'].tolist())
            logger.info(f"Score de polarização: {polarization_score:.4f}")
            
            # Classificar polarização
            if polarization_score > 0.1:
                polarization_level = "Alta"
            elif polarization_score > 0.05:
                polarization_level = "Média"
            else:
                polarization_level = "Baixa"
            
            # Estatísticas básicas
            stats = {
                'subreddit': subreddit,
                'total_posts': len(df),
                'avg_score': df['score'].mean(),
                'avg_comments': df['num_comments'].mean(),
                'polarization_score': polarization_score,
                'polarization_level': polarization_level,
                'avg_sentiment': df['sentiment_compound'].mean(),
                'positive_posts': len(df[df['sentiment_compound'] > 0.05]),
                'negative_posts': len(df[df['sentiment_compound'] < -0.05]),
                'neutral_posts': len(df[(df['sentiment_compound'] >= -0.05) & (df['sentiment_compound'] <= 0.05)])
            }
            
            self.processed_data = df
            self.stats = stats
            
            logger.info("Processamento concluído com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            return False
    
    def generate_visualizations(self, output_path: str = "visualizations/"):
        """Gera visualizações dos dados processados"""
        try:
            if self.processed_data.empty:
                logger.warning("Nenhum dado processado para visualização")
                return False
            
            # Configurar estilo dos gráficos
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # Garante que o diretório de saída existe
            import os
            os.makedirs(output_path, exist_ok=True)
            
            # Gráfico 1: Distribuição de sentimentos
            plt.figure(figsize=(10, 6))
            sentiment_counts = [
                self.stats['positive_posts'],
                self.stats['neutral_posts'], 
                self.stats['negative_posts']
            ]
            labels = ['Positivo', 'Neutro', 'Negativo']
            plt.pie(sentiment_counts, labels=labels, autopct='%1.1f%%', startangle=90)
            plt.title(f'Distribuição de Sentimentos em r/{self.stats["subreddit"]}')
            plt.savefig(f"{output_path}sentiment_distribution_{self.stats['subreddit']}.png")
            plt.close()
            
            # Gráfico 2: Score vs Sentimento
            plt.figure(figsize=(10, 6))
            plt.scatter(self.processed_data['sentiment_compound'], 
                        self.processed_data['score'], alpha=0.6)
            plt.xlabel('Sentimento (Compound Score)')
            plt.ylabel('Score do Post')
            plt.title(f'Relação entre Sentimento e Popularidade em r/{self.stats["subreddit"]}')
            plt.savefig(f"{output_path}sentiment_vs_score_{self.stats['subreddit']}.png")
            plt.close()
            
            # Gráfico 3: Timeline de sentimentos
            plt.figure(figsize=(12, 6))
            time_sentiment = self.processed_data[['created_utc', 'sentiment_compound']].copy()
            time_sentiment['date'] = time_sentiment['created_utc'].dt.date
            daily_avg = time_sentiment.groupby('date')['sentiment_compound'].mean()
            
            plt.plot(daily_avg.index, daily_avg.values, marker='o')
            plt.xlabel('Data')
            plt.ylabel('Sentimento Médio')
            plt.title(f'Evolução do Sentimento ao Longo do Tempo em r/{self.stats["subreddit"]}')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{output_path}sentiment_timeline_{self.stats['subreddit']}.png")
            plt.close()
            
            logger.info(f"Visualizações salvas em {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na geração de visualizações: {e}")
            return False
    
    def generate_report(self, output_file: str = "polarization_report.txt"):
        """Gera relatório completo da análise"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("RELATÓRIO DE ANÁLISE DE POLARIZAÇÃO - NEXPOL\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Subreddit analisado: r/{self.stats['subreddit']}\n")
                f.write(f"Total de posts analisados: {self.stats['total_posts']}\n")
                f.write(f"Score médio dos posts: {self.stats['avg_score']:.2f}\n")
                f.write(f"Comentários médios por post: {self.stats['avg_comments']:.2f}\n\n")
                
                f.write("ANÁLISE DE POLARIZAÇÃO:\n")
                f.write(f"Score de polarização: {self.stats['polarization_score']:.4f}\n")
                f.write(f"Nível de polarização: {self.stats['polarization_level']}\n\n")
                
                f.write("DISTRIBUIÇÃO DE SENTIMENTOS:\n")
                f.write(f"Posts positivos: {self.stats['positive_posts']} ({self.stats['positive_posts']/self.stats['total_posts']*100:.1f}%)\n")
                f.write(f"Posts neutros: {self.stats['neutral_posts']} ({self.stats['neutral_posts']/self.stats['total_posts']*100:.1f}%)\n")
                f.write(f"Posts negativos: {self.stats['negative_posts']} ({self.stats['negative_posts']/self.stats['total_posts']*100:.1f}%)\n")
                f.write(f"Sentimento médio: {self.stats['avg_sentiment']:.4f}\n")
                
                # Top posts mais polarizados
                polarized_posts = self.processed_data.nlargest(5, 'sentiment_compound')
                f.write("\nTOP POSTS MAIS POSITIVOS:\n")
                for idx, row in polarized_posts.iterrows():
                    f.write(f"- {row['title'][:50]}... (Score: {row['score']}, Sentimento: {row['sentiment_compound']:.4f})\n")
                
                polarized_posts = self.processed_data.nsmallest(5, 'sentiment_compound')
                f.write("\nTOP POSTS MAIS NEGATIVOS:\n")
                for idx, row in polarized_posts.iterrows():
                    f.write(f"- {row['title'][:50]}... (Score: {row['score']}, Sentimento: {row['sentiment_compound']:.4f})\n")
            
            logger.info(f"Relatório salvo em {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na geração do relatório: {e}")
            return False

# Testes unitários
def test_reddit_processor():
    """Testes para a classe RedditDataProcessor"""
    processor = RedditDataProcessor()
    
    # Teste de limpeza de texto
    test_text = "Hello world! https://example.com This is a test!!!"
    cleaned = processor.clean_text(test_text)
    assert "https" not in cleaned
    assert "!" not in cleaned
    print("✓ Teste de limpeza de texto passou")
    
    # Teste de análise de sentimento
    sentiment = processor.analyze_sentiment("I love this amazing wonderful product!")
    assert sentiment['compound'] > 0.5
    print("✓ Teste de análise de sentimento positivo passou")
    
    sentiment = processor.analyze_sentiment("I hate this terrible awful product!")
    assert sentiment['compound'] < -0.5
    print("✓ Teste de análise de sentimento negativo passou")
    
    # Teste de cálculo de polarização
    test_scores = [
        {'compound': 0.9}, {'compound': 0.8}, {'compound': -0.7}, {'compound': -0.6}
    ]
    polarization = processor.calculate_polarization_score(test_scores)
    assert polarization > 0.4
    print("✓ Teste de cálculo de polarização passou")
    
    print("Todos os testes passaram!")

# Exemplo de uso
if __name__ == "__main__":
    # Executar testes
    try:
        test_reddit_processor()
    except Exception as e:
        print(f"Testes falharam: {e}")
    
    # Exemplo de análise
    processor = RedditDataProcessor()
    
    # Analisar subreddits políticos comuns para comparação
    subreddits = ['politics', 'conservative', 'liberal', 'news']
    
    for subreddit in subreddits:
        print(f"\nAnalisando r/{subreddit}...")
        
        success = processor.process_data(subreddit, sample_size=30)
        if success:
            # Gerar visualizações
            processor.generate_visualizations()
            
            # Gerar relatório
            report_file = f"report_{subreddit}.txt"
            processor.generate_report(report_file)
            
            print(f"Análise de r/{subreddit} concluída. Relatório: {report_file}")
        else:
            print(f"Falha na análise de r/{subreddit}")
        
        # Esperar entre requisições para não sobrecarregar a API
        time.sleep(2)
