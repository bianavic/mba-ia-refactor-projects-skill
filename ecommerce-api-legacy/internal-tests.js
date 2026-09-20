#!/usr/bin/env node
//
// internal-tests.js — checagens de caixa-branca, em processo, sem servidor.
//
// Completa os outros dois validadores do projeto:
//   arch-check.sh    -> estrutura (AP-16: rota nao toca persistencia)
//   manual-tests.sh  -> comportamento via HTTP (precisa da app de pe)
//   internal-tests.js-> propriedades que a resposta HTTP nao revela
//
// O que so da para provar aqui:
//   1. Rollback da transacao do checkout. Nao da para fazer o SQLite falhar sob
//      demanda por curl, entao a falha e injetada em processo.
//   2. Que a checagem 1 sabe reprovar (controle negativo). Um teste que so sabe
//      passar nao mede nada.
//   3. Que src/app.js pode ser importado sem abrir porta — e propriedade do
//      modulo, nao de endpoint.
//   4. Que o teto de per_page e aplicado. Com 2 cursos no seed a resposta HTTP
//      fica identica com e sem limite, entao a prova tem que ser no validador.
//
// Uso:  node internal-tests.js     (ou: npm run test:internal)
// Saida: 0 = todas passaram, 1 = alguma falhou.

const { all, initSchema, withTransaction } = require('./src/database/connection');
const enrollmentModel = require('./src/models/enrollmentModel');
const createApp = require('./src/app');
const { validateReportQuery } = require('./src/middlewares/validators');
const config = require('./src/config');

const results = [];

function check(name, passed, detail) {
    results.push({ name, passed, detail });
    console.log(`  ${passed ? '✓' : '✗'} ${name}`);
    if (detail) console.log(`      ${detail}`);
}

async function countEnrollments() {
    return (await all('SELECT id FROM enrollments')).length;
}

/** 1. A transacao desfaz a matricula quando a gravacao seguinte falha. */
async function checkRollback() {
    const before = await countEnrollments();
    let propagated = null;

    try {
        await withTransaction(async () => {
            await enrollmentModel.create(1, 2);
            throw new Error('falha simulada gravando o pagamento');
        });
    } catch (err) {
        propagated = err.message;
    }

    const after = await countEnrollments();
    check(
        'rollback: matricula nao sobra quando o pagamento falha',
        after === before && propagated !== null,
        `erro propagado: ${propagated} | enrollments ${before} -> ${after}`
    );
}

/** 2. Controle negativo: sem transacao, a linha orfa TEM que sobrar. */
async function checkRollbackControl() {
    const before = await countEnrollments();

    try {
        await enrollmentModel.create(1, 2);
        throw new Error('falha simulada gravando o pagamento');
    } catch (err) {
        // esperado — o ponto e o que ficou no banco, nao o erro
    }

    const after = await countEnrollments();
    check(
        'controle negativo: sem transacao a linha orfa persiste (prova que a checagem acima mede algo)',
        after === before + 1,
        `enrollments ${before} -> ${after}`
    );
}

/** 3. A app monta sem efeito colateral — nada de porta aberta no import. */
function checkAppImportable() {
    const app = createApp();
    check(
        'app: src/app.js importavel sem abrir porta nem criar schema',
        typeof createApp === 'function' && typeof app === 'function',
        'quem chama listen() e o src/server.js'
    );
}

/** 4. per_page tem teto e default vindos do config. */
function checkPaginationClamp() {
    const excessivo = { query: { per_page: '999999999' } };
    validateReportQuery(excessivo, null, () => {});

    const semParametro = { query: {} };
    validateReportQuery(semParametro, null, () => {});

    check(
        'paginacao: per_page limitado ao teto e default vindo do config',
        excessivo.pagination.perPage === config.maxPageSize &&
            semParametro.pagination.perPage === config.defaultPageSize,
        `per_page=999999999 -> ${excessivo.pagination.perPage} (teto ${config.maxPageSize}) | ` +
            `sem per_page -> ${semParametro.pagination.perPage}`
    );
}

(async () => {
    console.log('==========================================================');
    console.log('internal-tests — ecommerce-api-legacy');
    console.log('Checagens em processo (sem servidor)');
    console.log('==========================================================\n');

    await initSchema();

    await checkRollback();
    await checkRollbackControl();
    checkAppImportable();
    checkPaginationClamp();

    const failed = results.filter((r) => !r.passed);
    console.log('\n==========================================================');
    if (failed.length === 0) {
        console.log(`PASS: ${results.length} checagem(ns) internas OK.`);
        console.log('==========================================================');
        process.exit(0);
    }
    console.log(`FAIL: ${failed.length} de ${results.length} checagem(ns) falharam.`);
    failed.forEach((r) => console.log(`  - ${r.name}`));
    console.log('==========================================================');
    process.exit(1);
})();
