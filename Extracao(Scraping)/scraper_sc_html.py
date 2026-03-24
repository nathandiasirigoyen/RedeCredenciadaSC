from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from datetime import datetime

def executar_scraper_saude_caixa():
    """
    Função Principal que encapsula toda a lógica (Closure).
    Todas as funções auxiliares e configurações são aninhadas aqui dentro,
    tornando esta função totalmente auto-contida e segura para imports.
    """

    # ============================================================================
    # 1. CONFIGURAÇÕES E CONSTANTES (Agora Locais)
    # ============================================================================

    URL = "https://saude.caixa.gov.br/RedeAtendimento"
    PASTA_SAIDA = "saude_caixa_html_bruto"
    TEMPO_ESPERA = 10

    # ============================================================================
    # 2. SELETORES (Agora Locais)
    # ============================================================================

    SELETOR_ESTADO_CONTAINER = (By.CSS_SELECTOR, "#select2-estado-container")
    SELETOR_BTN_ENCONTRAR = (By.ID, "btnBuscar")
    SELETOR_ULTIMA_PAGINA = (By.CSS_SELECTOR, "ul.pagination li:last-child a i.fa-angle-double-right")
    SELETOR_BTN_ANTERIOR = (By.CSS_SELECTOR, "ul.pagination li:not(.disabled) a i.fa-angle-left")

    ESTADOS = [
        "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", 
        "Distrito Federal", "Espírito Santo", "Goiás", "Maranhão", 
        "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Pará", 
        "Paraíba", "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro", 
        "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia", "Roraima", 
        "Santa Catarina", "São Paulo", "Sergipe", "Tocantins"
    ]
    
    # Variável local compartilhada pelas funções aninhadas
    driver = None

    # ============================================================================
    # 3. FUNÇÕES ANINHADAS
    # ============================================================================

    def criar_pasta_saida():
        # Acessa PASTA_SAIDA do escopo pai (executar_scraper_saude_caixa)
        if not os.path.exists(PASTA_SAIDA):
            os.makedirs(PASTA_SAIDA)
        print(f"📁 Pasta de saída definida: {os.path.abspath(PASTA_SAIDA)}")
        
    def configurar_driver():
        nonlocal driver # Permite modificar a variável 'driver' do escopo pai
        options = Options()
        options.add_experimental_option("prefs", {"download.prompt_for_download": False})
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        return driver
    
    def aguardar_elemento(seletor, tempo=TEMPO_ESPERA, clicavel=False):
        try:
            if clicavel:
                return WebDriverWait(driver, tempo).until(EC.element_to_be_clickable(seletor))
            else:
                return WebDriverWait(driver, tempo).until(EC.presence_of_element_located(seletor))
        except: return None

    def selecionar_estado_select2(estado):
        try:
            container = aguardar_elemento(SELETOR_ESTADO_CONTAINER, clicavel=True)
            if not container:
                print("❌ Container Estado não achado.")
                return False
            
            container.click()
            time.sleep(0.5)
            
            try:
                campo = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
                campo.clear()
                campo.send_keys(estado)
                time.sleep(0.8)
            except: pass
            
            opcoes = driver.find_elements(By.CSS_SELECTOR, ".select2-results__option")
            for op in opcoes:
                if estado.lower() in op.text.lower():
                    op.click()
                    print(f"✅ Estado selecionado: {estado}")
                    time.sleep(1)
                    return True
            try:
                campo.send_keys(Keys.ENTER)
                return True
            except: pass
            
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False
        except Exception as e:
            print(f"Erro seleção: {e}")
            return False

    def clicar_encontrar():
        try:
            btn = aguardar_elemento(SELETOR_BTN_ENCONTRAR, clicavel=True)
            if btn:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                return True
        except: pass
        print("❌ Falha ao clicar Encontrar")
        return False
    
    def aguardar_resultados_com_confirmacao():
        print("⏳ Aguardando carregamento dos resultados...")
        try:
            # Espera até 20 segundos para os resultados aparecerem
            WebDriverWait(driver, 20).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, ".card") or 
                          d.find_elements(By.XPATH, "//*[contains(text(), 'ESPECIALIDADE')]") or
                          d.find_elements(By.XPATH, "//*[contains(text(), 'Nenhum resultado')]") or
                          d.find_elements(By.ID,"idAlerta")
            )
            print("✅ Resultados detectados. Continuando automaticamente.")
            return True
        except TimeoutException:
            # Se der timeout, apenas avisa e continua sem pedir input
            print("⚠️ Tempo limite excedido aguardando resultados. Continuando execução...")
            return True

    def ir_para_ultima_pagina():
        try:
            btn = driver.find_elements(*SELETOR_ULTIMA_PAGINA)
            if btn and btn[0].is_displayed():
                pai = btn[0].find_element(By.XPATH, "./..")
                driver.execute_script("arguments[0].click();", pai)
                time.sleep(3)
        except: pass

    def clicar_pagina_anterior():
        try:
            btn = driver.find_elements(*SELETOR_BTN_ANTERIOR)
            if btn:
                pai = btn[0].find_element(By.XPATH, "./..")
                driver.execute_script("arguments[0].click();", pai)
                time.sleep(2)
                return True
        except: pass
        return False

    def salvar_html_pagina(estado, numero_pagina):
        """Salva o código-fonte atual em um arquivo HTML."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            estado_limpo = estado.replace(" ", "_")
            
            # Nome do arquivo: Estado_PaginaX_Timestamp.html
            nome_arquivo = f"{PASTA_SAIDA}/{estado_limpo}_pag{numero_pagina}_{timestamp}.html"
            
            # Pega o HTML completo
            html_content = driver.page_source
            
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            print(f"   💾 HTML salvo: {os.path.basename(nome_arquivo)}")
            return True
        except Exception as e:
            print(f"   ❌ Erro ao salvar HTML: {e}")
            return False

    def processar_estado(estado):
        print(f"\n{'='*40}")
        print(f"📍 Estado: {estado}")
        
        if not selecionar_estado_select2(estado): return
        clicar_encontrar()
        
        if not aguardar_resultados_com_confirmacao(): 
            return
            
        ir_para_ultima_pagina()
        
        # --- ALTERAÇÃO SOLICITADA ---
        # Detecta automaticamente o número da página baseada na classe 'active' do HTML
        try:
            # Como já fomos para a última página, o elemento ativo contém o número total
            elem_ativo = driver.find_element(By.CSS_SELECTOR, "ul.pagination li a.active")
            qtd = int(elem_ativo.text.strip())
            print(f"🔢 Total de páginas detectadas: {qtd}")
        except:
            print("⚠️ Paginação não encontrada ou erro na leitura. Assumindo 1 página.")
            qtd = 1
        # ----------------------------
        
        if qtd <= 0: return

        print(f"🚀 Salvando HTML de {qtd} páginas...")
        
        # Loop Reverso
        for i in range(qtd):
            # Calcula o número da página atual (ex: se tem 5 pags, começa na 5, depois 4...)
            pag_atual = qtd - i
            
            # Salva o HTML
            salvar_html_pagina(estado, pag_atual)
            
            # Volta página (se não for a última iteração)
            if i < (qtd - 1):
                if not clicar_pagina_anterior():
                    print("⚠️ Falha ao voltar página.")
                    break
                # Pequena pausa para garantir carregamento do DOM antes de salvar o próximo
                time.sleep(2)
        
        print(f"✅ Fim {estado}")

    # ============================================================================
    # 4. EXECUÇÃO DO FLUXO PRINCIPAL
    # ============================================================================

    criar_pasta_saida()
    configurar_driver()
    
    print(f"\n{'='*50}")
    print("LISTA DE ESTADOS DISPONÍVEIS:")
    print(", ".join(ESTADOS))
    print("="*50)
    
    selecao = input("\nDigite os nomes dos estados (separados por vírgula) ou ENTER para TODOS: ").strip()
    
    lista_estados_final = []
    if selecao:
        nomes_digitados = [x.strip().lower() for x in selecao.split(',')]
        for estado_real in ESTADOS:
            if estado_real.lower() in nomes_digitados:
                lista_estados_final.append(estado_real)
        if not lista_estados_final:
            print("⚠️ Nenhum estado válido encontrado. Usando lista COMPLETA.")
            lista_estados_final = ESTADOS
        else:
            print(f"✅ Processando apenas: {', '.join(lista_estados_final)}")
    else:
        print("✅ Processando TODOS os estados.")
        lista_estados_final = ESTADOS
    
    try:
        driver.get(URL)
        time.sleep(3)
        for estado in lista_estados_final:
            processar_estado(estado)
    except Exception as e:
        print(f"Erro Fatal: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    executar_scraper_saude_caixa()