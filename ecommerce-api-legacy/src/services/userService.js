const userModel = require('../models/userModel');
const { AppError, failWith } = require('../errors/AppError');

/**
 * Remove usuário e dependências. Diferente da versão anterior, um id
 * inexistente não é mais reportado como remoção bem-sucedida.
 */
async function deleteUser(userId) {
    const { changes } = await userModel.deleteCascade(userId).catch(failWith(500, 'Erro ao deletar usuário'));

    if (changes === 0) throw new AppError(404, 'Usuário não encontrado');
}

module.exports = { deleteUser };
