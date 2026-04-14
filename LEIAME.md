# 📚 Documentação Completa do Projeto: Busca Rápida Rede Credenciada Saúde Caixa

**Autor:** Nathan Dias Irigoyen  
**Pasta Base:** Saude Caixa  
**Data de Criação/Última Revisão:** Janeiro/Março de 2026

## ⚠️ AVISO LEGAL IMPORTANTE
Este é um **projeto independente** e não possui **nenhum vínculo oficial** com a Caixa Econômica Federal ou o plano Saúde Caixa. O objetivo é apenas otimizar a visualização e busca dos dados, que são extraídos de fontes públicas. Para acessar o portal oficial, utilize o link: [https://saude.caixa.gov.br/RedeAtendimento/](https://saude.caixa.gov.br/RedeAtendimento/). 

---

## 🎯 Visão Geral e Arquitetura do Projeto

O projeto é uma solução de três fases para obter, processar e disponibilizar de forma performática e segura os dados da rede credenciada para buscas na web.

| Fase | Objetivo Principal | Ferramentas Chave | Arquivos Relacionados |
| :---|:---|:---|:---|
| **1. Extração (Scraping)** | Obter os dados brutos do site oficial. | Python, Selenium, ChromeDriverManager. | `scraper_sc_html.py` |
| **2. Processamento e Otimização** | Limpar, estruturar e fragmentar (sharding) os dados para busca. | Python, BeautifulSoup, Regex. | `Processa_html_para_json.py`, `sharding.py`, `rede_credenciada_final.zip` |
| **3. Implantação e Busca Web** | Dispor os dados em um frontend web, com backend seguro e rápido. | JavaScript, Cloudflare Worker (`worker.js`), Cloudflare R2, R2 SDK (`upload.js`). | `index.html`, `ShardedProviderService.js`, `worker.js`, `upload.js` |

---

## 📂 Estrutura de Arquivos Detalhada

| Arquivo | Tipo | Descrição Completa |
| :---|:---|:---|
| `Projeto_rede_credenciada.md` | Documentação | Log de desenvolvimento do projeto, detalhando a construção do scraper, as utilidades de limpeza e as estratégias de defesa anti-scraping. |
| `scraper_sc_html.py` | Python Script | Contém a lógica de navegação e extração de páginas HTML do site oficial, incluindo tratamento de paginação. |
| `Processa_html_para_json.py`| Python Script | Realiza a conversão dos arquivos HTML brutos em um arquivo JSON estruturado, limpando textos e identificando campos-chave (Nome, Conselho, CNPJ). |
| `rede_credenciada_final.json`| Dados (JSON) | Arquivo consolidado (exemplo) contendo todos os registros de prestadores, antes da fragmentação. Inclui Pessoa Física e Jurídica. |
| `sharding.py` | Python Script | Implementa a fragmentação (*sharding*) do JSON por Estado, Cidade ou Especialidade. Essencial para otimizar o carregamento e a busca no ambiente web. |
| `index.html` | Frontend (HTML/JS) | Interface do usuário para a busca. Apresenta o formulário de pesquisa e a lógica de seleção em cascata (Estado → Cidade → Especialidade). |
| `ShardedProviderService.js` | JS (Cliente API) | Módulo que encapsula a comunicação com o Backend (Cloudflare Worker), enviando os filtros de busca e gerenciando o cache local. |
| `worker.js` | JS (Cloudflare Worker) | Lógica de Backend. Valida o token, consulta o mapa de arquivos para buscar o *shard* correto no R2 e executa a filtragem final dos resultados. |
| `upload.js` | JS (Deploy/R2) | Script utilitário para realizar o upload em lote dos arquivos processados e estáticos para o armazenamento Cloudflare R2 (compatível com AWS S3 SDK). |

---

## ⚙️ Detalhes e Mecanismos Chave

### 1. Sharding e Otimização da Busca
A principal estratégia de performance é a fragmentação (*sharding*) dos dados:

*   **Finalidade:** Em vez de carregar um arquivo JSON de 200MB no navegador (lento e custoso), os dados são pré-divididos (Ex: por Estado).
*   **Lógica:** O `sharding.py` cria o `mapa_arquivos.json`, que o `worker.js` usa para buscar no Cloudflare R2 **apenas** o arquivo de dados (shard) necessário para o Estado/Cidade/Especialidade selecionada.

### 2. Tratamento de Dados Semi-Estruturados
O `Processa_html_para_json.py` lida com a variabilidade dos dados:

*   **Identificação:** Utiliza Regex para extrair `Nome` e `Conselho Profissional` (CRM/CRO/CREFITO etc.) da primeira linha de cada bloco de prestador.
*   **Especialidades:** O `sharding.py` prioriza a especialidade em `ODONTOLOGIA` quando o campo é preenchido, caindo para `Especialidade(s)` em outros casos, e para `Geral` como fallback.

### 3. Segurança (Backend)
A arquitetura Cloudflare Worker/R2 aumenta a segurança:

*   **Proteção do Banco de Dados:** Os *shards* de dados estão no R2, sem acesso público direto.
*   **Controle de Acesso:** O `worker.js` exige um `X-Auth-Token` (definido no `ShardedProviderService.js` e `worker.js`) para processar as requisições, impedindo que terceiros usem a API sem permissão.

---

## 🛠️ Próximos Passos
1.  **Executar `scraper_sc_html.py`** para obter o HTML bruto atualizado.
2.  **Executar `Processa_html_para_json.py`** seguido por **`sharding.py`** para gerar os arquivos JSON otimizados e o mapa.
3.  **Atualizar credenciais** nos arquivos `upload.js`, `ShardedProviderService.js` e `worker.js`.
4.  **Executar `upload.js`** para fazer o deploy dos arquivos para o Cloudflare R2.
5.  **Configurar o Worker** na Cloudflare para apontar para o bucket R2.
