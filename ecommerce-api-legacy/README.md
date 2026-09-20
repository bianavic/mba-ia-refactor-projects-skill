# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Validação

Três checagens, complementares — nenhuma substitui a outra:

```bash
./arch-check.sh            # estrutura: nenhuma rota toca persistência (AP-16)
npm run test:internal      # caixa-branca, em processo, sem servidor
npm test                   # endpoints via curl (precisa da app de pé)
```

`internal-tests.js` cobre o que a resposta HTTP não revela: o rollback da transação
do checkout (com controle negativo, para provar que a checagem sabe reprovar), a app
ser importável sem abrir porta, e o teto de `per_page`.

Se a porta 3000 estiver ocupada, use `PORT=3100 npm start` e
`BASE=http://localhost:3100 npm test`.
