Projeto Rede Credenciada do Saúde Caixa
        Nathan Dias Irigoyen - 01/2026

1. Construção do scraper que extrai os dados do site oficial;
    🆗 Solução: `scraper_sc_html.py`;
        🆗 Adicionar automatização completa (2/2)
            🆗 Solução: confirma carregamento da página a partir do elemento `id="idAlerta"`;
            🆗 Solução: `driver.find_element(By.CSS_SELECTOR, "ul.pagination li a.active")` - encontra o bloco da lista de paginação (`\<ul.pagination\>`) -> encontra o item da lista que está marcado como ativo (`\<li\>` - número de página ativo) -> pega o número da página que está dentro do link `<a>`.
    ✅ Finalizado (2/2);

2. Construção das utilidades para organização e limpeza dos dados obtidos;
✅ Finalizado (2/2).

  2.1 Script organizador:
  🆗 `Processa_html_para_json.py`;
  ✅ Finalizado (3/3). 

      2.1.1 Lê o html e separa apenas os dados relevantes;
      ✅ Finalizado.

      2.1.2 Organiza os dados no formato chave:valor;
      ✅ Finalizado.

      2.1.3 Junta todos em um arquivo .json.
      ✅ Finalizado.
        ⁉️Foi necessário utilizar o formato .json para armazenamento de dados semi-estruturados tendo em vista que ele permite armazenar objetos com campos distintos
        entre sí, como é o caso das especialidades médicas, cuja quantidade vai divergir substancialmente entre os registros.

  2.2 Limpeza dos dados:
  ✅ Finalizado (3/3).

      2.2.1 Retira os números excessivos encontrados à **esquerda** nos campos de DDD dos registros (ex: (55\d\d) e (00\d\d));
      🆗 Solução: replace; com Regex: `Find(/(55), Replace()`.
      ✅ Finalizado.

      2.2.2 Retira os números excessivos encontrados à **direita** nos campos de DDD dos registros (ex: (51\d)) e transfere o algarismo para o número de telefone encontrado após o `)`;
      🆗 Solução: replace com Regex: `Find(\((\d{2})(\d+)\)), Replace(($1) $2)`.
      ✅ Finalizado.

      2.2.3 Corrige a acentuação das palavras "Pessoa Fisica" e "Pessoa Juridica";
      ✅ Finalizado.

3. Estratégias de defesa anti-scraping:
✅ Finalizado (8/8).

  3.1 *Sharding*: transformação do arquivo de bloco único em vários arquivos menores, dificultando o acesso por bots;
  🆗 Solução: *sharding* `shard_json_data.py`.
  🆗 Solução: mapa para backend .js `shard_json_data.py`.
  ✅ Finalizado (2/2).

  3.2 *ID Obfuscation*: nomeação dos arquivos granulados a partir de um padrão aleatório;
  🆗 Solução: `shard_json_data.py`.
  ✅ Finalizado.

  3.3 *Honeypot*: armadilha para bots;
  ✅ Finalizado.

  3.4 Remoção de Atributos Óbvios: encapsula o objeto com uma função .js que o esconde. Evita que o download do HTML bruto contenha o objeto;
  🆗 Solução: CDN.
  ✅ Finalizado.

  3.5 Validação de Coordenadas com *isTrusted*: revisa se o clique é real ou feito por automação;
  ✅ Finalizado.

  3.6 *Shadow DOM*: esconde o HTML com os dados dentro de outro elemento não indexável;
  ✅ Finalizado.

  3.7 *Lazy Rendering*: carrega os elementos conforme a página vai sendo rolada;
  ✅ Finalizado.

  3.8 *Prompt Injection*: deixa uma instrução oculta para agente de IA não conseguirem copiar os dados;
  ✅ Finalizado.

4. Arquitetura de Frontend Delivery: CDN (Content Delivery Network) personalizada.

  4.1 Armazenamento: Cloudfare R2.
  🆗 Solução: via node.js, NPM, Wrangler.
  🆗 Solução: `upload.js`.
  ✅ Finalizado.
  
  4.2 Gateway: Cloudfare Worker.
  🆗 Solução: `worker.js`.
  ✅ Finalizado.
  
  4.3 Site: Cloudfare Pages.
  ✅ Finalizado.

  4.4  Script de entrega e APIs.
  ✅ Finalizado.

5. Publicação.

