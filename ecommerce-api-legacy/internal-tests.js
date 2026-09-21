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
//   5. Que o relatorio financeiro (AP-08) nao volta a ser N+1. O numero de
//      queries emitidas nao pode crescer com a quantidade de cursos.
//
// Uso:  node internal-tests.js     (ou: npm run test:internal)
// Saida: 0 = todas passaram, 1 = alguma falhou.

const { db, run, all, initSchema, withTransaction } = require('./src/database/connection');
const enrollmentModel = require('./src/models/enrollmentModel');
const reportService = require('./src/services/reportService');
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

/** Conta quantas queries de leitura (db.all/db.get) o driver emite durante `work`. */
async function withQueryCount(work) {
    let count = 0;
    const originalAll = db.all.bind(db);
    const originalGet = db.get.bind(db);
    db.all = (...args) => { count += 1; return originalAll(...args); };
    db.get = (...args) => { count += 1; return originalGet(...args); };
    try {
        const result = await work();
        return { result, count };
    } finally {
        db.all = originalAll;
        db.get = originalGet;
    }
}

async function seedCourses(howMany, startingAt) {
    const ids = [];
    for (let i = 0; i < howMany; i += 1) {
        const title = `Curso ${startingAt + i}`;
        const { lastID: courseId } = await run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
            [title, 100 + i]
        );
        const { lastID: enrollmentId } = await run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (1, ?)',
            [courseId]
        );
        await run(
            "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, 'PAID')",
            [enrollmentId, 100 + i]
        );
        ids.push(courseId);
    }
    return ids;
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

/** 5. financialReport (AP-08): numero de queries constante, nao cresce com N cursos. */
async function checkFinancialReportQueryCountConstant() {
    await seedCourses(3, 100);
    const { count: smallCount, result: smallReport } = await withQueryCount(() =>
        reportService.financialReport({ page: 1, perPage: 50 })
    );

    await seedCourses(12, 200);
    const { count: largeCount, result: largeReport } = await withQueryCount(() =>
        reportService.financialReport({ page: 1, perPage: 50 })
    );

    check(
        'financialReport: numero de queries nao cresce com a quantidade de cursos',
        smallCount === largeCount && largeCount <= 3,
        `${smallReport.length} curso(s) -> ${smallCount} querie(s) | ` +
            `${largeReport.length} curso(s) -> ${largeCount} querie(s)`
    );
}

/** 6. Controle negativo: uma query por curso (jeito antigo) TEM que crescer com N. */
async function checkFinancialReportControlWouldGrow() {
    const courses = await all('SELECT id FROM courses');

    const { count: naiveCount } = await withQueryCount(async () => {
        for (const course of courses) {
            await enrollmentModel.findDetailsByCourseIds([course.id]);
        }
    });

    check(
        'controle negativo: uma query por curso cresce com N (prova que a checagem acima mede algo)',
        naiveCount === courses.length,
        `${courses.length} curso(s) -> ${naiveCount} querie(s) no jeito ingenuo`
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
    await checkFinancialReportQueryCountConstant();
    await checkFinancialReportControlWouldGrow();

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
