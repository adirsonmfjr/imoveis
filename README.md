# 🏗️ Imovelweb Scraper — Manual de Uso

## 📁 Estrutura dos Arquivos

- `extract_data.py`: código principal do scraper.
- `cookies.json`: cookies salvos automaticamente ao colar o cabeçalho `Cookie`.
- `listings.json`: todos os anúncios coletados, **acumulados** (sem sobrescrever).
- `scraper_state.json`: salva a última página raspada, total de anúncios e data/hora.

---

## ▶️ Como Executar o Scraper

```bash
py extract_data.py --url "https://www.imovelweb.com.br/imoveis-venda-sao-bernardo-do-campo-sp-pagina-1.html"
```

---

## 💡 Funcionamento

1. A URL determina automaticamente a cidade (`sao-bernardo-do-campo`) e a operação (`venda` ou `aluguel`).
2. O scraper acessa a **API interna** do Imovelweb e coleta os anúncios.
3. Se for a primeira execução, começa na página 1. Caso contrário, retoma da **última página salva**.
4. Os anúncios são **acumulados** no `listings.json` (mesmo que sejam repetidos).
5. Após cada página:
   - Salva os anúncios da página no arquivo.
   - Atualiza `scraper_state.json`.

---

## 🍪 Sobre Cookies

Se ocorrer o erro `403 (acesso negado)`, será solicitado o cabeçalho `Cookie`.

### Como obter os cookies:
1. Acesse a **última página visitada** do site (ex: `https://www.imovelweb.com.br/imoveis-venda-sao-bernardo-do-campo-sp-pagina-20.html`).
2. Abra o DevTools (`F12`) → aba `Network` → clique em qualquer request do tipo `XHR`.
3. Va até o cabeçalho **Request Headers** → copie **TODO o campo `Cookie`**.
4. Cole no terminal quando solicitado.

---

## ⚙️ Parâmetros Opcionais

| Parâmetro      | Descrição |
|----------------|-----------|
| `--output`     | Nome do arquivo de saída (padrão: `listings.json`) |
| `--cookies`    | Caminho para arquivo `.json` com cookies, ou string direta |

---

## 📌 Exemplo com cookies via argumento:

```bash
py extract_data.py --url "URL" --cookies "cookie1=valor1; cookie2=valor2"
```

---

## ❗ Observações

- O scraper pausa 2 segundos entre cada página para evitar bloqueios.
- Os anúncios são salvos **completos ou incompletos**, para tratamento posterior.
- Se desejar **reiniciar o scraping**, basta excluir o arquivo `scraper_state.json`.

