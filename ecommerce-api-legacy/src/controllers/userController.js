const userModel = require('../models/userModel');

async function deleteUser(req, res) {
    const { id } = req.params;

    try {
        await userModel.deleteCascade(id);
    } catch (err) {
        return res.status(500).send('Erro ao deletar usuário');
    }

    res.send('Usuário e seus registros associados (matrículas e pagamentos) foram deletados.');
}

module.exports = { deleteUser };
