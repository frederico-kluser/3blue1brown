# Cloudflare Tunnel: Expondo API Local com Domínio Próprio

> **Domínio configurado:** `ondokai.com`  
> **Sistema:** macOS  
> **Registrador:** GoDaddy  
> **Serviço local:** FastAPI em `localhost:8000`

Este guia documenta o processo completo para expor uma API local para a internet usando Cloudflare Tunnel com domínio próprio, incluindo HTTPS automático e URL persistente.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Instalação do cloudflared](#3-instalação-do-cloudflared)
4. [Adicionar Domínio ao Cloudflare](#4-adicionar-domínio-ao-cloudflare)
5. [Migrar Nameservers do GoDaddy](#5-migrar-nameservers-do-godaddy)
6. [Criar e Configurar o Tunnel](#6-criar-e-configurar-o-tunnel)
7. [Executar como Serviço 24/7](#7-executar-como-serviço-247)
8. [Comandos Úteis](#8-comandos-úteis)
9. [Troubleshooting](#9-troubleshooting)
10. [Múltiplos Serviços (Opcional)](#10-múltiplos-serviços-opcional)

---

## 1. Visão Geral

O Cloudflare Tunnel cria uma conexão segura entre seu computador local e a rede Cloudflare, eliminando a necessidade de:

- IP público fixo
- Port forwarding no roteador
- Configuração manual de SSL/TLS

```
[Internet] ←HTTPS→ [Cloudflare Edge] ←Tunnel→ [cloudflared] ←HTTP→ [localhost:8000]
```

**Benefícios:**
- HTTPS automático e gratuito
- Proteção DDoS incluída
- URL persistente (ex: `https://ondokai.com`)
- Funciona atrás de NAT/firewall

---

## 2. Pré-requisitos

- [ ] Conta gratuita na [Cloudflare](https://dash.cloudflare.com/sign-up)
- [ ] Domínio registrado (GoDaddy, Namecheap, etc.)
- [ ] macOS com Homebrew instalado
- [ ] API/serviço rodando localmente (ex: `localhost:8000`)

---

## 3. Instalação do cloudflared

### macOS (Homebrew)

```bash
# Instalar
brew install cloudflared

# Verificar instalação
cloudflared --version
# Saída esperada: cloudflared version 2025.x.x
```

O binário é instalado em:
- Apple Silicon: `/opt/homebrew/bin/cloudflared`
- Intel: `/usr/local/bin/cloudflared`

### Linux (Ubuntu/Debian)

```bash
# Adicionar repositório
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null

echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Instalar
sudo apt update && sudo apt install cloudflared
```

---

## 4. Adicionar Domínio ao Cloudflare

1. Acesse [dash.cloudflare.com](https://dash.cloudflare.com)
2. Clique em **"Add a Site"**
3. Digite seu domínio (ex: `ondokai.com`)
4. Selecione o plano **Free**
5. O Cloudflare importará seus registros DNS existentes
6. **Revise os registros** antes de continuar (especialmente MX para email)
7. Anote os **dois nameservers** atribuídos:
   ```
   Exemplo:
   anna.ns.cloudflare.com
   bob.ns.cloudflare.com
   ```

---

## 5. Migrar Nameservers do GoDaddy

### No painel GoDaddy:

1. Acesse [dcc.godaddy.com/control/portfolio](https://dcc.godaddy.com/control/portfolio)
2. Selecione seu domínio
3. Vá em **DNS** → **Nameservers**
4. Clique em **"I'll use my own nameservers"**
5. **Remova** os nameservers existentes do GoDaddy
6. **Adicione** os dois nameservers do Cloudflare (copiados no passo anterior)
7. Clique **Save**
8. Complete a verificação 2FA se solicitado

### Verificar propagação:

```bash
# Verificar se nameservers foram atualizados
dig ns ondokai.com @1.1.1.1

# Ou usar whois
whois ondokai.com | grep -i nameserver
```

**Tempo de propagação:** 
- Típico: 1-4 horas
- Máximo: até 48 horas

Quando concluído, o domínio mostrará status **"Active"** no dashboard Cloudflare.

---

## 6. Criar e Configurar o Tunnel

### 6.1 Autenticar no Cloudflare

```bash
cloudflared tunnel login
```

Isso abre o navegador para autenticação. Selecione o domínio desejado (ex: `ondokai.com`).

Após autorizar, um certificado é salvo em `~/.cloudflared/cert.pem`.

### 6.2 Criar o Tunnel

```bash
cloudflared tunnel create manim-api
```

**Saída esperada:**
```
Tunnel credentials written to /Users/seuuser/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json
Created tunnel manim-api with id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Anote o UUID** — você precisará dele para a configuração.

### 6.3 Criar arquivo de configuração

Crie o arquivo `~/.cloudflared/config.yml`:

```yaml
# ~/.cloudflared/config.yml

tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # Substitua pelo UUID do tunnel
credentials-file: /Users/seuuser/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  - hostname: ondokai.com
    service: http://localhost:8000
  
  # Catch-all obrigatório (sempre no final)
  - service: http_status:404
```

> **Importante:** Substitua `seuuser` pelo seu nome de usuário e o UUID pelo ID real do tunnel.

### 6.4 Criar rota DNS

```bash
cloudflared tunnel route dns manim-api ondokai.com
```

Isso cria automaticamente um registro CNAME no Cloudflare apontando para `<UUID>.cfargotunnel.com`.

### 6.5 Testar manualmente

```bash
# Terminal 1: Inicie sua API
cd manim-api && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Inicie o tunnel
cloudflared tunnel run manim-api
```

Acesse `https://ondokai.com` — deve responder com sua API.

---

## 7. Executar como Serviço 24/7

Para que o tunnel rode automaticamente após reiniciar o Mac:

### 7.1 Preparar configuração para o sistema

```bash
# Criar diretório de configuração do sistema
sudo mkdir -p /etc/cloudflared

# Copiar configuração e credenciais
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/
sudo cp ~/.cloudflared/*.json /etc/cloudflared/
```

### 7.2 Atualizar caminho das credenciais

Edite `/etc/cloudflared/config.yml` para usar o caminho do sistema:

```yaml
tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
credentials-file: /etc/cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  - hostname: ondokai.com
    service: http://localhost:8000
  - service: http_status:404
```

### 7.3 Instalar e iniciar o serviço

```bash
# Instalar como Launch Daemon
sudo cloudflared service install

# Iniciar imediatamente
sudo launchctl start com.cloudflare.cloudflared
```

O serviço é configurado em `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist` com:
- `RunAtLoad: true` — inicia no boot
- `KeepAlive: true` — reinicia automaticamente se crashar

### 7.4 Verificar funcionamento

```bash
# Checar se o serviço está rodando
sudo launchctl list com.cloudflare.cloudflared
# Se rodando, mostra o PID

# Testar endpoint
curl -I https://ondokai.com
```

---

## 8. Comandos Úteis

| Ação | Comando |
|------|---------|
| **Instalar** | `brew install cloudflared` |
| **Autenticar** | `cloudflared tunnel login` |
| **Criar tunnel** | `cloudflared tunnel create <nome>` |
| **Listar tunnels** | `cloudflared tunnel list` |
| **Info do tunnel** | `cloudflared tunnel info <nome>` |
| **Criar rota DNS** | `cloudflared tunnel route dns <nome> <hostname>` |
| **Rodar manualmente** | `cloudflared tunnel run <nome>` |
| **Validar config** | `cloudflared tunnel ingress validate` |
| **Testar regra** | `cloudflared tunnel ingress rule https://ondokai.com` |
| **Instalar serviço** | `sudo cloudflared service install` |
| **Desinstalar serviço** | `sudo cloudflared service uninstall` |
| **Status do serviço** | `sudo launchctl list com.cloudflare.cloudflared` |
| **Parar serviço** | `sudo launchctl stop com.cloudflare.cloudflared` |
| **Iniciar serviço** | `sudo launchctl start com.cloudflare.cloudflared` |
| **Ver logs** | `tail -f /Library/Logs/com.cloudflare.cloudflared.err.log` |
| **Deletar tunnel** | `cloudflared tunnel delete <nome>` |

---

## 9. Troubleshooting

### DNS não propaga após mudar nameservers

**Sintoma:** Domínio ainda mostra "Pending" no Cloudflare após várias horas.

**Soluções:**
- Verifique se DNSSEC está **desabilitado** no GoDaddy antes de migrar
- Confirme que **ambos** os nameservers foram adicionados
- Use `whois ondokai.com | grep -i nameserver` para verificar
- Aguarde até 48 horas

### Tunnel não conecta

**Verificações:**
```bash
# 1. API local está rodando?
curl http://localhost:8000

# 2. Validar configuração
cloudflared tunnel ingress validate

# 3. Testar qual regra corresponde
cloudflared tunnel ingress rule https://ondokai.com

# 4. Rodar em modo debug
cloudflared tunnel --loglevel debug run manim-api
```

### Serviço não inicia após reboot

```bash
# Verificar se plist existe
ls -la /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# Verificar se config existe
ls -la /etc/cloudflared/

# Ver erro específico
tail -50 /Library/Logs/com.cloudflare.cloudflared.err.log
```

**Problema comum:** O plist pode não incluir os argumentos corretos. Verifique:

```bash
sudo cat /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

`ProgramArguments` deve conter:
```xml
<array>
    <string>/opt/homebrew/bin/cloudflared</string>
    <string>tunnel</string>
    <string>run</string>
</array>
```

### ERR_TOO_MANY_REDIRECTS (se usar com Vercel)

Se você também usa Vercel no mesmo domínio:
- No Cloudflare, vá em **SSL/TLS → Overview**
- Mude para **Full** ou **Full (strict)**

---

## 10. Múltiplos Serviços (Opcional)

Para expor múltiplas APIs/serviços em subdomínios diferentes usando o mesmo tunnel:

### Configuração multi-serviço

```yaml
# ~/.cloudflared/config.yml

tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
credentials-file: /etc/cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  # API principal
  - hostname: ondokai.com
    service: http://localhost:8000
  
  # Documentação
  - hostname: docs.ondokai.com
    service: http://localhost:3000
  
  # Staging
  - hostname: staging.ondokai.com
    service: http://localhost:8001
  
  # Wildcard (qualquer outro subdomínio)
  - hostname: "*.ondokai.com"
    service: http://localhost:9000
  
  # Catch-all obrigatório
  - service: http_status:404
```

### Criar rotas DNS para cada hostname

```bash
cloudflared tunnel route dns manim-api ondokai.com
cloudflared tunnel route dns manim-api docs.ondokai.com
cloudflared tunnel route dns manim-api staging.ondokai.com
cloudflared tunnel route dns manim-api "*.ondokai.com"
```

### Reiniciar o serviço após mudanças

```bash
sudo launchctl stop com.cloudflare.cloudflared
sudo launchctl start com.cloudflare.cloudflared
```

---

## Verificação Final

Após completar a configuração:

```bash
# Health check da API
curl https://ondokai.com/

# Resposta esperada:
# {"status":"healthy","manim_version":"Manim Community v0.19.0","openai_model":"gpt-5.1-codex-max"}
```

✅ **Pronto!** Sua API está exposta publicamente em `https://ondokai.com` com HTTPS automático.

---

## Referências

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Cloudflare DNS Setup](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/)
- [GoDaddy Nameserver Guide](https://www.godaddy.com/help/edit-my-domain-nameservers-664)
- [Run as Service on macOS](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/local-management/as-a-service/macos/)
