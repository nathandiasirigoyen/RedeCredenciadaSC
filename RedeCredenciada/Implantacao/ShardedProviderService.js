/**
 * ShardedProviderService (Client Version)
 * * Este serviço agora atua como um cliente HTTP que se comunica com o seu Cloudflare Worker.
 * A lógica pesada (Mapas, R2, Filtros) foi movida para o backend (Worker) por segurança.
 */
class ShardedProviderService {
    constructor() {
        // =========================================================================
        // ⚠️ CONFIGURAÇÕES OBRIGATÓRIAS (PREENCHA AQUI)
        // =========================================================================
        
        // 1. URL do seu Cloudflare Worker (Ex: https://api-busca.seu-usuario.workers.dev)
        this.workerApiUrl = "API URL";

        // 2. Token de Segurança (Opcional, mas recomendado)
        // Defina uma string aleatória aqui e configure a mesma no seu Worker para validar a requisição.
        this.apiToken = "TOKEN API"; 

        // =========================================================================

        this.cache = new Map(); // Mantém o cache de requisições para economizar chamadas ao Worker
    }

    /**
     * Envia os filtros para o Worker e retorna a lista de prestadores processada.
     * Mantém a mesma assinatura do método anterior para compatibilidade com o HTML.
     */
    async findProviders({ state, city, specialty, name, registerNum }) {
        // Validação básica antes de chamar a API
        if (!state) {
            console.warn("O campo Estado é obrigatório.");
            return [];
        }

        // Cria uma chave única para este conjunto de filtros (Cache Key)
        // Ex: "SP|Santos|Cardio||"
        const cacheKey = `${state}|${city || ''}|${specialty || ''}|${name || ''}|${registerNum || ''}`;

        // 1. Verifica se já fizemos essa busca nesta sessão (Economia de banda e latência)
        if (this.cache.has(cacheKey)) {
            console.log("Recuperando dados do cache local...");
            return this.cache.get(cacheKey);
        }

        try {
            console.log("Consultando Cloudflare Worker...");

            // 2. Chamada à API (Worker)
            const response = await fetch(this.workerApiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Envia o token para o Worker saber que é o seu site chamando
                    'X-Auth-Token': this.apiToken 
                },
                // Envia apenas os dados necessários
                body: JSON.stringify({ 
                    state, 
                    city, 
                    specialty, 
                    name, 
                    registerNum 
                })
            });

            // 3. Tratamento de Erros HTTP
            if (!response.ok) {
                if (response.status === 403) throw new Error("Acesso negado pelo Worker (Token ou Origem inválidos).");
                if (response.status === 404) return []; // Nenhum dado encontrado é normal
                if (response.status === 429) throw new Error("Muitas requisições. Tente novamente em instantes.");
                throw new Error(`Erro no servidor: ${response.statusText}`);
            }

            // 4. Processamento da Resposta
            const data = await response.json();

            // Salva no cache e retorna
            this.cache.set(cacheKey, data);
            return data;

        } catch (error) {
            console.error("Falha na comunicação com a API:", error);
            // Em caso de erro crítico, retorna array vazio para não quebrar a UI
            // Opcional: Relançar o erro se quiser mostrar alerta no HTML
            throw error; 
        }
    }
}