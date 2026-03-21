/**
 * Cloudflare Worker - Lógica de Backend Seguro
 * Este código roda nos servidores da Cloudflare, não no navegador do usuário.
 */
export default {
  async fetch(request, env, ctx) {
    // =========================================================================
    // 1. CONFIGURAÇÕES DE SEGURANÇA & VALIDAÇÃO
    // =========================================================================
    
    // Configurar CORS (Permite que apenas seu site acesse este Worker)
    const corsHeaders = {
      'Access-Control-Allow-Origin': 'https://seusite.pages.dev', // ⚠️ MUDE ISSO PARA SEU DOMÍNIO FINAL
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token',
    };

    // Responder a pre-flight requests (necessário para navegadores)
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Apenas aceita POST
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405, headers: corsHeaders });
    }

    // Validação do Token Secreto (O mesmo que você colocou no provider_service.js)
    const token = request.headers.get('X-Auth-Token');
    const MY_SECRET_TOKEN = "SUBSTITUA-POR-UM-TOKEN-SECRETO-ALEATORIO"; // ⚠️ Tem que ser IGUAL ao do frontend
    
    if (token !== MY_SECRET_TOKEN) {
      return new Response(JSON.stringify({ error: 'Acesso Negado (Token Inválido)' }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // =========================================================================
    // 2. RECEBIMENTO DO PEDIDO (INPUT)
    // =========================================================================
    
    let filters;
    try {
      filters = await request.json(); // { state: "SP", city: "Santos", ... }
    } catch (e) {
      return new Response('JSON Inválido', { status: 400, headers: corsHeaders });
    }

    const { state, city, specialty, name, registerNum } = filters;

    if (!state) {
      return new Response(JSON.stringify({ error: 'Estado é obrigatório' }), { 
        status: 400, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // =========================================================================
    // 3. INTELIGÊNCIA: DESCOBRIR QUAL ARQUIVO ABRIR (USANDO O MAPA)
    // =========================================================================

    // Primeiro, buscamos o mapa_arquivos.json no R2 para saber a estrutura
    // 'BUCKET' é o nome da ligação que faremos no painel da Cloudflare depois
    const mapObject = await env.BUCKET.get('output_shards/mapa_arquivos.json');
    
    if (!mapObject) {
      return new Response(JSON.stringify({ error: 'Erro interno: Mapa não encontrado' }), { status: 500, headers: corsHeaders });
    }

    const fileMap = await mapObject.json();

    // Lógica de navegação no mapa
    let targetFileUrl = null;
    let node = fileMap[state];

    if (typeof node === 'string') {
        targetFileUrl = node; // Modo 1: Estado direto
    } else if (node) {
        // Se temos cidade e o mapa desce até cidade
        if (city && node[city]) {
            let cityNode = node[city];
            if (typeof cityNode === 'string') {
                targetFileUrl = cityNode; // Modo 2: Cidade encontrada
            } else if (specialty && cityNode[specialty]) {
                targetFileUrl = cityNode[specialty]; // Modo 3: Especialidade encontrada
            }
        }
        
        // Se não achou arquivo específico, tenta fallback (ex: se pediu cidade mas mapa só tem estado)
        if (!targetFileUrl && typeof node === 'string') targetFileUrl = node;
    }

    if (!targetFileUrl) {
      // Se não achou arquivo correspondente no mapa, retorna vazio
      return new Response(JSON.stringify([]), { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      });
    }

    // =========================================================================
    // 4. BUSCA E FILTRAGEM DOS DADOS REAIS
    // =========================================================================

    // Limpa o prefixo "./" ou "output_shards/" se houver no mapa, pois no R2 a chave é direta
    // Supondo que o mapa tenha: "./output_shards/SP/arquivo.json", precisamos limpar para "output_shards/SP/arquivo.json"
    const r2Key = targetFileUrl.replace(/^\.\//, ''); 

    const dataObject = await env.BUCKET.get(r2Key);
    
    if (!dataObject) {
      return new Response(JSON.stringify([]), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    const rawList = await dataObject.json();

    // FILTRAGEM SERVER-SIDE (Aqui está a segurança extra!)
    // O usuário recebe APENAS o que filtrou, nunca a lista completa do JSON.
    
    const filteredList = rawList.filter(item => {
        // Normalizações
        const itemCity = (item["Cidade/Estado"] || "").toLowerCase();

        // Para prestadores de odontologia, o campo "Especialidade(s)" vem vazio ("") e as
        // especialidades ficam no campo "ODONTOLOGIA" com valores como "CLÍNICA GERAL".
        // Porém, no mapa de arquivos (e no dropdown do site), a chave é composta:
        // "ODONTOLOGIA CLÍNICA GERAL". Precisamos reconstruir esse formato aqui para que
        // o filtro filterSpec.includes() encontre a correspondência corretamente.
        let itemSpecs;
        if (item["ODONTOLOGIA"]) {
            // Separa por vírgula (ex: "CLÍNICA GERAL, ODONTOLOGIA: DENTÍSTICA")
            // Remove eventual prefixo redundante "ODONTOLOGIA:" que já existe dentro do valor
            // e prefixa cada sub-especialidade com "ODONTOLOGIA " para formar a chave completa.
            itemSpecs = item["ODONTOLOGIA"]
                .split(",")
                .map(s => "ODONTOLOGIA " + s.replace(/^ODONTOLOGIA\s*:\s*/i, "").trim())
                .join(", ")
                .toLowerCase();
        } else {
            itemSpecs = (item["Especialidade(s)"] || "").toLowerCase();
        }

        const itemName = (item["Nome"] || "").toLowerCase();
        const itemReg = Object.values(item).join(" ").replace(/[^a-zA-Z0-9]/g, "");

        // Inputs normalizados
        const filterCity = city ? city.toLowerCase() : null;
        const filterSpec = specialty ? specialty.toLowerCase() : null;
        const filterName = name ? name.toLowerCase().trim() : null;
        const filterReg = registerNum ? registerNum.replace(/[^a-zA-Z0-9]/g, "") : null;

        if (filterCity && !itemCity.includes(filterCity)) return false;
        if (filterSpec && !itemSpecs.includes(filterSpec)) return false;
        if (filterName && !itemName.includes(filterName)) return false;
        if (filterReg && !itemReg.includes(filterReg)) return false;

        return true;
    });

    // =========================================================================
    // 5. RESPOSTA FINAL
    // =========================================================================

    return new Response(JSON.stringify(filteredList), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
};