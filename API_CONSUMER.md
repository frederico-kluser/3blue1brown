# Manim API – Guia para Consumidores (ondokai.com)

> **Última atualização:** 2026-01-03 • Ambiente público exposto via [`https://ondokai.com`](https://ondokai.com)
>
> Esta documentação é voltada para times ou integrações externas que vão consumir diretamente a Manim Video Generator API exposta pelo domínio ondokai.com. Todas as URLs, exemplos e recomendações abaixo assumem que você está chamando o serviço remoto (não a instância local).

---

## 1. Visão geral
- **O que é:** API FastAPI que transforma descrições em linguagem natural em código e vídeos Manim (Community Edition 0.19.0).
- **Principais entregas:**
  - Geração de código Manim validado (`/generate-code`).
  - Renderização e retorno do vídeo como base64 (`/generate-video`).
  - Download direto do arquivo MP4 (`/generate-video-file`).
- **Modelo LLM:** OpenAI GPT-5.1 Codex Max (temperatura baixa, otimizada para geração determinística de cenas).
- **Expectativa de latência:** 20–70s por render, dependendo da complexidade da cena e resolução solicitada.

### Base URL
```
https://ondokai.com
```

### Autenticação e segurança
- **Autenticação:** não há token ou API key neste endpoint público.
- **Transporte:** todo o tráfego passa pelo Cloudflare Tunnel com TLS (HTTPS). Certifique-se de sempre usar `https://`.
- **CORS:** o servidor envia `Access-Control-Allow-Origin: *` (e cabeçalhos relacionados), liberando chamadas diretas a partir de frontends como `http://localhost:5173`.
- **Rate limiting:** não há limite rígido configurado, mas recomenda-se no máximo 6–8 renders simultâneas para evitar fila (servidor roda em Mac mini M1 16GB).

### Requisitos de cliente
- Suporte a HTTPS e JSON.
- Timeout mínimo recomendado: **120 segundos** para `generate-video` e `generate-video-file`.
- Clientes que não suportam respostas grandes/streaming devem preferir `/generate-video` (retorna base64 em JSON).

---

## 2. Endpoint: Health Check
| Método | Caminho | Uso |
|--------|---------|-----|
| `GET`  | `/`     | Diagnóstico rápido da API e modelo ativo |

**Exemplo**
```bash
curl https://ondokai.com/
```
**Resposta**
```json
{
  "status": "healthy",
  "manim_version": "Manim Community v0.19.0",
  "openai_model": "gpt-5.1-codex-max"
}
```

---

## 3. Endpoint: `POST /generate-code`
Retorna apenas o código Manim e metadados de validação.

### Request body
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `description` | string | ✅ | Prompt em linguagem natural (10–2000 chars). |
| `width` | int | opcional | Resolução horizontal. Default 1920. Intervalo [320, 3840]. |
| `height` | int | opcional | Resolução vertical. Default 1080. Intervalo [320, 3840]. |

### Exemplo (curl)
```bash
curl -X POST https://ondokai.com/generate-code \
  -H "Content-Type: application/json" \
  -d '{
        "description": "Create a blue circle that grows then slides right",
        "width": 1280,
        "height": 720
      }'
```

### Resposta (sucesso)
```json
{
  "success": true,
  "code": "from manim import *\n...",
  "scene_name": "GeneratedScene",
  "is_valid": true,
  "validation_message": "Code validated successfully"
}
```

### Resposta (erro de validação)
```json
{
  "success": false,
  "error": "Code generation failed: description must be >= 10 characters"
}
```

---

## 4. Endpoint: `POST /generate-video`
Gera o código, renderiza via Manim CE 0.19.0 e retorna o vídeo em base64.

### Request body
Mesmo payload do `/generate-code`.

### Resposta (sucesso)
```json
{
  "success": true,
  "scene_name": "GeneratedScene",
  "video_base64": "AAAAIGZ0eXBpc29tAAACAGlzb20..."
}
```

- `video_base64` corresponde a um arquivo MP4 em H.264 (60 FPS). Salve convertendo de base64 para bytes.
- O tamanho típico varia de 150 KB a alguns MB, dependendo da duração e resolução.

### Resposta (falha)
```json
{
  "success": false,
  "error": "Render failed: Render timeout after 120 seconds",
  "render_logs": "...stderr do Manim..."
}
```

### Exemplo (JavaScript Fetch)
```javascript
const payload = {
  description: "Show the Pythagorean theorem equation a^2 + b^2 = c^2 appearing",
  width: 1280,
  height: 720,
};

fetch("https://ondokai.com/generate-video", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
})
  .then(async (response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.error ?? "unknown error");
    const mp4 = Buffer.from(data.video_base64, "base64");
    console.log(`Render ok, bytes: ${mp4.length}`);
  })
  .catch(console.error);
```

### Boas práticas
- Configure timeout mínimo de 120s.
- Retente com backoff em caso de 524/504 (Cloudflare derruba requests que excedem ~100s sem resposta).
- Limite as requisições paralelas para evitar saturar o túnel (6–8 simultâneas recomendadas no hardware atual).
- O backend já tenta regenerar o código Manim até **3 vezes** antes de desistir; cada retry adiciona instruções para produzir uma versão mais simples (2D, animações básicas) mantendo a intenção original. Ainda assim, trate os erros no cliente para orientar o usuário a revisar o prompt.

---

## 5. Endpoint: `POST /generate-video-file`
Semelhante ao `/generate-video`, porém retorna um stream `video/mp4`. Ideal para clientes que preferem baixar o arquivo já pronto.

### Exemplo (curl – salvando em disco)
```bash
curl -X POST https://ondokai.com/generate-video-file \
  -H "Content-Type: application/json" \
  -d '{
        "description": "Transform a red square into a blue circle",
        "width": 1080,
        "height": 1080
      }' \
  --output output.mp4
```

### Respostas
- **200 OK**: corpo binário MP4 + `Content-Disposition: attachment; filename="GeneratedScene.mp4"`.
- **400**: erro de validação de entrada.
- **500**: render falhou (logs no corpo JSON).

### Considerações
- Use clientes/bibliotecas que suportem downloads grandes.
- Esse endpoint bloqueia a conexão até o render terminar; mantenha timeout ≥ 120s.

---

## 6. Modelos e limites
| Item | Valor |
|------|-------|
| Modelo LLM | `gpt-5.1-codex-max` |
| FPS padrão | 60 |
| Timeout de render | 120 s (config atual) |
| Resolução padrão | 1920 x 1080 |
| Resolução mínima/máxima | 320 x 320 / 3840 x 3840 |
| Concurrency segura | 6–8 requisições simultâneas |

### Impacto da concorrência
- A API executa o Manim em threads paralelas; latência aumenta quando todos os 8 núcleos estão ocupados. 
- **Qualidade do vídeo não muda** com múltiplas execuções, apenas o tempo total cresce.

---

## 7. Erros comuns
| Código | Situação | Como resolver |
|--------|----------|----------------|
| `422 Unprocessable Entity` | JSON inválido ou campos fora do range | Verifique `description`, `width`, `height`. |
| `500 Render failed` | Erro do Manim (sintaxe, LaTeX, timeout) | Leia `render_logs`, ajuste descrição ou reduza resolução. |

### Mensagens de validação detalhadas (`Code generation failed`)
Quando o LLM retorna código incompleto, o backend responde `success: false` com dicas explícitas sobre como ajustar o prompt. Exemplos:
- `Missing 'from manim import' statement...` → deixe claro na descrição que o código deve começar com `from manim import *` (ou imports equivalentes) antes da classe.
- `Missing Scene class definition...` → peça explicitamente uma classe como `class MinhaCena(Scene):` contendo o método `construct` com as animações desejadas.
- `Missing construct method...` → mencione que a classe precisa implementar `def construct(self):` descrevendo cada etapa da animação.

Se qualquer uma dessas mensagens aparecer, basta reforçar essas instruções na descrição original e reenviar a requisição.
| `524 Cloudflare Timeout` | Render > ~100s sem resposta | Reenvie com descrição mais simples ou menor resolução; considere fila própria. |
| `502/503` | Túnel indisponível | Aguarde e repita; cheque [status](https://ondokai.com/). |

---

## 8. Ferramentas de teste
- **Postman**: importe `manim-api/postman_collection.json`. Há uma pasta "Ondokai.com" com todos os endpoints já configurados para o domínio público.
- **cURL**: scripts acima.
- **SDKs**: qualquer cliente HTTP padrão (Python `httpx`, JS `fetch`, etc.).

### Checklist antes de integrar
1. Verificar acesso HTTPS externo (sem VPN).
2. Ajustar timeout > 120s.
3. Implementar retentativas exponenciais em caso de 50x/524.
4. Converter o `video_base64` em arquivo local quando usar `/generate-video`.
5. Validar que o payload JSON está minificando `"` corretamente (evite escapar manualmente strings em shell).

---

## 9. Roadmap / contato
- Planejamos expor métricas (tempo médio, tokens) e endpoints adicionais (ex.: status de fila) em versões futuras.
- Problemas com o domínio/túnel: abra issue no repositório interno ou contate o time de infraestrutura.

Bom uso! Sinta-se à vontade para sugerir melhorias ou abrir PRs com novas automações de consumo. 🚀
