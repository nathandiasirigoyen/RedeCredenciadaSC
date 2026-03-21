"""
Processador de HTML para JSON - Saúde Caixa
===========================================

Objetivo:
Ler arquivos .html brutos salvos anteriormente e estruturar os dados em JSON.

Lógica de Extração:
1. Identifica blocos de prestadores.
2. Separa Nome e Conselho (CRM/CRO) da primeira linha.
3. Processa campos onde o valor pode estar na mesma linha OU na próxima.
"""

import os
import glob
import json
import re
from bs4 import BeautifulSoup

# Configurações
PASTA_ENTRADA = "saude_caixa_html_bruto"
ARQUIVO_SAIDA = "rede_credenciada_final.json"

def limpar_texto(texto):
    """Remove espaços extras e caracteres invisíveis."""
    if not texto: return ""
    return " ".join(texto.split())

def extrair_dados_do_bloco(container_soup):
    """
    Recebe o objeto BeautifulSoup de um card/container e retorna um dicionário limpo.
    """
    # Obtém o texto separando por quebras de linha
    texto_bruto = container_soup.get_text(separator="\n", strip=True)
    linhas = [limpar_texto(l) for l in texto_bruto.split('\n') if limpar_texto(l)]
    
    dados = {}
    chave_principal = None
    capturando = False
    ultimo_campo_pendente = None # Variável para guardar chave esperando valor na próxima linha
    
    # Itera sobre as linhas para estruturar
    for i, linha in enumerate(linhas):
        # Gatilho de início
        if "Mais Informações" in linha or "Mais informações" in linha:
            capturando = True
            continue
            
        if not capturando:
            continue
            
        # A primeira linha após "Mais Informações" é a Chave Principal
        if chave_principal is None:
            # Regex para identificar documentos de conselho no final da linha (CRM, CRO, etc.)
            # Captura algo como "CRM: 12345" ou "CRO 123"
            match_conselho = re.search(r'\s*((?:CRM|CRO|CREFITO|RMS|CRP|COREN|OAB)[\s:]*[\d\.\/-]+.*$)', linha, re.IGNORECASE)
            
            if match_conselho:
                conselho_completo = match_conselho.group(1).strip()
                # Remove o conselho do nome principal
                nome_limpo = linha[:match_conselho.start()].strip()
                
                chave_principal = nome_limpo
                dados['Nome'] = nome_limpo
                dados['Conselho Profissional'] = conselho_completo # Adiciona antes dos outros dados
            else:
                chave_principal = linha
                dados['Nome'] = linha
            
            continue
        
        # Processa campos (ex: "Razão Social:")
        if ":" in linha:
            # Divide apenas na primeira ocorrência de ":"
            partes = linha.split(":", 1)
            chave = partes[0].strip()
            valor = partes[1].strip()
            
            # Se tiver valor na mesma linha, salva direto
            if valor:
                dados[chave] = valor
                ultimo_campo_pendente = None
            else:
                # Se o valor estiver vazio, marca para pegar na próxima linha
                ultimo_campo_pendente = chave
                # Inicializa com vazio para garantir que a chave exista
                dados[chave] = ""
        
        elif ultimo_campo_pendente:
            # Se esta linha não tem ":", e temos um campo pendente, esta linha é o valor
            dados[ultimo_campo_pendente] = linha
            ultimo_campo_pendente = None
            
        else:
            # Linha solta que não é chave nem valor esperado (pode ser continuação de endereço, etc.)
            pass

    return chave_principal, dados

def processar_arquivos():
    if not os.path.exists(PASTA_ENTRADA):
        print(f"❌ Pasta '{PASTA_ENTRADA}' não encontrada.")
        return

    arquivos = glob.glob(os.path.join(PASTA_ENTRADA, "*.html"))
    if not arquivos:
        print("❌ Nenhum arquivo .html encontrado na pasta.")
        return

    print(f"📂 Encontrados {len(arquivos)} arquivos para processar.")
    
    # Dicionário mestre que vai virar o JSON
    dados_consolidados = {}
    total_registros = 0

    for caminho_arquivo in arquivos:
        print(f"   Processando: {os.path.basename(caminho_arquivo)}...")
        
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            soup = BeautifulSoup(conteudo, 'html.parser')
            
            # ESTRATÉGIA DE BUSCA:
            # Busca botões de imprimir para localizar os cards
            botoes_imprimir = soup.find_all(class_=lambda c: c and 'ver-detalhes-imprimir' in c)
            
            if not botoes_imprimir:
                botoes_imprimir = soup.select(".card button, .card a.btn")

            for btn in botoes_imprimir:
                # Sobe na hierarquia até achar o container que agrupa os dados
                container = btn.parent
                while container and "Mais Informações" not in container.get_text():
                    container = container.parent
                
                if container:
                    chave, dados = extrair_dados_do_bloco(container)
                    
                    if chave:
                        dados_consolidados[chave] = dados
                        total_registros += 1

        except Exception as e:
            print(f"   ⚠️ Erro ao ler {os.path.basename(caminho_arquivo)}: {e}")

    # Salva o JSON final
    try:
        with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
            json.dump(dados_consolidados, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ Processamento Concluído!")
        print(f"📊 Total de Médicos/Locais únicos: {len(dados_consolidados)}")
        print(f"💾 Arquivo salvo: {os.path.abspath(ARQUIVO_SAIDA)}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar JSON: {e}")

if __name__ == "__main__":
    processar_arquivos()