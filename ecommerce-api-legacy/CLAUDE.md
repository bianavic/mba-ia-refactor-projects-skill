# ecommerce-api-legacy (Projeto 2)

Node.js 18+ / Express 4.18.2 com `sqlite3` e `dotenv`. **O nome da pasta engana:** o
domínio não é e-commerce, é um LMS de e-learning — usuários, cursos, matrículas,
pagamentos e log de auditoria.

## Rodar e validar

```bash
npm install
npm start              # ou: node src/app.js — http://localhost:3000
./manual-tests.sh      # endpoints via curl
./arch-check.sh        # AP-16: rotas não tocam persistência
```

`api.http` tem as mesmas chamadas para rodar direto da IDE. Não há suíte automatizada.

## Estrutura

`src/app.js` é o composition root; fluxo `src/routes/index.js` → `controllers/` →
`models/`, com `services/` para integrações (gateway de pagamento, cache) e
`middlewares/errorHandler.js` como tratamento central de erro.

- `routes/index.js` só mapeia caminho → método de controller. Nada de lógica ali.
- Só `models/` acessa `database/connection.js`. Controller não monta SQL.
- Configuração exclusivamente por `src/config/index.js` (lê `.env`); veja `.env.example`.

## Invariantes de segurança (achados CRITICAL já corrigidos — não regredir)

- **Nunca logar dado sensível**: número de cartão, senha ou chave de gateway. O bug
  original imprimia o cartão em texto plano no log do checkout.
- Log sempre via `src/utils/logger.js` (JSON estruturado, respeita `LOG_LEVEL`),
  nunca `console.log` direto.
- Credenciais só do ambiente. `.env` não é commitado; `.env.example` não leva valor real.
- Respostas de usuário não serializam senha/hash.

## Dependências

`npm audit` reporta 1 vulnerabilidade moderada em `qs` — **conhecida e documentada**
no README (seção 5.3). `npm audit fix` não resolve: exigiria migrar Express 4→5, um
major fora do escopo. Não bump o Express nem "conserte" isso sem o usuário pedir.
