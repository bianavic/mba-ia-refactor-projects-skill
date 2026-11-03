const userService = require('../services/userService');
const { ValidationError } = require('../errors/AppError');

function parseUserId(raw) {
    if (!/^\d+$/.test(raw)) throw new ValidationError();
    const id = Number(raw);
    if (id < 1 || !Number.isSafeInteger(id)) throw new ValidationError();
    return id;
}

async function deleteUser(req, res) {
    await userService.deleteUser(parseUserId(req.params.id));
    res.send('Usuário deletado');
}

async function exportUser(req, res) {
    res.json(await userService.exportUser(parseUserId(req.params.id)));
}

module.exports = { deleteUser, exportUser };
