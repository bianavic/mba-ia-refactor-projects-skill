const userService = require('../services/userService');

async function deleteUser(req, res) {
    await userService.deleteUser(req.userId);
    res.send('Usuário e seus registros associados (matrículas e pagamentos) foram deletados.');
}

module.exports = { deleteUser };
