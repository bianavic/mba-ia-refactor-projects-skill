# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Por padrão `GET /api/admin/financial-report` e `DELETE /api/users/:id` ficam desabilitados
(403) — para testar essa parte, suba o servidor com um token antes:

```bash
ADMIN_TOKEN=algum-token npm start
```

(ou defina `ADMIN_TOKEN=algum-token` em um `.env` — veja `.env.example` — já que o projeto
carrega variáveis de ambiente via `dotenv`) e envie o header `X-Admin-Token: algum-token`
nas chamadas a essas duas rotas.

Exemplos de requisições estão em `api.http` (boilerplate original) — mas atenção: os exemplos de `GET /api/admin/financial-report` e `DELETE /api/users/1` desse arquivo são anteriores à guarda de autenticação e **não mandam o header `X-Admin-Token`**, então hoje respondem 401 (ou 403, se `ADMIN_TOKEN` não estiver definido no servidor). O arquivo é mantido como registro do estado original. Para uma cobertura completa
e interativa (todos os endpoints, edge cases, e os casos de auth do `X-Admin-Token`), use
`api-tests.http` com a extensão "REST Client" do VS Code ou equivalente — ajuste a variável
`@adminToken` para o mesmo valor usado em `ADMIN_TOKEN` ao subir o servidor.

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
